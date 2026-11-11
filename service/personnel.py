"""
Mobilités du personnel (démarche 156966) : liste affichée dans la page Personnel.

Génération : gabarits contrat_pedagogique_personnel, attestation_presence_personnel
et contrat_financier_personnel de Pony_express (voir generation.py).
Envoi vers DN : voir dn.py (identifiants des annotations à configurer).
"""

import os

from pony_express.service.grist import GristService
from pony_express.service.utils import clean_text, get_date_from_timestamp
from pony_express.templates import contrat_pedagogique as kit

from service.grist_lecture import avec_repli, colonnes_jointes

DEMARCHE_PERSONNEL = 156966
TABLE_CHAMPS = f"Demarche_{DEMARCHE_PERSONNEL}_champs"
TABLE_ANNOTATIONS = f"Demarche_{DEMARCHE_PERSONNEL}_annotations"
TABLE_DOSSIERS = f"Demarche_{DEMARCHE_PERSONNEL}_dossiers"

# Même document Grist que les apprenants, sauf si GRIST_DOC_ID_PERSONNEL est défini
GRIST_DOC_ID = os.environ.get("GRIST_DOC_ID_PERSONNEL") or kit.GRIST_DOC_ID

# Colonnes des cases « envoyé » dans les annotations (mêmes noms que les autres démarches par défaut)
COL_ENVOYE_PEDAGOGIQUE = os.environ.get("GRIST_PERSONNEL_ENVOYE_PEDAGOGIQUE", "contrat_pedagogique_et_attestation_de_presence_envoyes_par_l_ensfea")
COL_ENVOYE_FINANCIER = os.environ.get("GRIST_PERSONNEL_ENVOYE_FINANCIER", "contrat_financier_envoye_par_l_ensfea")

# Colonnes lues (les autres colonnes des tables ne sont pas téléchargées)
COLONNES_CHAMPS = [
    "dossier_number",
    "nom",
    "prenom",
    "votre_etablissement",
    "pays_d_accueil",
    "ville_du_pays_d_accueil",
    "type_de_mobilite_de_personnel",
    "type_de_transport",
    "date_debut_activite_hors_jours_de_voyage",
    "date_fin_activite_hors_jours_de_voyage",
]
COLONNES_ANNOTATIONS = [COL_ENVOYE_PEDAGOGIQUE, COL_ENVOYE_FINANCIER]
COLONNES_DOSSIERS = ["state"]


def _grist() -> GristService:
    return GristService(GRIST_DOC_ID, kit.GRIST_TEAM_SITE, kit.GRIST_SERVER)


def _date(row: dict, column: str) -> str:
    """Date au format jj-mm-aa ; chaîne vide si absente ou illisible."""
    try:
        return get_date_from_timestamp(row[column])
    except (KeyError, TypeError, ValueError):
        return ""


def _par_dossier(rows: list[dict]) -> dict:
    return {str(r.get("dossier_number")): r for r in rows}


def _lignes_completes() -> list[dict]:
    """Repli : tables entières, fusionnées par numéro de dossier."""
    grist = _grist()
    annotations = _par_dossier(grist.get_table_records(TABLE_ANNOTATIONS))
    dossiers = _par_dossier(grist.get_table_records(TABLE_DOSSIERS))
    lignes = []
    for row in grist.get_table_records(TABLE_CHAMPS):
        numero = str(row.get("dossier_number"))
        annot = {c: annotations.get(numero, {}).get(c) for c in COLONNES_ANNOTATIONS}
        lignes.append(row | annot | {"state": dossiers.get(numero, {}).get("state")})
    return lignes


def list_personnel() -> list[dict]:
    # Une requête SQL ciblée (colonnes ci-dessus) ; tables entières si elle échoue
    lignes = avec_repli(
        "Page Personnel",
        lambda: colonnes_jointes(GRIST_DOC_ID, TABLE_CHAMPS, COLONNES_CHAMPS,
                                 {TABLE_ANNOTATIONS: COLONNES_ANNOTATIONS, TABLE_DOSSIERS: COLONNES_DOSSIERS}),
        _lignes_completes,
    )

    personnes = []
    for row in lignes:
        nom = clean_text(row.get("nom"))
        prenom = kit.premier_prenom(clean_text(row.get("prenom")))
        personnes.append(
            {
                "dossier_number": str(row.get("dossier_number")),
                "demarche": DEMARCHE_PERSONNEL,
                "nom": nom,
                "prenom": prenom,
                "nom_complet": f"{nom} {prenom}".strip(),
                "etablissement": clean_text(row.get("votre_etablissement")) or "Non renseigné",
                "pays_accueil": clean_text(row.get("pays_d_accueil")),
                "ville_accueil": clean_text(row.get("ville_du_pays_d_accueil")),
                "type_mobilite": clean_text(row.get("type_de_mobilite_de_personnel")),
                "type_transport": clean_text(row.get("type_de_transport")),
                "date_debut_activite": _date(row, "date_debut_activite_hors_jours_de_voyage"),
                "date_fin_activite": _date(row, "date_fin_activite_hors_jours_de_voyage"),
                "state": clean_text(row.get("state")),
                "envoye_pedagogique": bool(row.get(COL_ENVOYE_PEDAGOGIQUE)),
                "envoye_financier": bool(row.get(COL_ENVOYE_FINANCIER)),
                # statut de génération, non persisté (mémoire de la session)
                "statuts": {"pedagogique_personnel": "non_genere", "financier_personnel": "non_genere"},
            }
        )
    personnes.sort(key=lambda p: (p["nom"].lower(), p["prenom"].lower(), p["dossier_number"]))
    return personnes
