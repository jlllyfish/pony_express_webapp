"""Contrat financier Erasmus+ pour la mobilité du personnel (démarche DN 156966) : même modèle que les apprenants."""
import json
import os
import re
from copy import deepcopy
from datetime import datetime
from enum import Enum

from slugify import slugify

from pony_express.service.grist import GristService
from pony_express.service.ponyexpress import generate_pdf_from_grist
from pony_express.service.utils import clean_text, get_date_from_timestamp

# Accès au document Grist
GRIST_SERVER = os.environ["GRIST_SERVER"]
GRIST_TEAM_SITE = os.environ["GRIST_TEAM_SITE"]
GRIST_DOC_ID = os.environ["GRIST_DOC_ID"]
# même modèle de contrat que les apprenants : on réutilise le template contrat_financier
GRIST_PDF_COLUMN = None

# Template Typst
TEMPLATE_NAME = "contrat_financier"
TEMPLATE_FILENAME = "contrat_financier_template"
TEMPLATE_FOLDERNAME = "contrat_financier"

# Tables OTP de la démarche, reliées par le numéro de dossier
DEMARCHE = "156966"  # mobilité du personnel
GRIST_TABLE = os.environ.get("GRIST_TABLE_PERSONNEL", f"Demarche_{DEMARCHE}_champs")  # table principale
TABLE_ANNOTATIONS = f"Demarche_{DEMARCHE}_annotations"
TABLE_ETABLISSEMENTS = "Etablissements"


# =====================================================================
# RUBRIQUES : {paramètre du template Typst : colonne Grist}
# Un paramètre déclaré nulle part s'affiche « [donnée manquante] ».
# =====================================================================

# Table principale (GRIST_TABLE = table champs : une ligne par dossier)
PRINCIPALE = {
    "numero_dossier": "dossier_number",
    "participant_nom": "nom",
    "participant_prenom": "prenom",
    "participant_date_naissance": "date_de_naissance",
    "participant_adresse": "adresse_du_participant",  # champ adresse DN (JSON)
    "participant_telephone": "numero_de_telephone",
    "participant_email": "adresse_electronique",
    "type_activite": "type_de_mobilite_de_personnel",
    "date_debut": "date_debut_activite_hors_jours_de_voyage",
    "date_fin": "date_fin_activite_hors_jours_de_voyage",
    "pays": "pays_d_accueil",
    "ville": "ville_du_pays_d_accueil",
    "etablissement": "votre_etablissement",  # valeur = ref_etab_DN
    "option_prise_en_charge": "choix_de_la_modalite_de_prise_en_charge_de_la_bourse",
    "assurance_responsable": "partie_responsable_de_la_souscription_de_l_assurance",
    "compagnie_assurance": "compagnie_d_assurance",
    "numero_police_assurance": "numero_et_police_d_assurance",
    "banque_nom": "rib_nom_de_la_banque",
    "banque_titulaire": "rib_titulaire",
    "banque_iban": "rib_iban",
    "banque_bic": "rib_bic",
}

# Tables jointes : une ligne par dossier
JOINTES = {
    TABLE_ANNOTATIONS: {
        "code_projet": "code_projet",
        "duree_voyage": "nombre_de_jours_de_voyage",
        "frais_sejour": "montant_frais_de_sejour",
        "frais_voyage": "montant_frais_de_voyage",
        "montant_bourse": "montant_bourse",
    },
}

# Tables de référence : UNE ligne choisie pour le dossier
#   "lien": (paramètre, "colonne") -> ligne dont la colonne = valeur du paramètre du dossier
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
    "mobilite": "MOBILITÉ DU PERSONNEL",  # en tête de la page de garde
    "limite_prolongation": "89",   # article 3.3 (jours)
    "accompte_pourcentage": "80",  # article 5.1 (%)
}

