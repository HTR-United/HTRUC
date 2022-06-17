from typing import Dict, Tuple, Callable, AnyStr, Iterable
from htruc.schemas.upgrade_path import upgrade_2021_10_15_to_2022_04_15, CatalogRecord


def get_list():
    raise NotImplementedError()


SchemaVersion = AnyStr

# This Tuple is used to know which schema are supported
UpgradeOrder: Tuple[SchemaVersion, ...] = (
    "https://htr-united.github.io/schema/2021-10-15/schema.json",
    "https://htr-united.github.io/schema/2022-04-15/schema.json",
)

UpgradeFunction: Dict[str, Callable[[CatalogRecord], CatalogRecord]] = {
    UpgradeOrder[0]: upgrade_2021_10_15_to_2022_04_15
}


def recursive_update(catalog_record: CatalogRecord) -> Tuple[CatalogRecord, Iterable[SchemaVersion]]:
    """ Automatically upgrade a schema

    :returns: The catalog record upgrade to the latest schema, with the list of upgrade it went through

    """
    version = catalog_record["schema"]
    # If the version is the latest, no need to upgrade
    if version == UpgradeOrder[-1]:
        return catalog_record, []
    current_version_index = UpgradeOrder.index(version)

    for version in UpgradeOrder[current_version_index:-1]:
        catalog_record = UpgradeFunction[version](catalog_record)

    return catalog_record, UpgradeOrder[current_version_index:-1]
