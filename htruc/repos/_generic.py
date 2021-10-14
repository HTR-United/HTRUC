from typing import Optional, Dict, Any
import requests
from htruc.utils import parse_yaml


Catalog = Dict[str, Any]


def get_a_yaml(address: str, raise_on_parse_error: bool = False) -> Optional[Catalog]:
    req = requests.get(address)
    if req.status_code >= 400:
        return None

    yaml = req.text
    try:
        return parse_yaml(yaml)
    except Exception as E:
        print(f"Parse error on {address}")
        if raise_on_parse_error:
            raise
        return None
