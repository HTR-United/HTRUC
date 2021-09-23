from typing import Union, TextIO, Dict, Any
import yaml


def parse_yaml(file: Union[str, TextIO]) -> Dict[str, Any]:
    """ Parse a yaml file

    >>> parse_yaml('tests/simple_yaml.yml')
    {'test': 'yes'}
    """
    if isinstance(file, str):
        with open(file) as file:
            content = file.read()
    else:
        content = file.read()
    return yaml.load(content, Loader=yaml.Loader)
