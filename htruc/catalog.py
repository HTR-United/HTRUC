from typing import Optional, Dict, Any, List, Tuple
import os
import logging
import pandas

from htruc.repos import get_github_repo_yaml, get_htr_united_repos, get_a_yaml
from htruc.utils import parse_yaml


logger = logging.getLogger()

Catalog = Dict[str, Any]


def get_local_yaml(directory: str) -> Dict[str, Catalog]:
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
    return out


def get_all_catalogs(
    access_token: Optional[str] = None,
    local_directory: Optional[str] = None,
    get_distant: bool = True,
    main_organization: Optional[str] = "htr-united",
    check_link: bool = False,
    ignore_orgs_gits: List[str] = None
):
    """

    """
    data = {}
    if local_directory:
        data.update(get_local_yaml(directory=local_directory))
        if check_link:
            for uri in data:
                # We update the catalog if needs be by checking each repo
                if "github.com" in uri:
                    data[uri] = get_github_repo_yaml(address=uri, access_token=access_token)
    if get_distant:
        data.update(
            get_htr_united_repos(
                access_token=access_token,
                main_organization=main_organization,
                exclude=ignore_orgs_gits
            )
        )
    return data


def get_statistics(repositories: Dict[str, Catalog]) -> pandas.DataFrame:
    """

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
