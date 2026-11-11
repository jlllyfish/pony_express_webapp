"""Contrat financier Erasmus+ pour les mobilités de groupe (démarche DN 156967)."""
import os
import re
from copy import deepcopy

from slugify import slugify

from pony_express.service.grist import GristService
from pony_express.service.ponyexpress import generate_pdf_from_grist
from pony_express.service.utils import clean_text, group_blocks

# outils communs (sans effet de bord sur les tables de ce module)
from pony_express.templates.contrat_financier import (
    build_enum, build_reference_tables, set_date, set_duree, set_joined, set_montant, value,
)
from pony_express.templates.contrat_pedagogique_groupe import lignes, personnes, ville_depuis_adresse

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
TEMPLATE_NAME = "contrat_financier_groupe"
TEMPLATE_FILENAME = "contrat_financier_groupe_template"
TEMPLATE_FOLDERNAME = "contrat_financier_groupe"


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
    "liste_participants": "liste_des_participants_de_l_etablissement_d_envoi",  # un apprenant par ligne
    # accompagnateur référent (les autres : répétable)
    "ref_nom": "nom_accompagnateur_referent",
    "ref_prenom": "prenom_accompagnateur_referent",
    "option_prise_en_charge": "choix_de_la_modalite_de_prise_en_charge_de_la_bourse",
    "assurance_responsable": "partie_responsable_de_la_souscription_de_l_assurance",
    "compagnie_assurance": "compagnie_d_assurance",
    "numero_police_assurance": "numero_et_police_d_assurance",
}

# Tables jointes : une ligne par dossier
JOINTES = {
    TABLE_ANNOTATIONS: {
        "code_projet": "code_projet",
        # montants PAR PERSONNE (identiques pour tous les apprenants / accompagnateurs du dossier)
        "duree_voyage": "nombre_de_jours_de_voyage",
        "voyage_participant": "montant_frais_de_voyage_par_participant",
        "apprenant_sejour": "montant_frais_de_sejour_apprenant",
        "apprenant_bourse": "montant_total_bourse_apprenant_voyage_sejour",
        "accompagnateur_sejour": "montant_frais_de_sejour_accompagnateur",
        "accompagnateur_bourse": "montant_total_bourse_accompagnateur_voyage_sejour",
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
            "organisme_envoi_nom": "Nom_etablissement",
            "organisme_envoi_statut_juridique": "Statut",
            "organisme_envoi_adresse": "Adresse",
            "organisme_envoi_email": "Mail",
            "organisme_envoi_code": "Code_OID",
            "envoi_direction_nom": "Nom_direction",
            "envoi_direction_prenom": "Prenom_direction",
        },
    },
}

# Valeurs identiques pour tous les dossiers
CONSTANTES = {
    "organisme_envoi_representant_fonction": "Directeur·rice",
    "limite_prolongation": "0",   # article 3.3 (jours)
    "accompte_pourcentage": "80",  # article 5.1 (%)
}

# Calculés dans apply_data_transformation :
#   titre_activite, pays_ville, duree, duree_jours_bourse (= jours d'activité + jours de voyage),
#   participants_frais (apprenants puis accompagnateurs, montants par personne des annotations),
#   frais_sejour / frais_voyage / valeur_bourse (totaux, seulement si tous les montants sont connus),
#   organisme_envoi_representant_nom_complet, option_prise_en_charge normalisée


STUDENT_DATA = build_enum("STUDENT_DATA", PRINCIPALE, JOINTES, module=__name__)


def _extra_tables() -> dict:
    tables = build_reference_tables(REFERENCES)
    for table, columns in BLOCS.values():
        tables[table] = [BLOCK_KEY, BLOCK_ORDER, *columns.values()]
    return tables


EXTRA_TABLES = _extra_tables()

MANQUANT = "[donnée manquante]"


def should_be_exported(record: dict) -> bool:
    """True si la ligne doit produire un PDF (ajouter ici un filtre, ex : statut)."""
    return True


def name_pdf(record) -> str:
    return slugify(f"groupe_{record.get('numero_dossier', record['id'])}_{record.get('ville', '')}_financier")


def apply_data_transformation(data: dict) -> dict:
    transformed = deepcopy(data)
    set_date(transformed, "date_debut")
    set_date(transformed, "date_fin")
    set_duree(transformed, "duree", "date_debut", "date_fin")
    pays, ville = value(data, "pays"), value(data, "ville")
    set_joined(transformed, "pays_ville", [value(data, "pays_libelle") or pays, ville])
    set_joined(transformed, "titre_activite", [f"Mobilité de groupe – {ville}" if ville else "", f"({pays})" if pays else ""], " ")

    apply_references(transformed, data)
    set_joined(transformed, "organisme_envoi_representant_nom_complet",
               [transformed.get("envoi_direction_prenom", ""), transformed.get("envoi_direction_nom", "").upper()], " ")

    # jours de bourse = jours d'activité (bornes incluses) + jours de voyage
    try:
        jours = int(transformed["duree"].split()[0]) + int(float(value(data, "duree_voyage") or 0))
        transformed["duree_jours_bourse"] = str(jours)
    except (KeyError, ValueError):
        transformed.pop("duree_jours_bourse", None)

    # tableau des frais : apprenants de l'établissement d'envoi, puis accompagnateurs
    #   (montants par personne des annotations ; voyage identique pour tous)
    montants = {}
    for cle in ("voyage_participant", "apprenant_sejour", "apprenant_bourse", "accompagnateur_sejour", "accompagnateur_bourse"):
        set_montant(montants, cle, data)
    voyage = montants.get("voyage_participant", MANQUANT)
    apprenant = ("Apprenant", montants.get("apprenant_sejour", MANQUANT), voyage, montants.get("apprenant_bourse", MANQUANT))
    accompagnant = ("Accompagnateur", montants.get("accompagnateur_sejour", MANQUANT), voyage, montants.get("accompagnateur_bourse", MANQUANT))
    lignes_frais = [(nom, *apprenant) for nom in lignes(value(data, "liste_participants"))]
    for p in accompagnateurs(data):
        lignes_frais.append((f"{p['nom'].upper()} {p.get('prenom', '')}".strip(), *accompagnant))
    if lignes_frais:
        transformed["participants_frais"] = lignes_frais
    # totaux seulement si tous les montants sont connus (sinon [donnée manquante])
    for i, cle in ((2, "frais_sejour"), (3, "frais_voyage"), (4, "valeur_bourse")):
        valeurs = [ligne[i] for ligne in lignes_frais]
        if valeurs and MANQUANT not in valeurs:
            set_montant(transformed, cle, {cle: str(sum(float(v.replace(" ", "").replace(",", ".")) for v in valeurs))})
        else:
            transformed.pop(cle, None)

    # « Option 1 : ... » -> code testé par le template (voir contrat financier individuel)
    libelle = value(data, "option_prise_en_charge")
    transformed.pop("option_prise_en_charge", None)
    option = re.search(r"option\s*(\d)", libelle, re.IGNORECASE)
    if option:
        transformed["option_libelle"] = libelle
        code = f"Option {option.group(1)}"
        if code == "Option 3":
            sans_accents = libelle.lower().replace("é", "e")
            code += " transport" if "transport" in sans_accents else " sejour" if "sejour" in sans_accents else ""
        transformed["option_prise_en_charge"] = code

    transformed.update(CONSTANTES)
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


def accompagnateurs(data: dict) -> list[dict]:
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
    print("GENERATE CONTRATS FINANCIERS DE GROUPE")
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
