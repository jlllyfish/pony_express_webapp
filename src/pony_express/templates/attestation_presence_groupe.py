"""Attestation de présence Europass pour les activités de groupe (démarche DN 156967)."""
import os
from copy import deepcopy

from slugify import slugify

from pony_express.service.grist import GristService
from pony_express.service.ponyexpress import generate_pdf_from_grist
from pony_express.service.utils import clean_text, group_blocks

# outils communs (sans effet de bord sur les tables de ce module)
from pony_express.templates.contrat_financier import (
    build_enum, build_reference_tables, set_date, set_duree, set_joined, value,
)
from pony_express.templates.contrat_pedagogique_groupe import lignes, personnes, set_or_drop

# Accès au document Grist (même document que les mobilités individuelles)
GRIST_SERVER = os.environ["GRIST_SERVER"]
GRIST_TEAM_SITE = os.environ["GRIST_TEAM_SITE"]
GRIST_DOC_ID = os.environ["GRIST_DOC_ID"]
GRIST_PDF_COLUMN = None

# Tables OTP de la démarche de groupe, reliées par le numéro de dossier
DEMARCHE = "156967"
GRIST_TABLE = os.environ.get("GRIST_TABLE_GROUPE", f"Demarche_{DEMARCHE}_champs")  # table principale
TABLE_ANNOTATIONS = f"Demarche_{DEMARCHE}_annotations"
TABLE_ACCOMPAGNATEURS = f"Demarche_{DEMARCHE}_repetable_autre_s_accompagnateur_s"
TABLE_ETABLISSEMENTS = "Etablissements"
BLOCK_KEY = "dossier_number"
BLOCK_ORDER = "block_row_index"

# Template Typst
TEMPLATE_NAME = "attestation_presence_groupe"
TEMPLATE_FILENAME = "attestation_presence_groupe_template"
TEMPLATE_FOLDERNAME = "attestation_presence_groupe"


# =====================================================================
# RUBRIQUES : {paramètre du template Typst : colonne Grist}
# Un paramètre déclaré nulle part s'affiche « [donnée manquante] ».
# =====================================================================

# Table principale (GRIST_TABLE = table champs : une ligne par dossier)
PRINCIPALE = {
    "numero_dossier": "dossier_number",
    "etablissement": "votre_etablissement",  # valeur = ref_etab_DN
    "date_debut": "date_debut_activite_hors_jours_de_voyage",
    "date_fin": "date_fin_activite_hors_jours_de_voyage",
    "pays": "pays_d_accueil_nom",
    "pays_libelle": "pays_d_accueil",  # « Italie (IT) »
    "ville": "ville_pays_d_accueil",
    # un participant par ligne, dans chaque établissement
    "participants_envoi": "liste_des_participants_de_l_etablissement_d_envoi",
    "participants_accueil": "liste_des_participants_de_l_etablissement_d_accueil",
    # accompagnateur référent (les autres : répétable)
    "ref_nom": "nom_accompagnateur_referent",
    "ref_prenom": "prenom_accompagnateur_referent",
    # organisme d'accueil et son responsable (signataire)
    "organisation_accueil_nom": "nom_de_l_organisme_d_accueil",
    "organisation_accueil_adresse": "adresse_organisme_d_accueil",
    "accueil_resp_nom": "nom_responsable_organisme_d_accueil",
    "accueil_resp_prenom": "prenom_responsable_organisme_d_accueil",
}

# Tables jointes : une ligne par dossier
JOINTES = {
    TABLE_ANNOTATIONS: {
        "code_projet": "code_projet",
    },
}

BLOCS = {
    "accompagnants": (TABLE_ACCOMPAGNATEURS, {"nom": "nom", "prenom": "prenom"}),
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
#   titre_activite, pays_ville, duree, date_debut_en / date_fin_en (format américain),
#   participants (envoi, accompagnateurs, puis accueil), date_signature_accueil (= date de fin)


STUDENT_DATA = build_enum("STUDENT_DATA", PRINCIPALE, JOINTES, module=__name__)


def _extra_tables() -> dict:
    tables = build_reference_tables(REFERENCES)
    for table, columns in BLOCS.values():
        tables[table] = [BLOCK_KEY, BLOCK_ORDER, *columns.values()]
    return tables


EXTRA_TABLES = _extra_tables()


def should_be_exported(record: dict) -> bool:
    """True si la ligne doit produire un PDF (ajouter ici un filtre, ex : statut)."""
    return True


def name_pdf(record) -> str:
    return slugify(f"groupe_{record.get('numero_dossier', record['id'])}_{record.get('ville', '')}_attestation")


def apply_data_transformation(data: dict) -> dict:
    transformed = deepcopy(data)
    set_date(transformed, "date_debut")
    set_date(transformed, "date_fin")
    set_duree(transformed, "duree", "date_debut", "date_fin")
    pays, ville = value(data, "pays"), value(data, "ville")
    set_joined(transformed, "pays_ville", [value(data, "pays_libelle") or pays, ville])
    set_joined(transformed, "titre_activite", [f"Mobilité de groupe – {ville}" if ville else "", f"({pays})" if pays else ""], " ")
    apply_references(transformed, data)

    # participants de l'établissement d'envoi, accompagnateurs, puis participants de l'accueil
    envoi = transformed.get("organisation_envoi_nom", "")
    accueil = transformed.get("organisation_accueil_nom", "")
    accompagnateurs = [f"{p['nom'].upper()} {p.get('prenom', '')}".strip() for p in liste_accompagnateurs(data)]
    set_or_drop(transformed, "participants",
                [(nom, envoi) for nom in lignes(value(data, "participants_envoi")) + accompagnateurs]
                + [(nom, accueil) for nom in lignes(value(data, "participants_accueil"))])

    # la personne responsable de l'organisme d'accueil signe à la date de fin
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


def liste_accompagnateurs(data: dict) -> list[dict]:
    """Référent, puis les autres accompagnateurs du répétable (nom renseigné)."""
    _, colonnes = BLOCS["accompagnants"]
    autres = [{champ: value(b, col) for champ, col in colonnes.items()}
              for b in get_blocks(TABLE_ACCOMPAGNATEURS, data.get("numero_dossier"))]
    return personnes(data, "ref") + [p for p in autres if p.get("nom")]


def fetch_table(table: str) -> list[dict]:
    """Lit une table Grist entière (remplacée par check_mapping.py en mode hors-ligne)."""
    return GristService(GRIST_DOC_ID, GRIST_TEAM_SITE, GRIST_SERVER).get_table_records(table)


_blocks_cache: dict[str, dict] = {}


def get_blocks(table: str, dossier_number) -> list[dict]:
    """Blocs répétables d'un dossier, dans l'ordre. Chaque table n'est lue qu'une fois."""
    if table not in _blocks_cache:
        _blocks_cache[table] = group_blocks(fetch_table(table), BLOCK_KEY, BLOCK_ORDER)
    try:
        return _blocks_cache[table].get(int(dossier_number), [])
    except (TypeError, ValueError):
        return []


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
    print("GENERATE ATTESTATIONS DE PRESENCE DE GROUPE")
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
