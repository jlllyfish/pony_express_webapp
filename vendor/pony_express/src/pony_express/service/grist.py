import logging
from collections.abc import Callable
from enum import EnumType

from pygrister.api import GristApi

logger = logging.getLogger(__name__)

JOIN_KEY = "dossier_number"  # clé commune aux tables OTP (dossiers, champs, annotations, blocs)


def not_in_grist(fieldname) -> str:
    return fieldname + " is not in GRIST"


def normalize_key(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return value


def make_lookup(fetch: Callable[[str], list[dict]], join_key: str = JOIN_KEY):
    """lookup(table, record) -> ligne de `table` ayant le même numéro de dossier (table lue une seule fois)."""
    cache: dict[str, dict] = {}

    def lookup(table: str, record: dict) -> dict | None:
        if table not in cache:
            cache[table] = {normalize_key(r.get(join_key)): r for r in fetch(table)}
        return cache[table].get(normalize_key(record.get(join_key)))
    return lookup


def map_record(record: dict, config_enum: EnumType, lookup) -> dict:
    """
    Valeur de l'Enum = ID de colonne de la table principale,
    ou "Table.colonne" pour une colonne d'une autre table reliée par numéro de dossier.
    """
    record_data = {'id': record["id"]}
    for enum_item in config_enum:
        if "." in enum_item.value:
            table, column = enum_item.value.split(".", 1)
            source = lookup(table, record)
        else:
            column, source = enum_item.value, record
        if source is not None and column in source:
            record_data[enum_item.name] = source[column]
        else:
            record_data[enum_item.name] = not_in_grist(enum_item.name)
    return record_data


class GristService():
    def __init__(self, doc_id, doc_team_site, doc_self_hosted_server=None):

        config = {
            'GRIST_DOC_ID': doc_id,
            'GRIST_TEAM_SITE': doc_team_site
        }
        if doc_self_hosted_server:
            config['GRIST_SELF_MANAGED'] = "Y"
            config['GRIST_SELF_MANAGED_HOME'] = doc_self_hosted_server

        self.grist = GristApi(config=config)

    def get_grist_data(self, table, config_enum: EnumType, should_be_exported: Callable[[dict], bool],
                       join_key: str = JOIN_KEY) -> list[dict]:
        raw_data = self.get_table_records(table)
        lookup = make_lookup(self.get_table_records, join_key)
        return [map_record(record, config_enum, lookup) for record in raw_data if should_be_exported(record)]

    def get_table_records(self, table) -> list[dict]:
        """Toutes les lignes d'une table (ex : table de blocs répétables)."""
        status, records = self.grist.list_records(table)
        if status != 200:
            raise RuntimeError(f"Lecture de la table Grist '{table}' impossible : HTTP {status}")
        return records

    def update_grist_data(self, table, data):
        status, response = self.grist.update_records(table, data)
        if status != 200 :
            logger.error(f"Failed to update data: HTTP {status}")

    def upload_attachments(
        self,
        filepath: str,
    ) -> str:
        status, attachment_ids = self.grist.upload_attachments([filepath])

        #return "mock_upload_id"

        if status != 200 or not attachment_ids:
            logger.error(f"Failed to upload attachment: HTTP {status}")
            print("error")

        attachment_id = attachment_ids[0]  # Récupérer le premier ID
        logger.info(
            f"Successfully uploaded file, attachment ID: {attachment_id}"
        )
        print(f"Successfully uploaded file, attachment ID: {attachment_id}"
)

        return attachment_id
