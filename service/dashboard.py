"""
Tableau de bord : lecture des tables Grist (en parallèle) et mémoire de 5 min.

Les règles de calcul, les tables et les colonnes utilisées sont dans
dashboard_calculs.py : c'est le fichier à modifier pour faire évoluer un indicateur.
"""

import logging
import os
import time
from concurrent.futures import ThreadPoolExecutor

from pony_express.service.grist import GristService
from pony_express.templates import contrat_pedagogique as kit

from service import dashboard_calculs as calc

logger = logging.getLogger(__name__)

# Document Grist de chaque démarche (le même par défaut)
DOCS = {
    "apprenants": kit.GRIST_DOC_ID,
    "groupes": os.environ.get("GRIST_DOC_ID_GROUPE") or kit.GRIST_DOC_ID,
    "personnel": os.environ.get("GRIST_DOC_ID_PERSONNEL") or kit.GRIST_DOC_ID,
}
SUFFIXES = ("champs", "annotations", "dossiers")

# Exposés pour le contrôle de santé
TABLE_FINANCIER = calc.TABLE_FINANCIER
DEMARCHES = {t: {"numero": d["numero"], "doc_id": DOCS[t]} for t, d in calc.DEMARCHES.items()}

CACHE_SECONDES = 300
_cache: dict = {"t": 0, "donnees": None}


def _table(type_mob: str, suffixe: str) -> str:
    return f"Demarche_{calc.DEMARCHES[type_mob]['numero']}_{suffixe}"


def _lire(doc_id: str, table: str) -> tuple[list[dict], dict]:
    """Lecture d'une table Grist, chronométrée (un client par lecture : appels en parallèle)."""
    debut = time.perf_counter()
    rows = GristService(doc_id, kit.GRIST_TEAM_SITE, kit.GRIST_SERVER).get_table_records(table)
    ms = round((time.perf_counter() - debut) * 1000)
    logger.warning("Dashboard : %s lue en %d ms (%d lignes)", table, ms, len(rows))
    return rows, {"table": table, "lignes": len(rows), "ms": ms}


def _lire_tables() -> tuple[dict, list]:
    """Financier Erasmus + 3 tables par démarche, lues en parallèle."""
    a_lire = [(kit.GRIST_DOC_ID, calc.TABLE_FINANCIER)] + [
        (DOCS[t], _table(t, s)) for t in calc.TYPES for s in SUFFIXES
    ]
    with ThreadPoolExecutor(max_workers=len(a_lire)) as pool:
        resultats = list(pool.map(lambda t: _lire(*t), a_lire))
    tables = {table: rows for (_, table), (rows, _) in zip(a_lire, resultats)}
    return tables, [chrono for _, chrono in resultats]


def _charger(rafraichir: bool = False) -> dict:
    if not rafraichir and _cache["donnees"] and time.time() - _cache["t"] < CACHE_SECONDES:
        return {**_cache["donnees"], "chargement": {**_cache["donnees"]["chargement"], "memoire": True}}
    debut = time.perf_counter()
    tables, chrono = _lire_tables()
    donnees = {
        "projets": calc.projets(tables[calc.TABLE_FINANCIER]),
        "mobilites": [
            m for t in calc.TYPES
            for m in calc.mobilites_demarche(t, *(tables[_table(t, s)] for s in SUFFIXES))
        ],
    }
    donnees["chargement"] = {"ms": round((time.perf_counter() - debut) * 1000), "tables": chrono, "memoire": False}
    logger.warning("Dashboard : lecture Grist totale %d ms", donnees["chargement"]["ms"])
    _cache.update(t=time.time(), donnees=donnees)
    return donnees


def donnees_dashboard(
    etablissement: str = "", code_projet: str = "", annee: str = "", type_mobilite: str = "",
    rafraichir: bool = False,
) -> dict:
    donnees = _charger(rafraichir)
    reponse = calc.indicateurs(donnees["projets"], donnees["mobilites"],
                               etablissement, code_projet, annee, type_mobilite)
    reponse["chargement"] = donnees["chargement"]
    return reponse
