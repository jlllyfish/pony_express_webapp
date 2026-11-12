"""Attestation de présence Europass (après la mobilité) : une page, signatures envoi / accueil."""
import os
from copy import deepcopy

from slugify import slugify

from pony_express.service.grist import GristService
from pony_express.service.ponyexpress import generate_pdf_from_grist
from pony_express.service.utils import clean_text

# outils communs (sans effet de bord sur les tables de ce module)
from pony_express.templates.contrat_financier import (
    build_enum, build_reference_tables, premier_prenom, set_date, set_duree, set_joined, value,
)

# Accès au document Grist
GRIST_SERVER = os.environ["GRIST_SERVER"]
GRIST_TEAM_SITE = os.environ["GRIST_TEAM_SITE"]
GRIST_DOC_ID = os.environ["GRIST_DOC_ID"]
GRIST_TABLE = os.environ["GRIST_TABLE"]  # table principale (ex : Demarche_128447_annotations)
GRIST_PDF_COLUMN = None

# Template Typst
TEMPLATE_NAME = "attestation_presence"
TEMPLATE_FILENAME = "attestation_presence_template"
TEMPLATE_FOLDERNAME = "attestation_presence"

# Tables OTP de la démarche, reliées par le numéro de dossier
DEMARCHE = "128447"
TABLE_CHAMPS = f"Demarche_{DEMARCHE}_champs"
TABLE_ETABLISSEMENTS = "Etablissements"


# =====================================================================
# RUBRIQUES : {paramètre du template Typst : colonne Grist}
# Un paramètre déclaré nulle part s'affiche « [donnée manquante] ».
# =====================================================================

# Table principale (GRIST_TABLE)
PRINCIPALE = {
    "numero_dossier": "dossier_number",
    "code_projet": "code_projet",
    "participant_nom": "nom_participant",
    "participant_prenom": "prenom_s_participant",
}

# Tables jointes : une ligne par dossier
JOINTES = {
    TABLE_CHAMPS: {
        "date_debut": "date_debut_activite_hors_jours_de_voyage",
        "date_fin": "date_fin_activite_hors_jours_de_voyage",
        "pays": "pays_d_accueil",
        "ville": "ville_pays_d_accueil",
        "etablissement": "votre_etablissement",  # valeur = ref_etab_DN
        "organisation_accueil_nom": "nom_de_l_organisme_d_accueil",
        "organisation_accueil_adresse": "adresse_organisme_d_accueil",
        "accueil_resp_nom": "nom_responsable_organisme_d_accueil",
        "accueil_resp_prenom": "prenom_responsable_organisme_d_accueil",
    },
}

# Tables de référence : UNE ligne choisie pour le dossier
REFERENCES = {
    TABLE_ETABLISSEMENTS: {
        "lien": ("etablissement", "ref_etab_DN"),
        "champs": {
            "organisation_envoi_nom": "Nom_etablissement",
            "organisation_envoi_adresse": "Adresse",
            "envoi_direction_nom": "Nom_direction",
            "envoi_direction_prenom": "Prenom_direction",
        },
    },
}

# Calculés dans apply_data_transformation :
#   pays_ville, duree, participant_premier_prenom,
#   date_signature_accueil (= date de fin de stage, pré-remplie dans le bloc de l'organisme d'accueil),
#   date_debut_en, date_fin_en (format américain pour la traduction anglaise)

STUDENT_DATA = build_enum("STUDENT_DATA", PRINCIPALE, JOINTES, module=__name__)
EXTRA_TABLES = build_reference_tables(REFERENCES)


def should_be_exported(record: dict) -> bool:
    """True si la ligne doit produire un PDF (ajouter ici un filtre, ex : statut)."""
    return True


def name_pdf(record) -> str:
    return slugify(f"{record['participant_nom']}_{record['participant_prenom']}_{record['id']}_attestation")


def apply_data_transformation(data: dict) -> dict:
    transformed = deepcopy(data)
    set_date(transformed, "date_debut")
    set_date(transformed, "date_fin")
    set_duree(transformed, "duree", "date_debut", "date_fin")
    set_joined(transformed, "pays_ville", [value(data, "pays"), value(data, "ville")])
    transformed["participant_premier_prenom"] = premier_prenom(value(data, "participant_prenom"))
    apply_references(transformed, data)
    # la personne responsable de l'organisme d'accueil signe à la date de fin de stage
    if "date_fin" in transformed:
        transformed["date_signature_accueil"] = transformed["date_fin"]
    # traduction anglaise : dates au format américain (mm/dd/yyyy)
    for key in ("date_debut", "date_fin"):
        if key in transformed:
            jour, mois, annee = transformed[key].split(".")
            transformed[key + "_en"] = f"{mois}/{jour}/{annee}"
    # colonne vide ou absente de Grist : [donnée manquante] plutôt qu'une case blanche
    for param in list(transformed):
        val = transformed[param]
        if param in STUDENT_DATA.__members__ and val in ("", None):
            transformed.pop(param)
        elif isinstance(val, str) and val.endswith(" is not in GRIST"):
            transformed.pop(param)
    return transformed


# =====================================================================
# Outils
# =====================================================================


def fetch_table(table: str) -> list[dict]:
    """Lit une table Grist entière (remplacée par check_mapping.py en mode hors-ligne)."""
    return GristService(GRIST_DOC_ID, GRIST_TEAM_SITE, GRIST_SERVER).get_table_records(table)


_reference_cache: dict[str, list[dict]] = {}


def get_reference(table: str, lien, data: dict) -> dict | None:
    """Ligne de la table de référence correspondant au dossier (None si aucune ou ambiguë)."""
    if table not in _reference_cache:
        _reference_cache[table] = fetch_table(table)
    rows = _reference_cache[table]
    if lien is None:
        return rows[0] if len(rows) == 1 else None
    param, column = lien
    wanted = value(data, param).casefold()
    if not wanted:
        return None
    matches = [r for r in rows if clean_text(r.get(column)).casefold() == wanted]
    return matches[0] if len(matches) == 1 else None


def apply_references(transformed: dict, data: dict) -> None:
    """Remplit les champs des tables de référence ; sans correspondance : [donnée manquante]."""
    for table, ref in REFERENCES.items():
        row = get_reference(table, ref["lien"], data) or {}
        for param, column in ref["champs"].items():
            text = value(row, column)
            if text:
                transformed[param] = text
            else:
                transformed.pop(param, None)


if __name__ == "__main__":
    print("GENERATE ATTESTATIONS DE PRESENCE")
    generate_pdf_from_grist(
        GRIST_DOC_ID,
        GRIST_TEAM_SITE,
        GRIST_TABLE,
        STUDENT_DATA,
        TEMPLATE_FOLDERNAME,
        TEMPLATE_FILENAME,
        TEMPLATE_NAME,
        should_be_exported,
        apply_data_transformation,
        name_pdf,
        GRIST_SERVER,
        GRIST_PDF_COLUMN,
    )
