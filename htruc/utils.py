from typing import Union, TextIO, Dict, Any
import os.path
import yaml


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
