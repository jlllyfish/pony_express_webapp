"""
Lectures Grist ciblées, partagées par les pages de l'interface.

- colonnes_jointes() : seulement les colonnes utiles d'une table, avec celles
  d'autres tables reliées par numéro de dossier (une requête SQL Grist).
- ligne_du_dossier() : la ou les lignes d'un seul dossier (filtre de l'API Grist).

En cas d'échec (colonne renommée, SQL indisponible…), l'appelant se replie
sur la lecture complète des tables : l'interface continue de fonctionner.
"""

import logging

from pony_express.service.grist import GristService
from pony_express.templates import contrat_pedagogique as kit

logger = logging.getLogger(__name__)
CLE = "dossier_number"


def _api(doc_id: str):
    return GristService(doc_id, kit.GRIST_TEAM_SITE, kit.GRIST_SERVER).grist


def requete_jointe(table: str, colonnes: list, jointures: dict | None = None) -> str:
    """SELECT des colonnes de `table` + celles des tables de `jointures` ({table: [colonnes]}),
    reliées par dossier_number (LEFT JOIN : une ligne de `table` sans correspondance est gardée)."""
    selection = [f't0."{c}" AS "{c}"' for c in colonnes]
    liens = []
    for i, (autre, cols) in enumerate((jointures or {}).items(), start=1):
        selection += [f't{i}."{c}" AS "{c}"' for c in cols]
        liens.append(f'LEFT JOIN "{autre}" t{i} ON t{i}."{CLE}" = t0."{CLE}"')
    return f'SELECT {", ".join(selection)} FROM "{table}" t0 {" ".join(liens)}'.strip()


def colonnes_jointes(doc_id: str, table: str, colonnes: list, jointures: dict | None = None) -> list[dict]:
    """Lignes de `table` réduites aux colonnes demandées (+ colonnes jointes). Lève une erreur si échec."""
    status, rows = _api(doc_id).run_sql(requete_jointe(table, colonnes, jointures))
    if status != 200:
        raise RuntimeError(f"SQL sur {table} : HTTP {status} {rows}")
    return rows


def ligne_du_dossier(doc_id: str, table: str, dossier_number) -> list[dict]:
    """Lignes de `table` pour un seul numéro de dossier (filtre côté Grist)."""
    status, rows = _api(doc_id).list_records(table, filter={CLE: [str(dossier_number)]})
    if status != 200:
        raise RuntimeError(f"Lecture filtrée de {table} : HTTP {status}")
    return rows


def avec_repli(nom: str, cible, complet):
    """Exécute la lecture ciblée ; en cas d'échec, journalise et fait la lecture complète."""
    try:
        return cible()
    except Exception as exc:  # noqa: BLE001
        logger.warning("%s : lecture ciblée impossible (%s), lecture complète", nom, exc)
        return complet()
