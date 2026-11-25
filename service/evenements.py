"""
Mises à jour partagées entre utilisateurs (sans actualiser la page).

Chaque génération ou envoi réussi devient un évènement numéroté. Les navigateurs ouverts
interrogent /api/evenements?depuis=<n> toutes les quelques secondes et appliquent ce qui a
changé (requête légère : ni Grist ni DN). En mémoire : l'app tourne en un seul processus ;
après un redémarrage, les navigateurs voient que la numérotation est repartie et rechargent.

Les statuts « généré » (PDF vérifié, non conservé) sont aussi gardés ici, pour que chacun les
voie en ouvrant la page, et plus seulement l'utilisateur qui a généré.
"""

import threading
import time
import uuid

GARDER = 1000  # évènements conservés ; au-delà, un navigateur trop en retard recharge la liste

_verrou = threading.Lock()
_evenements: list[dict] = []
_version = 0
_generes: dict = {}  # {vue: {dossier: {document: "genere"}}}
# Identifie ce démarrage : un navigateur qui voit une autre instance recharge (numérotation repartie)
INSTANCE = uuid.uuid4().hex[:8]


def vue_du_document(document: str) -> str:
    if document.endswith("_groupe"):
        return "groupes"
    if document.endswith("_personnel"):
        return "personnel"
    return "apprenants"


def champ_envoi(document: str) -> str:
    return "envoye_financier" if document.startswith("financier") else "envoye_pedagogique"


def version() -> int:
    return _version


def _ajouter(evenement: dict) -> None:
    global _version
    with _verrou:
        _version += 1
        _evenements.append({"v": _version, "t": time.time(), **evenement})
        del _evenements[:-GARDER]


def genere(document: str, dossiers, par: str, qui: str) -> None:
    vue = vue_du_document(document)
    with _verrou:
        for n in dossiers:
            _generes.setdefault(vue, {}).setdefault(str(n), {})[document] = "genere"
    for n in dossiers:
        _ajouter({"type": "genere", "vue": vue, "dossier": str(n), "document": document, "par": par, "qui": qui})


def envoye(document: str, dossier, par: str, qui: str) -> None:
    _ajouter({"type": "envoye", "vue": vue_du_document(document), "dossier": str(dossier),
              "document": document, "champ": champ_envoi(document), "par": par, "qui": qui})


def recharger(vue: str, par: str, qui: str) -> None:
    """La liste d'une page a été relue dans Grist ou recalée sur DN : les autres la rechargent."""
    _ajouter({"type": "recharger", "vue": vue, "par": par, "qui": qui})


def statuts_generes(vue: str) -> dict:
    with _verrou:
        return {n: dict(docs) for n, docs in _generes.get(vue, {}).items()}


def depuis(v: int) -> dict:
    with _verrou:
        if _evenements and v < _evenements[0]["v"] - 1:
            return {"version": _version, "instance": INSTANCE, "recharger": True, "evenements": []}
        return {"version": _version, "instance": INSTANCE,
                "evenements": [e for e in _evenements if e["v"] > v]}
