from typing import Optional, Dict, Any, Tuple
import re
import yaml
from github import Github
from github.GithubException import UnknownObjectException
from htruc.utils import parse_yaml


Catalog = Dict[str, Any]


def get_github_repo_yaml(
        address: str,
        access_token: Optional[str] = None,
        raise_on_parse_error: bool = False) -> Optional[Catalog]:
    """
    >>> get_github_repo_yaml("github.com/htr-united/cremma-medieval.git")["title"]
    'Cremma Medieval'
    """

    user, repo_name = re.findall("github.com/([^/]+)/([^/]+)", address)[0]
    if repo_name.endswith(".git"):
        repo_name = repo_name[:-4]
    g = Github(access_token)
    repo = g.get_repo(f"{user}/{repo_name}")
    try:
        text = repo.get_contents("htr-united.yml").decoded_content.decode()
    except UnknownObjectException as e:
        return None
    try:
        return parse_yaml(text)
    except yaml.parser.ParserError:
        print(f"Parse error on {user}/{repo_name}")
        if raise_on_parse_error:
            raise
        return None


def get_htr_united_repos(
        access_token: Optional[str] = None,
        main_organization: str = "htr-united",
        exclude: Tuple[str, ...] = ("htr-united", "template-htr-united-datarepo", )
) -> Dict[str, Catalog]:
    """ Get a single repo specific tokens

    >>> get_htr_united_repos()
    """
    g = Github(access_token)
    o = g.get_organization(main_organization)
    out = {}
    for repo in o.get_repos(type="public"):
        if repo.name in exclude:
            continue
        data = get_github_repo_yaml(repo.clone_url, access_token=access_token)
        if data:
            out[repo.full_name] = data
    return out
