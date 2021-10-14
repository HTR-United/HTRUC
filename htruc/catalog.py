from typing import Optional, Dict, Any
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
    check_link: bool = False
):
    """

    >>> get_statistics(local_directory="./")
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
        data.update(get_htr_united_repos(access_token=access_token, main_organization=main_organization))
    return data


def get_statistics(repositories: Dict[str, Catalog]) -> pandas.DataFrame:
    """

    >>> x = get_all_catalogs(local_directory="/home/thibault/dev/htr-united", check_link=False, get_distant=False)
    >>> get_statistics(x).groupby(by="metric").sum()
    """
    df = [

    ]
    for repository, entry in repositories.items():
        try:
            begin, end = entry["time"].split("--")
            for a_volume in entry.get("volume", []):
                df.append({
                    "uri": repository,
                    "title": entry["title"],
                    "start": int(begin),
                    "end": int(end),
                    "metric": a_volume["metric"].lower(),
                    "count": int(a_volume["count"])
                })
        except KeyError:
            logger.warning(f"Unable to parse {repository} for statistics")
    return pandas.DataFrame(df)


def group_per_year(df: pandas.DataFrame, column: Optional[str] = "metric", period: int = 50):
    """ Group a column per year

    """
    new = []
    all_values = df[column].unique().tolist()
    for start in range(df.start.min(), df.end.max()+1, period):
        for x in df[(df.start >= start) & (df.start <= start + period-1)].groupby(
            "metric"
        )[("count", "metric", "start")].sum("count"):
            print(x)
    return new
