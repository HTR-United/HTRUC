from typing import Optional, Dict, Any, List, Tuple, Iterable, Union
import os
import logging
import pandas
import cffconvert
import requests

from htruc.repos import get_github_repo_yaml, get_htr_united_repos, get_github_repo_cff
from htruc.utils import parse_yaml
from htruc import validator
from htruc.schemas import recursive_update
from htruc.types import CatalogRecord, Catalog
logger = logging.getLogger()


def _clean_a_dict(catalog: Catalog) -> Catalog:
    invalid: List[str] = []

    for schema in catalog:
        for status in validator.run([catalog[schema]], schema_path="auto"):
            if not status.status:  # If the schema is invalid
                invalid.append(schema)
                logging.warning(f"Invalid schema file for {schema}")

    for key in invalid:
        del catalog[key]

    return catalog


def _upgrade_a_dict(catalog: Catalog) -> Catalog:
    for schema in catalog:
        new_version, nb_upgrade = recursive_update(catalog[schema])
        if nb_upgrade:
            catalog[schema] = new_version

    return catalog


def get_local_yaml(directory: str, keep_valid_only: bool = True) -> Catalog:
    """ Reads all local YAML file in a given directory and parses them as Catalog Record.

    :param directory: Directory to scan
    :param keep_valid_only: Only keeps passing HTR-United files

    """
    out = {}
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(".yml") or file.endswith(".yaml"):
                try:
                    data = parse_yaml(os.path.join(root, file))
                    out[data.get("url")] = data
                except Exception as E:
                    logging.warning(f"Impossible to parse and understand {file}")
                    logger.info(str(E))
    if keep_valid_only:
        _clean_a_dict(out)
    return out


def get_all_catalogs(
    access_token: Optional[str] = None,
    local_directory: Optional[str] = None,
    get_distant: bool = True,
    organizations: Optional[Union[str, Iterable[str]]] = "htr-united",
    check_link: bool = False,
    ignore_orgs_gits: List[str] = None,
    keep_valid_only: bool = True,
    auto_upgrade: bool = False,
    citation_cff: bool = False
) -> Catalog:
    """ Retrieve repositories from various location (online, locally) and create a catalog out of the records.

    :param access_token: Github Access Token to retrieve information ~ without limit from Github.com
    :param local_directory: Local directory to scan for files
    :param get_distant: Retrieves data from organisations on Github (Scan all their repositories)
    :param organizations: Organizations to scan
    :param check_link: If a local directory catalog record links to a github repository, scan the remote repository
        for any updates on the catalog
    :param ignore_orgs_gits: Ignore specific repositories in the scan
    :param keep_valid_only: Only Keeps valid catalog record
    :param auto_upgrade: Upgrade automatically all schemas to the latest version (Only applied if keep_valid_only is
        True)
    """
    data = {}
    if local_directory:
        data.update(get_local_yaml(directory=local_directory, keep_valid_only=False))
        if check_link:
            for uri in data:
                # We update the catalog if needs be by checking each repo
                if "github.com" in uri:
                    data[uri] = get_github_repo_yaml(address=uri, access_token=access_token)
    if get_distant:
        if isinstance(organizations, str):
            organizations = (organizations, )
        for orga in organizations:
            data.update(
                get_htr_united_repos(
                    access_token=access_token,
                    main_organization=orga,
                    exclude=ignore_orgs_gits
                )
            )
    if keep_valid_only:
        _clean_a_dict(data)
    if auto_upgrade and keep_valid_only:
        _upgrade_a_dict(data)
    if citation_cff:
        for key in data:
            data[key].update(_get_bibtex_and_apa(data[key], access_token=access_token))
    return data


def get_statistics(repositories: Catalog) -> pandas.DataFrame:
    """ Retrieve statistics from a diction of repositories

    :param repositories: Dictionary of Repositories records

    >>> #x = get_all_catalogs(local_directory="/home/thibault/dev/htr-united", check_link=False, get_distant=False)
    >>> #get_statistics(x).groupby(by="metric").sum()
    """
    df = [

    ]
    for repository, entry in repositories.items():
        try:
            begin, end = entry["time"]["notBefore"], entry["time"]["notAfter"]
            for a_volume in entry.get("volume", []):
                df.append({
                    "uri": repository,
                    "title": entry["title"],
                    "start": int(begin),
                    "end": int(end),
                    "metric": a_volume["metric"].lower(),
                    "count": int(a_volume["count"]),
                    "format": entry["format"],
                    "script-type": entry["script-type"]
                })
        except KeyError:
            logger.warning(f"Unable to parse {repository} for statistics")
        except TypeError:
            logger.warning(f"Unable to parse {repository} for statistics")
    return pandas.DataFrame(df)


