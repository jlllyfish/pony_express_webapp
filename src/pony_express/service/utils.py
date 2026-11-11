import pathlib
from collections import defaultdict
from datetime import datetime, timedelta, timezone


def get_date_from_timestamp(str_timestamp: str) -> str:
    """Accepte un timestamp Grist, ["d", timestamp] ou une date ISO ("2026-03-01..."). ValueError sinon."""
    if isinstance(str_timestamp, list):
        str_timestamp = _parse_grist_date_data(str_timestamp)
    if isinstance(str_timestamp, str) and not str_timestamp.lstrip("-").isdigit():
        date = datetime.fromisoformat(str_timestamp.strip()[:10])
        return date.strftime("%d-%m-%y")
    timestamp = int(str_timestamp)
    # dates Grist = minuit UTC ; fromtimestamp() plante sous Windows avant 1970
    date = datetime(1970, 1, 1, tzinfo=timezone.utc) + timedelta(seconds=timestamp)
    return date.strftime("%d-%m-%y")

def _parse_grist_date_data(grist_date: list[str]) -> str:
    return grist_date[1]

def concat_values(data: dict, labels: list) -> list:
    data_list = []
    for label in labels:
        if data[label]:
            data_list.append(data[label])
    return data_list

def group_blocks(records: list[dict], key: str, order: str) -> dict[int, list[dict]]:
    """Regroupe les lignes d'une table de blocs répétables par numéro de dossier, triées par index."""
    groups = defaultdict(list)
    for record in sorted(records, key=lambda r: int(r.get(order) or 0)):
        if record.get(key) not in (None, ""):
            groups[int(record[key])].append(record)
    return groups

def clean_text(value) -> str:
    return str(value).replace("\r\n", "\n").strip() if value else ""

TEMPLATES_FOLDER_PATH = str(pathlib.Path(__file__).parent.parent.parent.parent.resolve()) + "/templates/"