# Calculés dans apply_data_transformation :
#   participant_nom_complet, participant_premier_prenom, pays_ville, duree,
#   duree_jours_bourse (= jours d'activité + jours de voyage), valeur_bourse / montant_global
#   (= montant_bourse), organisme_envoi_representant_nom_complet, option_prise_en_charge normalisée
# Pas encore dans Grist (-> « [donnée manquante] ») :
#   inclut_dans_contribution


# =====================================================================
# Construction automatique (rien à modifier ici pour le mapping)
# =====================================================================


def build_enum(name: str, principale: dict, jointes: dict, module: str = __name__) -> Enum:
    """Enum attendue par PonyExpress : nom = paramètre Typst, valeur = colonne ou "Table.colonne".
    `module` : module qui déclare l'Enum (check_mapping.py la cherche dans le module de la config)."""
    members = dict(principale)
    for table, columns in jointes.items():
        for param, column in columns.items():
            if param in members:
                raise ValueError(f"Paramètre déclaré deux fois : {param}")
            members[param] = f"{table}.{column}"
    return Enum(name, members, module=module)


def build_reference_tables(references: dict) -> dict:
    """Colonnes attendues dans chaque table de référence (contrôlées par check_mapping.py)."""
    tables = {}
    for table, ref in references.items():
        expected = list(dict.fromkeys(ref["champs"].values()))
        if ref["lien"] and ref["lien"][1] != "id" and ref["lien"][1] not in expected:
            expected.append(ref["lien"][1])
        tables[table] = expected
    return tables


PERSON_DATA = build_enum("PERSON_DATA", PRINCIPALE, JOINTES, module=__name__)
EXTRA_TABLES = build_reference_tables(REFERENCES)


def should_be_exported(record: dict) -> bool:
    """True si la ligne doit produire un PDF (ajouter ici un filtre, ex : statut)."""
    return True


def name_pdf(record) -> str:
    return slugify(f"{record['participant_nom']}_{record['participant_prenom']}_{record['id']}_financier_personnel")


def apply_data_transformation(data: dict) -> dict:
    transformed = deepcopy(data)
    set_date(transformed, "date_debut")
    set_date(transformed, "date_fin")
    set_date(transformed, "participant_date_naissance")
    # champ « adresse » de DN : objet JSON -> libellé lisible
    adresse = adresse_lisible(value(data, "participant_adresse"))
    if adresse:
        transformed["participant_adresse"] = adresse
    set_duree(transformed, "duree", "date_debut", "date_fin")
    set_joined(transformed, "pays_ville", [value(data, "pays"), value(data, "ville")])

    prenoms, nom = value(data, "participant_prenom"), value(data, "participant_nom")
    set_joined(transformed, "participant_nom_complet", [prenoms, nom], " ")
    transformed["participant_premier_prenom"] = premier_prenom(prenoms)

    apply_references(transformed, data)
    set_joined(transformed, "organisme_envoi_representant_nom_complet",
               [transformed.get("envoi_direction_prenom", ""), transformed.get("envoi_direction_nom", "").upper()], " ")

    # jours de bourse = jours d'activité (bornes incluses) + jours de voyage
    try:
        jours = int(transformed["duree"].split()[0]) + int(float(value(data, "duree_voyage") or 0))
        transformed["duree_jours_bourse"] = str(jours)
    except (KeyError, ValueError):
        transformed.pop("duree_jours_bourse", None)

    for key in ("montant_bourse", "frais_sejour", "frais_voyage"):
        set_montant(transformed, key, data)
    if "montant_bourse" in transformed:
        transformed["valeur_bourse"] = transformed["montant_bourse"]
        transformed["montant_global"] = transformed["montant_bourse"]

    # menu à choix simple de DN : libellé affiché en gras + code testé par le template
    #   "Option 1", "Option 2", "Option 3 transport" (transport pris en charge par l'EPL),
    #   "Option 3 sejour" (frais de séjour pris en charge par l'EPL)
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
    transformed["inclut_dans_contribution"] = []  # pas encore dans Grist
    # colonne vide ou absente de Grist : [donnée manquante] plutôt qu'une case blanche
    for param in list(transformed):
        val = transformed[param]
        if param in PERSON_DATA.__members__ and val in ("", None):
            transformed.pop(param)
        elif isinstance(val, str) and val.endswith(" is not in GRIST"):
            transformed.pop(param)
    return transformed


