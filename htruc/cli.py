import sys
import click

from htruc.validator import run


def _error(message):
    click.echo(
        click.style(message, fg="red"),
        color=True
    )


@click.group()
def cli():
    """ Interface for HTRUC """


@cli.command("test")
@click.argument("files", type=click.File(), nargs=-1)
def command(files):
    """ Test catalog files """
    statuses = []
    for status in run(files):
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
