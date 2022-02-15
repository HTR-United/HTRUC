import sys
import click
import requests
import os.path
import yaml
import json
import matplotlib
from typing import Optional, List

from htruc.validator import run
from htruc.catalog import get_all_catalogs, get_statistics, group_per_year, update_volume
from htruc.utils import parse_yaml, create_json_catalog


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


@cli.command("make")
@click.argument("directory", default="./catalog/")
@click.option("-m", "--main-organization", default="htr-united", show_default=True,
              help="Organization to retrieve repositories from")
@click.option("--remote/--no-remote", is_flag=True, default=True, show_default=True,
              help="Retrieve data from remote repositories in the organization's account")
@click.option("--check-link", is_flag=True, default=False, show_default=True,
              help="For each github repository documented in the local files, tries to download a `htr-united.yaml`"
                   " file from it.")
@click.option("--output", default="catalog.yaml", show_default=True,
              help="Dumps the agglutinated catalog as YAML")
@click.option("--json", default=None, show_default=True,
              help="Dumps the whole catalog as JSON too")
@click.option("--graph", default=None, show_default=True,
              help="Produce a graph at the path given (PNG Files please) with the amount of metrics"
                   "at different times")
@click.option("--graph-csv", default=None, show_default=True,
              help="Outputs the data behind the graph into a CSV file")
@click.option("--access_token", default=None, show_default=True,
              help="Github Access token")
@click.option("--statistics", default=None, show_default=True,
              help="Produce a recap CSV file with different statistics about the period covered by the dataset")
@click.option("--ignore-repo", default=["htr-united", "template-htr-united-datarepo"], multiple=True, show_default=True,
              help="Repos of the main organization that can be ignored")
@click.option("--ids", default="ids.json", type=click.Path(dir_okay=False), show_default=True,
              help="JSON file with IDs that maps each repository URLs")
def make(directory, main_organization: str, access_token: Optional[str] = None, remote: bool = True,
         check_link: bool = False, output: str = "catalog.yaml",
         json: Optional[str] = None,
         graph: Optional[str] = None,
         statistics: Optional[str] = None,
         graph_csv: Optional[str] = None,
         ignore_repo: List[str] = None,
         ids: click.File = None):
    """ Generate a catalog from a main repository and an organization

    """
    catalog = get_all_catalogs(
        access_token=access_token,
        main_organization=main_organization,
        local_directory=directory,
        get_distant=remote,
        check_link=check_link,
        ignore_orgs_gits=ignore_repo
    )
    click.echo(f"Dumping YAML output into {output}")
    with open(output, "w") as f:
        yaml.dump(list(catalog.values()), f, sort_keys=False)

    if json:
        click.echo(f"Dumping JSON output into {json}")
        from json import dump
        with open(json, "w") as f:
            dump(create_json_catalog(catalog, ids_files=ids), f)
    if graph or statistics or graph_csv:
        stats = get_statistics(catalog)
        if statistics:
            click.echo(f"Writing stats to {statistics}")
            stats.to_csv(statistics)
        if graph or graph_csv:
            data = group_per_year(stats)
            if graph_csv:
                click.echo(f"Plotting stats to {graph_csv}")
                data.to_csv(graph_csv)
            if graph:
                click.echo(f"Plotting {len(data.columns)-1} files with {graph} basename")
                basedir, basename = os.path.dirname(graph), os.path.basename(graph)
                basename = ".".join(basename.split(".")[:-1])
                import matplotlib.pyplot as plot

                num_axes = len(data.columns) - 1
                nrows = num_axes // 2 + int(bool(num_axes % 2))
                fig, axes = plot.subplots(
                    nrows=nrows,
                    ncols=2,
                    sharex=True,
                    squeeze=True,
                    figsize=(10, 5 * nrows),
                    dpi=300
                )
                cols = [col for col in data.columns if col != "year"]
                for metric, ax in zip(cols, [c for r in axes for c in r]):
                    data.plot.line(x="year", y=metric, ax=ax)
                fig.savefig(graph)
                click.echo(f"Saved {graph}")


@cli.command("update-volumes")
@click.argument("catalog-file", type=click.File(), nargs=1)
@click.argument("metrics-json", type=click.File(), nargs=1)
@click.option(
    "--version", type=str, default="2021-10-15", show_default=True,
    help="Date of the schema version"
)
@click.option(
    "--inplace", type=bool, is_flag=True, default=False, show_default=True,
    help="Saves the modified catalog inside the original file"
)
def catalog_volume_update(catalog_file, metrics_json, version, inplace):
    """ Update the metrics of a file """
    catalog = parse_yaml(catalog_file)
    new = json.load(metrics_json)
    updated, difference = update_volume(catalog.get("volume", []), new)
    catalog["volume"] = updated
    for metric in difference:
        if metric["count"] < 0:
            click.echo(click.style(f"> The category `{metric['metric']}` decreased by {abs(metric['count'])}",
                                   fg="yellow"))
        else:
            click.echo(click.style(f"> The category `{metric['metric']}` increased by {metric['count']}", fg="green"))

    # Close the original file
    catalog_file.close()
    filename = f"{catalog_file.name}"
    if not inplace:
        filename = filename.split(".")
        filename = ".".join([*filename[:-1], "auto-update", filename[-1]])
    click.echo(f"Writing the update volumes in {filename}")
    with open(filename, "w") as f:
        yaml.dump(catalog, f, sort_keys=False)


if __name__ == "__main__":
    cli()
