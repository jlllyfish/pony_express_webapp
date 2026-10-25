"""
Mobilités de groupe (démarche 156967) : liste affichée dans la page Groupe.

Génération et envoi du contrat pédagogique de groupe : voir generation.py et dn.py.
"""

import os

from pony_express.service.grist import GristService
from pony_express.service.utils import clean_text, get_date_from_timestamp
from pony_express.templates import contrat_pedagogique as kit

DEMARCHE_GROUPE = 156967
TABLE_CHAMPS = f"Demarche_{DEMARCHE_GROUPE}_champs"
TABLE_ANNOTATIONS = f"Demarche_{DEMARCHE_GROUPE}_annotations"
TABLE_DOSSIERS = f"Demarche_{DEMARCHE_GROUPE}_dossiers"

# Même document Grist que les apprenants, sauf si GRIST_DOC_ID_GROUPE est défini
GRIST_DOC_ID = os.environ.get("GRIST_DOC_ID_GROUPE") or kit.GRIST_DOC_ID


def _grist() -> GristService:
    return GristService(GRIST_DOC_ID, kit.GRIST_TEAM_SITE, kit.GRIST_SERVER)


def _date(row: dict, column: str) -> str:
    """Date au format jj-mm-aa ; chaîne vide si absente ou illisible."""
    try:
        return get_date_from_timestamp(row[column])
    except (KeyError, TypeError, ValueError):
        return ""


def _entier(value):
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def _par_dossier(rows: list[dict]) -> dict:
    return {str(r.get("dossier_number")): r for r in rows}


def list_groupes() -> list[dict]:
    grist = _grist()
    champs = grist.get_table_records(TABLE_CHAMPS)
    annotations = _par_dossier(grist.get_table_records(TABLE_ANNOTATIONS))
    dossiers = _par_dossier(grist.get_table_records(TABLE_DOSSIERS))

    groupes = []
    for row in champs:
        numero = str(row.get("dossier_number"))
        annot = annotations.get(numero, {})
        dossier = dossiers.get(numero, {})
        groupes.append(
            {
                "dossier_number": numero,
                "demarche": DEMARCHE_GROUPE,
                "titre": clean_text(row.get("centre_constitutif_du_participant")),
                "etablissement": clean_text(row.get("votre_etablissement")) or "Non renseigné",
                "pays_accueil": clean_text(row.get("pays_d_accueil_nom")),
                "date_debut_activite": _date(row, "date_debut_activite_hors_jours_de_voyage"),
                "date_fin_activite": _date(row, "date_fin_activite_hors_jours_de_voyage"),
                "date_trajet_aller": _date(row, "date_de_trajet_aller"),
                "date_trajet_retour": _date(row, "date_de_trajet_retour"),
                "effectif": _entier(row.get("nombre_d_apprenants_total")),
                "accompagnateurs": clean_text(row.get("combien_d_accompagnateurs_sont_prevus")),
                "state": clean_text(dossier.get("state")),
                "envoye_pedagogique": bool(annot.get("contrat_pedagogique_envoye_par_l_ensfea")),
                "envoye_financier": bool(annot.get("contrat_financier_envoye_par_l_ensfea")),
                # statut de génération, non persisté (mémoire de la session)
                "statuts": {"pedagogique_groupe": "non_genere", "financier_groupe": "non_genere"},
            }
        )
    groupes.sort(key=lambda g: (g["titre"].lower(), g["dossier_number"]))
    return groupes
