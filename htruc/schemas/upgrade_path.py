import logging
import click
from htruc.types import CatalogRecord


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

    catalog_record["script"] = [
        {"iso": script}
        for script in catalog_record["script"]
    ]
    log(f"--> Automatically converted script to objects", verbose=verbose, use_log=use_log)

    catalog_record["production-software"] = "Unknown [Automatically filled]"
    log(f"--> Automatically upgraded with `production-software`=`Unknown`", verbose=verbose, use_log=use_log)

    return catalog_record


def upgrade_2022_04_15_to_2023_06_27(catalog_record: CatalogRecord, verbose=True, use_log=False) -> CatalogRecord:
    catalog_record["schema"] = "https://htr-united.github.io/schema/2023-06-27/schema.json"
    log("Upgrading from 2022-04-15 to 2023-06-27", verbose=verbose, use_log=use_log)

    catalog_record["automatically-aligned"] = False
    log(f"--> Automatically set to False automatically-aligned flag", verbose=verbose, use_log=use_log)

    return catalog_record
