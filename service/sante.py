"""
État de santé des services externes (Grist, Démarches Numériques), en lecture seule.

Appelé au chargement de l'interface et à chaque rafraîchissement : repère une
clé ou un jeton refusé, un document ou une table introuvable, une démarche
inaccessible, avant qu'une génération ou un envoi n'échoue en cours de route.
"""

import time
from datetime import datetime

import requests
from pony_express.service.grist import GristService
from pony_express.templates import contrat_pedagogique as kit

from service import dashboard, dn
from service.generation import TEMPLATES

TIMEOUT = 15  # secondes


def _tables_attendues() -> dict:
    """{doc_id: {tables}} : tables lues par les templates et par l'interface."""
    attendues: dict[str, set] = {}
    for tpl, _ in TEMPLATES.values():
        tables = attendues.setdefault(tpl.GRIST_DOC_ID, set())
        for nom in dir(tpl):
            valeur = getattr(tpl, nom)
            if (nom == "GRIST_TABLE" or nom.startswith("TABLE_")) and isinstance(valeur, str):
                tables.add(valeur)
        tables.update(getattr(tpl, "EXTRA_TABLES", {}).keys())
    for dem in dn.DEMARCHES.values():
        attendues.setdefault(dem["doc_id"], set()).update(
            {dem["table_dossiers"], dem["table_annotations"]}
        )
    # table champs des groupes (page Groupe)
    attendues.setdefault(dn.DEMARCHES["groupes"]["doc_id"], set()).add("Demarche_156967_champs")
    # tableau de bord : financier + tables des trois démarches
    attendues.setdefault(kit.GRIST_DOC_ID, set()).add(dashboard.TABLE_FINANCIER)
    for dem in dashboard.DEMARCHES.values():
        attendues.setdefault(dem["doc_id"], set()).update(
            f"Demarche_{dem['numero']}_{suffixe}" for suffixe in ("champs", "annotations", "dossiers")
        )
    return attendues


def _ids_tables(api) -> set:
    """Ids des tables du document (pygrister : (status, liste))."""
    status, tables = api.list_tables()
    if status != 200:
        raise RuntimeError(f"HTTP {status}")
    return {t["id"] if isinstance(t, dict) else str(t) for t in tables}


def _message_erreur(exc: Exception) -> str:
    texte = str(exc)
    if "401" in texte or "403" in texte:
        return "Accès refusé : vérifie GRIST_API_KEY et les droits sur le document."
    if "404" in texte:
        return "Document introuvable : vérifie GRIST_DOC_ID, GRIST_TEAM_SITE et GRIST_SERVER."
    if "timed out" in texte.lower() or "timeout" in texte.lower():
        return "Grist ne répond pas (délai dépassé)."
    return texte[:300]


def verifier_grist() -> dict:
    debut = time.monotonic()
    manquantes = []
    try:
        for doc_id, tables in _tables_attendues().items():
            api = GristService(doc_id, kit.GRIST_TEAM_SITE, kit.GRIST_SERVER).grist
            presentes = _ids_tables(api)
            manquantes += sorted(t for t in tables if t not in presentes)
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "message": _message_erreur(exc), "ms": _ms(debut)}
    if manquantes:
        return {
            "ok": False,
            "message": "Tables absentes du document Grist : " + ", ".join(manquantes),
            "ms": _ms(debut),
        }
    return {"ok": True, "message": "Document et tables accessibles", "ms": _ms(debut)}


def _graphql(query: str, variables: dict) -> dict:
    resp = requests.post(
        dn.API_URL,
        headers=dn.HEADERS,
        json={"query": query, "variables": variables},
        timeout=TIMEOUT,
    )
    if resp.status_code in (401, 403):
        raise RuntimeError("Jeton refusé : vérifie DN_API_TOKEN.")
    resp.raise_for_status()
    data = resp.json()
    if "errors" in data:
        raise RuntimeError("; ".join(e.get("message", "") for e in data["errors"])[:300])
    return data["data"]


def verifier_dn() -> dict:
    debut = time.monotonic()
    avertissements = []
    try:
        for nom, dem in dn.DEMARCHES.items():
            data = _graphql(
                "query($n: Int!) { demarche(number: $n) { number title } }", {"n": dem["numero"]}
            )
            if not data.get("demarche"):
                return {
                    "ok": False,
                    "message": f"Démarche {dem['numero']} ({nom}) inaccessible avec ce jeton.",
                    "ms": _ms(debut),
                }
            # L'instructeur doit appartenir à un groupe de la démarche (sinon : envoi refusé)
            try:
                data = _graphql(
                    "query($n: Int!) { demarche(number: $n) "
                    "{ groupeInstructeurs { instructeurs { id } } } }",
                    {"n": dem["numero"]},
                )
                ids = {
                    i["id"]
                    for g in data["demarche"]["groupeInstructeurs"]
                    for i in g["instructeurs"]
                }
                if dn.INSTRUCTEUR_ID not in ids:
                    return {
                        "ok": False,
                        "message": (
                            f"INSTRUCTEUR_ID n'est pas instructeur de la démarche "
                            f"{dem['numero']} ({nom})."
                        ),
                        "ms": _ms(debut),
                    }
            except Exception:  # noqa: BLE001 - vérification secondaire, non bloquante
                avertissements.append(f"instructeur non vérifié ({nom})")
    except requests.Timeout:
        return {"ok": False, "message": "DN ne répond pas (délai dépassé).", "ms": _ms(debut)}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "message": str(exc)[:300], "ms": _ms(debut)}
    message = "Jeton valide, démarches 128447 et 156967 accessibles"
    if avertissements:
        message += " (" + ", ".join(avertissements) + ")"
    return {"ok": True, "message": message, "ms": _ms(debut)}


def _ms(debut: float) -> int:
    return round((time.monotonic() - debut) * 1000)


def etat_de_sante() -> dict:
    return {
        "grist": verifier_grist(),
        "dn": verifier_dn(),
        "heure": datetime.now().strftime("%H:%M"),
    }