def group_per_year(df: pandas.DataFrame, column: Optional[str] = "metric", period: int = 50):
    """ Group a column per year

    >>> group_per_year(pandas.DataFrame([
    ... {"start": 1300, "end": 1399, "metric": "line", "count": 134},
    ... {"start": 1300, "end": 1399, "metric": "characters", "count": 234},
    ... {"start": 1350, "end": 1449, "metric": "line", "count": 34},
    ... {"start": 1500, "end": 1551, "metric": "line", "count": 37},
    ... {"start": 1503, "end": 1504, "metric": "line", "count": 37},
    ... {"start": 1300, "end": 1499, "metric": "line", "count": 2}]))
       year  characters  line
    0  1300         234   136
    1  1350         234   170
    2  1400           0    36
    3  1450           0     2
    4  1500           0    74
    5  1550           0    37

    """
    new_df = [
        {
            "year": range_start,
            **df[
                df.start.between(range_start, range_start+period-1) | \
                df.end.between(range_start, range_start+period-1) | \
                ((df.start < range_start) & (range_start+period-1 < df.end))
            ].groupby(column)["count"].sum()
        }
        for range_start in range(
            df.start.min() // period * period,
            period * (df.end.max() // period) + int(bool(df.end.max() % period)),
            period
        )
    ]
    return pandas.DataFrame(new_df).fillna(0).astype(int)


MetricLists = List[Dict[str, int]]


def update_volume(original_volume: MetricLists, metrics: MetricLists) -> Tuple[MetricLists, MetricLists]:
    """ Compute the new metrics for a catalog, returns a difference list as a second output

    >>> old = [{"metric": "pages", "count": 5}, {"metric": "documents", "count": 5}]
    >>> new = [{"metric": "pages", "count": 10}, {"metric": "line", "count": 105}]
    >>> out = update_volume(old, new)
    >>> out == (
    ...    [{"metric": "documents", "count": 5}, {"metric": "line", "count": 105}, {"metric": "pages", "count": 10}],
    ...    [{"metric": "pages", "count": 5}],
    ... )
    True

    """
    old = {vol["metric"]: vol["count"] for vol in original_volume}
    new = {vol["metric"]: vol["count"] for vol in metrics}
    all_keys = sorted(list(set(old.keys()).union(set(new.keys()))))
    diff = {key: new.get(key) - old.get(key) for key in all_keys if key in old and key in new}
    return (
        [{"metric": key, "count": new.get(key, old.get(key))} for key in all_keys],
        [{"metric": key, "count": diff.get(key)} for key in diff]
    )


def _get_bibtex_and_apa(catalog_record: CatalogRecord, access_token: Optional[str]=None) -> Dict[str, str]:
    """

    """
    if "citation-file-link" not in catalog_record and "github.com" not in catalog_record["url"]:
        return {}
    elif "citation-file-link" not in catalog_record:
        citation_file_content = get_github_repo_cff(catalog_record["url"], access_token=access_token)
        if not citation_file_content:
            return {}
    else:  # We got a URI
        try:
            req = requests.get(catalog_record["citation-file-link"])
            req.raise_for_status()
            citation_file_content = req.text
            if "</html>" in citation_file_content.lower():
                raise Exception("CFF File link is wrong, it returns HTML.")
        except Exception as E:
            logger.error(f"Error retrieving CITATION File for {catalog_record['citation-file-link']}: {str(E)}")
            if "github.com" in catalog_record["url"]:
                logger.error(f"Trying to reach github directly")
                return _get_bibtex_and_apa({"url": catalog_record["url"]}, access_token=access_token)
            return {}

    try:
        citation = cffconvert.Citation(citation_file_content)
    except Exception as E:
        logger.error(f"Unable to parse CFF for {catalog_record['url']} ({E})")
        return {}
    return_obj = {}
    try:
        return_obj["_bibtex"] = citation.as_bibtex()
    except Exception as E:
        logger.error(f"Unable to parse as Bibtex {catalog_record['url']} ({E})")

    try:
        return_obj["_apa"] = citation.as_apalike()
    except Exception as E:
        logger.error(f"Unable to parse as APA {catalog_record['url']} ({E})")

    return return_obj
