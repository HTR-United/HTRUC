from typing import Dict, Any
import logging
import click


CatalogRecord = Dict[str, Any]
Logger = logging.getLogger(__name__)


def log(data, verbose: bool, use_log: bool = False):
    if not verbose:
        return
    if use_log:
        Logger.info(data)
    else:
        click.echo(click.style(data, fg="cyan", italic=True))


def upgrade_2021_10_15_to_2022_04_15(catalog_record: CatalogRecord, verbose=True, use_log=False) -> CatalogRecord:
    catalog_record["schema"] = "https://htr-united.github.io/schema/2022-04-15/schema.json"
    log("Upgrading from 2021-10-15 to 2022-04-15", verbose=verbose, use_log=use_log)

    for author in catalog_record.get("authors", []):
        author["type"] = "person"
        log(f"--> Automatically upgrade author {author['name']} with `type`=`person`", verbose=verbose, use_log=use_log)

    catalog_record["script"] = [
        {"iso": script}
        for script in catalog_record["script"]
    ]
    log(f"--> Automatically converted script to objects", verbose=verbose, use_log=use_log)

    catalog_record["production-software"] = "Unknown [Automatically filled]"
    log(f"--> Automatically upgraded with `production-software`=`Unknown`", verbose=verbose, use_log=use_log)

    return catalog_record
