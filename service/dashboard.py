"""
Tableau de bord : lecture Grist (en parallèle) et mémoire de 5 min.

Lecture par requête SQL Grist : une requête par démarche, limitée aux colonnes
utiles (dashboard_calculs.colonnes_lues) avec la jointure champs / annotations /
dossiers faite par Grist. En cas d'échec (colonne absente, SQL indisponible),
repli sur la lecture complète des tables.

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


def _sql_demarche(type_mob: str) -> str:
    """Requête SQL d'une démarche : colonnes utiles des 3 tables, jointes par numéro de dossier."""
    alias = {"champs": "c", "annotations": "a", "dossiers": "d"}
    colonnes = ['c."dossier_number" AS "dossier_number"'] + [
        f'{alias[t]}."{col}" AS "{col}"'
        for t, cols in calc.colonnes_lues(type_mob).items() for col in cols
    ]
    return (
        f'SELECT {", ".join(colonnes)} FROM "{_table(type_mob, "champs")}" c '
        f'LEFT JOIN "{_table(type_mob, "annotations")}" a ON a."dossier_number" = c."dossier_number" '
        f'LEFT JOIN "{_table(type_mob, "dossiers")}" d ON d."dossier_number" = c."dossier_number"'
    )


def _lire_sql(type_mob: str) -> tuple[list[dict], dict]:
    debut = time.perf_counter()
    api = GristService(DOCS[type_mob], kit.GRIST_TEAM_SITE, kit.GRIST_SERVER).grist
    status, rows = api.run_sql(_sql_demarche(type_mob))
    if status != 200:
        raise RuntimeError(f"SQL {type_mob} : HTTP {status} {rows}")
    ms = round((time.perf_counter() - debut) * 1000)
    nom = f"Demarche_{calc.DEMARCHES[type_mob]['numero']} (SQL)"
    logger.warning("Dashboard : %s lue en %d ms (%d lignes)", nom, ms, len(rows))
    return rows, {"table": nom, "lignes": len(rows), "ms": ms}


def _charger_sql() -> tuple[dict, list]:
    """Financier Erasmus + une requête SQL par démarche, en parallèle."""
    with ThreadPoolExecutor(max_workers=len(calc.TYPES) + 1) as pool:
        financier = pool.submit(_lire, kit.GRIST_DOC_ID, calc.TABLE_FINANCIER)
        demarches = {t: pool.submit(_lire_sql, t) for t in calc.TYPES}
        rows_fin, chrono_fin = financier.result()
        resultats = {t: f.result() for t, f in demarches.items()}
    donnees = {
        "projets": calc.projets(rows_fin),
        "mobilites": [m for t, (rows, _) in resultats.items() for m in calc.mobilites_jointes(t, rows)],
    }
    return donnees, [chrono_fin] + [c for _, c in resultats.values()]


def _charger_tables() -> tuple[dict, list]:
    """Repli : lecture complète des tables."""
    tables, chrono = _lire_tables()
    donnees = {
        "projets": calc.projets(tables[calc.TABLE_FINANCIER]),
        "mobilites": [
            m for t in calc.TYPES
            for m in calc.mobilites_demarche(t, *(tables[_table(t, s)] for s in SUFFIXES))
        ],
    }
    return donnees, chrono


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
    try:
        donnees, chrono = _charger_sql()
        mode, erreur = "sql", None
    except Exception as exc:  # colonne absente, SQL refusé… : lecture complète
        logger.warning("Dashboard : SQL impossible (%s), lecture complète des tables", exc)
        donnees, chrono = _charger_tables()
        mode, erreur = "tables", str(exc)[:300]
    donnees["chargement"] = {"ms": round((time.perf_counter() - debut) * 1000), "tables": chrono,
                             "memoire": False, "mode": mode, "erreur_sql": erreur}
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
