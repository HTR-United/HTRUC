from typing import Union, TextIO, Dict, Any, List, Optional
import os.path
import yaml
import requests
import json


def parse_yaml(file: Union[str, TextIO]) -> Dict[str, Any]:
    """ Parse a yaml file

    >>> parse_yaml('tests/test_data/simple_yaml.yml')
    {'test': 'yes'}
    """
    if isinstance(file, str):
        if os.path.isfile(file) and os.path.exists(file):
            with open(file) as file:
                content = file.read()
        else:
            content = file
    else:
        content = file.read()
    return yaml.load(content, Loader=yaml.Loader)


def create_json_catalog(catalog: Dict[str, Dict], ids_files: Optional[str]) -> Dict[str, Dict]:
    ids = {}
    if os.path.exists(ids_files):
        with open(ids_files) as f:
            ids = json.load(f)
    for key in catalog:
        if key not in ids:
            ids[key] = f"repo-{str(len(ids)).zfill(5)}"

    with open(ids_files, "w") as f:
        json.dump(ids, f)

    return {
        ids[key]: catalog[key]
        for key in catalog
    }


def get_local_or_download(version, force_download: bool = False, is_uri: bool = False):
    if is_uri:
        version = version.split("/")[-2]
    basedir = os.path.dirname(__file__)
    local_path = os.path.join(basedir, "schemas", f"{version}.json")
    if not force_download and os.path.exists(local_path):
        return local_path
    else:
        req = requests.get(f"https://htr-united.github.io/schema/{version}/schema.json")
        req.raise_for_status()
        with open(local_path, "w") as f:
            f.write(req.text)
        return local_path
