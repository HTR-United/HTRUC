from typing import Iterable, List
import click
from dataclasses import dataclass
import yaml
import json
from jsonschema import validate



@dataclass
class Status:
    filename: str
    status: bool
    messages: List[str]


def _error(message):
    click.echo(
        click.style(message, fg="red"),
        color=True
    )


def _reformat_errors(msg):
    return str(msg).replace("\n", "\n    ").strip()


def run(files: Iterable[click.File]):
    with open("schema.json") as f:
        schema = json.load(f)

    for file in files:
        parsed = None
        try:
            parsed = yaml.load(file.read(), Loader=yaml.Loader)
        except yaml.parser.ParserError as e:
            yield Status(file.name, False, [f"Parse error: {_reformat_errors(e)}"])
        if parsed:
            validate(
                parsed,
                schema=schema
            )


@click.command("test")
@click.argument("files", type=click.File(), nargs=-1)
def command(files):
    for status in run(files):
        if status.status is False:
            _error(f"☒ File `{status.filename}` testing failed")
            for message in status.messages:
                _error(f"  {message}")


if __name__ == "__main__":
    command()