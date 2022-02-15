from typing import Union, TextIO, Dict, Any, List, Optional
import os.path
import yaml
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