# =====================================================================
# Outils
# =====================================================================


def adresse_lisible(texte: str) -> str:
    """Champ adresse de DN (JSON) -> « 44 Allées Charles de Fitte 31300 Toulouse » ; texte simple inchangé."""
    if not texte.startswith("{"):
        return texte
    try:
        adresse = json.loads(texte)
    except ValueError:
        return texte
    label = (adresse.get("address") or {}).get("label")
    if label:
        return label
    commune = adresse.get("commune") or {}
    return " ".join(x for x in (commune.get("postalCode"), commune.get("name")) if x)


def fetch_table(table: str) -> list[dict]:
    """Lit une table Grist entière (remplacée par check_mapping.py en mode hors-ligne)."""
    return GristService(GRIST_DOC_ID, GRIST_TEAM_SITE, GRIST_SERVER).get_table_records(table)


def premier_prenom(prenoms: str) -> str:
    """"Pauline, Marie, Gilda" -> "Pauline" (premier prénom seulement)."""
    return prenoms.split(",")[0].strip()


def value(row: dict, key: str) -> str:
    """Texte nettoyé ; "" si la colonne est vide ou introuvable."""
    text = clean_text(row.get(key))
    return "" if text.endswith(" is not in GRIST") else text


def set_date(data: dict, key: str) -> None:
    """Date au format jj.mm.aaaa ; si absente ou illisible : [donnée manquante]."""
    try:
        jour = datetime.strptime(get_date_from_timestamp(data[key]), "%d-%m-%y")
        data[key] = jour.strftime("%d.%m.%Y")
    except (KeyError, TypeError, ValueError):
        data.pop(key, None)


def set_duree(data: dict, key: str, debut: str, fin: str) -> None:
    """Durée en jours, bornes incluses (dates déjà passées par set_date) ; sinon [donnée manquante]."""
    try:
        jours = (datetime.strptime(data[fin], "%d.%m.%Y")
                 - datetime.strptime(data[debut], "%d.%m.%Y")).days + 1
    except (KeyError, TypeError, ValueError):
        data.pop(key, None)
        return
    if jours > 0:
        data[key] = f"{jours} jour{'s' if jours > 1 else ''}"
    else:
        data.pop(key, None)


def set_joined(data: dict, key: str, values: list, separator: str = ", ") -> None:
    """Assemble les valeurs renseignées ; si aucune : [donnée manquante]."""
    parts = [part for part in values if part]
    if parts:
        data[key] = separator.join(parts)
    else:
        data.pop(key, None)


def set_montant(data: dict, key: str, source: dict) -> None:
    """1140 -> "1 140" ; 1140.5 -> "1 140,50" ; vide : [donnée manquante]."""
    raw = value(source, key).replace(" ", "").replace(",", ".")
    try:
        montant = float(raw)
    except ValueError:
        data.pop(key, None)
        return
    texte = f"{montant:,.2f}".replace(",", " ").replace(".", ",")
    data[key] = texte[:-3] if texte.endswith(",00") else texte


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
    print("GENERATE CONTRATS FINANCIERS PERSONNEL")
    generate_pdf_from_grist(
        GRIST_DOC_ID,
        GRIST_TEAM_SITE,
        GRIST_TABLE,
        PERSON_DATA,
        TEMPLATE_FOLDERNAME,
        TEMPLATE_FILENAME,
        TEMPLATE_NAME,
        should_be_exported,
        apply_data_transformation,
        name_pdf,
        GRIST_SERVER,
        GRIST_PDF_COLUMN,
    )
