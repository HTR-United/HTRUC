import sys
import click
import requests
import os.path

from htruc.validator import run


def _error(message):
    click.echo(
        click.style(message, fg="red"),
        color=True
    )


def _get_local_or_download(version, force_download: bool = False):
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


@click.group()
def cli():
    """ Interface for HTRUC """


@cli.command("test")
@click.argument("files", type=click.File(), nargs=-1)
@click.option(
    "--version", type=str, default="2021-10-15", show_default=True,
    help="Date of the schema version"
)
@click.option("--force-download", is_flag=True, help="Download the schema using the version provided")
def test(files, version: str, force_download: bool):
    """ Test catalog files """
    click.echo(f"{len(files)} to be tested")
    statuses = []
    schema_path = _get_local_or_download(version, force_download=force_download)
    for status in run(files, schema_path=schema_path):
        statuses.append(status.status)
        if status.status is False:
            _error(f"☒ File `{status.filename}` testing failed")
            for message in status.messages:
                _error(f"  {message}")
    click.echo()
    click.echo(
        click.style(
            f"{statuses.count(True)/len(statuses)*100:.2f}% of schema passed ({statuses.count(True)}/{len(statuses)})",
            fg="red" if False in statuses else "green"
        )
    )
    sys.exit(-1 if False in statuses else 0)


if __name__ == "__main__":
    cli()
