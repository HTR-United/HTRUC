from typing import Iterable, List, TextIO, Dict, Any, Optional, Union
from dataclasses import dataclass
import json
import os

from jsonschema import validate, ValidationError, Draft7Validator
from yaml.parser import ParserError

from htruc.utils import parse_yaml, get_local_or_download


@dataclass
class Status:
    filename: str
    status: bool
    messages: List[str]


def _reformat_errors(msg):
    return str(msg).replace("\n", "\n    ").strip()


def _elipse(msg: str) -> str:
    if len(msg) > 122:
        return msg[:100]+"[...]"+msg[-17:]
    return msg


def run(files: Iterable[Union[TextIO, str]], schema_path: str):
    """ Run tests on a catalog

    >>> list(run(['tests/test_data/example.yaml'], "./htruc/schemas/2021-10-15.json"))
    [Status(filename='tests/test_data/example.yaml', status=False, messages=["Path `format`: 'ALTO' is not one of ['Alto-XML', 'Page-XML']", "'schema' is a required property"])]
    """
    validator: Optional[Draft7Validator] = None
    if schema_path != "auto":
        with open(schema_path) as f:
            schema = json.load(f)
        validator = Draft7Validator(schema)

    for file in files:
        # Parse the file
        filename = file if isinstance(file, str) else file.name
        try:
            parsed = parse_yaml(file)
        except ParserError as e:
            yield Status(filename, False, [f"Parse error: {_reformat_errors(e)}"])
            continue

        local_validator = validator
        if not validator:
            if parsed["schema"].startswith("https://htr-united.github.io/schema/"):
                local_validator = get_local_or_download(parsed["schema"], is_uri=True)
                with open(local_validator) as f:
                    schema = json.load(f)
                local_validator = Draft7Validator(schema)
            else:
                yield Status(filename, False, [f"Wrong schema URI ({parsed['schema']})"])
                continue

        if local_validator.is_valid(parsed):
            yield Status(filename, True, [])
            continue

        yield Status(filename, False, [
            f"Path `{'.'.join(map(str, error.path))}`: {_elipse(error.message)}" \
                if error.path else _elipse(error.message)
            for error in local_validator.iter_errors(parsed)
        ])
        #    yield
        #raise Exception
        #raise Exception

        # Validate the file
        #try:
        #    validate(parsed, schema=schema)
        #    yield Status(filename, True, [])
        #except ValidationError as validation_error:
        #    print(validation_error.errors)
        #     yield Status(filename, False, [])

