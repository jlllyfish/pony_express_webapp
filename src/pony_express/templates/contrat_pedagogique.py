import os
from copy import deepcopy
from datetime import datetime
from enum import Enum

from slugify import slugify

from pony_express.service.grist import GristService
from pony_express.service.ponyexpress import generate_pdf_from_grist
from pony_express.service.utils import clean_text, get_date_from_timestamp, group_blocks

# Accès au document Grist
GRIST_SERVER = os.environ["GRIST_SERVER"]
GRIST_TEAM_SITE = os.environ["GRIST_TEAM_SITE"]
GRIST_DOC_ID = os.environ["GRIST_DOC_ID"]
GRIST_TABLE = os.environ[
    "GRIST_TABLE"
]  # table principale (ex : Demarche_128447_annotations)
GRIST_PDF_COLUMN = None

# Template Typst
TEMPLATE_NAME = "contrat_pedagogique"
TEMPLATE_FILENAME = "contrat_pedagogique_template"
TEMPLATE_FOLDERNAME = "contrat_pedagogique"

# Tables OTP de la démarche, toutes reliées par le numéro de dossier
DEMARCHE = "128447"
TABLE_CHAMPS = f"Demarche_{DEMARCHE}_champs"
TABLE_ACQUIS = f"Demarche_{DEMARCHE}_repetable_acquis_d_apprentissage"
TABLE_ACTIVITES = f"Demarche_{DEMARCHE}_repetable_activites_et_taches"
TABLE_ACCOMPAGNATEURS = (
    f"Demarche_{DEMARCHE}_repetable_information_personnelle_accompagnateur"
)
TABLE_ETABLISSEMENTS = "Etablissements"
BLOCK_KEY = "dossier_number"  # numéro de dossier dans les tables de blocs
BLOCK_ORDER = "block_row_index"  # ordre des blocs


# =====================================================================
# RUBRIQUES : {paramètre du template Typst : colonne Grist}
# Un paramètre déclaré nulle part s'affiche « [donnée manquante] ».
# =====================================================================

# Table principale (GRIST_TABLE)
PRINCIPALE = {
    "numero_dossier": "dossier_number",  # relie toutes les autres tables
    "code_projet": "code_projet",
    "participant_qualification": "qualification_apprenant",
    "participant_nom": "nom_participant",
    "participant_prenom": "prenom_s_participant",
    "participant_adresse": "adresse_participant",
    "participant_email": "mail_participant",
    "participant_telephone": "telephone_participant",
    "tuteur_1_nom": "nom_parent_tuteur_legal_1",
    "tuteur_1_prenom": "prenom_parent_tuteur_legal_1",
    "tuteur_1_email": "mail_parent_tuteur_legal_1",
    "tuteur_1_telephone": "telephone_parent_tuteur_legal_1",
    "tuteur_2_nom": "nom_parent_tuteur_legal_2",
    "tuteur_2_prenom": "prenom_parent_tuteur_legal_2",
    "tuteur_2_email": "mail_parent_tuteur_legal_2",
    "tuteur_2_telephone": "telephone_parent_tuteur_legal_2",
}

# Tables jointes : une ligne par dossier
JOINTES = {
    TABLE_CHAMPS: {
        "type_activite": "mobilite_apprenant",
        "date_debut": "date_debut_activite_hors_jours_de_voyage",
        "date_fin": "date_fin_activite_hors_jours_de_voyage",
        "pays": "pays_d_accueil",
        "ville": "ville_pays_d_accueil",
        "evaluation_format": "format_et_procedures_d_evaluation",
        "evaluation_criteres": "criteres_d_evaluation",
        "reconnaissance": "reconnaisance_des_acquis_d_apprentissage",
        "retour_lieu": "lieu_du_retour",
        "retour_conditions": "condition_du_retour",
        "etablissement": "votre_etablissement",  # valeur = ref_etab_DN
        "organisation_accueil_nom": "nom_de_l_organisme_d_accueil",
        "organisation_accueil_adresse": "adresse_organisme_d_accueil",
        "organisation_accueil_email": "mail_organisme_d_accueil",
        "organisation_accueil_telephone": "telephone_organisme_d_accueil",
        "tuteur_nom": "nom_tuteur",
        "tuteur_prenom": "prenom_tuteur",
        "tuteur_email": "mail_tuteur",
        "tuteur_telephone": "numero_de_telephone_tuteur",
        "contact_admin_identique": "le_contact_administratif_est_le_meme_que_tuteur",
        "contact_admin_nom": "nom_contact_administratif",
        "contact_admin_prenom": "prenom_contact_administratif",
        "contact_admin_fonction": "fonction_contact_administratif",
        "contact_admin_email": "mail_contact_administratif",
        "contact_admin_telephone": "telephone_contact_administratif",
        # organisme d'accueil : responsable, puis contact / tuteur / contact d'urgence
        "accueil_resp_nom": "nom_responsable_organisme_d_accueil",
        "accueil_resp_prenom": "prenom_responsable_organisme_d_accueil",
        "accueil_resp_email": "mail_responsable_organisme_d_accueil",
        "accueil_resp_telephone": "telephone_responsable_organisme_d_accueil",
        "accueil_resp_est_contact": "la_personne_responsable_de_l_organisme_d_accueil_est_egalement_la_personne_de_contact",
        "accueil_resp_est_tuteur": "la_personne_responsable_de_l_organisme_d_accueil_est_egalement_le_tuteur",
        "accueil_resp_est_urgence": "la_personne_responsable_de_l_organisme_d_accueil_est_egalement_le_contact_d_urgence",
        "accueil_contact_est_tuteur": "la_personne_de_contact_de_l_organisme_d_accueil_est_egalement_le_tuteur",
        "accueil_contact_est_urgence": "la_personne_de_contact_de_l_organisme_d_accueil_est_egalement_le_contact_d_urgence",
        "accueil_tuteur_est_urgence": "le_tuteur_de_l_organisme_d_accueil_est_egalement_le_contact_d_urgence",
        "accueil_contact_nom": "nom",
        "accueil_contact_prenom": "prenom",
        "accueil_contact_email": "mail",
        "accueil_contact_telephone": "telephone",
        "accueil_tuteur_nom": "nom_1",
        "accueil_tuteur_prenom": "prenom_1",
        "accueil_tuteur_email": "mail_1",
        "accueil_tuteur_telephone": "numero_de_telephone",
        "accueil_urgence_nom": "nom_2",
        "accueil_urgence_prenom": "prenom_2",
        "accueil_urgence_email": "mail_2",
        "accueil_urgence_telephone": "numero_de_telephone_1",
        # Fonction (pas encore dans DN/Grist -> « [donnée manquante] ») : à ajouter ici
        # "accueil_resp_fonction", "accueil_contact_fonction",
        # "accueil_tuteur_fonction", "accueil_urgence_fonction"
    },
}

# Blocs répétables : plusieurs lignes par dossier
#   paramètre: (table, "colonne")              -> liste de textes
#   paramètre: (table, {champ: "colonne"})     -> liste de fiches
BLOCS = {
    "acquis_list": (TABLE_ACQUIS, "acquis"),
    "activites": (TABLE_ACTIVITES, "activite"),
    "tutorings": (TABLE_ACTIVITES, "tutorat_et_suivi_de_cette_activite"),
    "accompagnants": (
        TABLE_ACCOMPAGNATEURS,
        {
            "nom": "nom",
            "prenom": "prenom",
            "email": "adresse_electronique",
            "telephone": "numero_de_telephone",
            "fonction": "intitule_du_poste",
        },
    ),
}

# Tables de reference : UNE ligne choisie pour le dossier
#   "lien": None                      -> la table ne doit contenir qu'une seule ligne
#   "lien": (parametre, "colonne")    -> ligne dont la colonne = valeur du parametre du dossier
#                                       (parametre declare dans PRINCIPALE ou JOINTES ; "id" pour une colonne Reference)
REFERENCES = {
    TABLE_ETABLISSEMENTS: {
        "lien": ("etablissement", "ref_etab_DN"),
        "champs": {
            "organisation_envoi_nom": "Nom_etablissement",
            "organisation_envoi_adresse": "Adresse",
            "organisation_envoi_email": "Mail",
            "organisation_envoi_telephone": "Telephone",
            "envoi_direction_nom": "Nom_direction",
            "envoi_direction_prenom": "Prenom_direction",
        },
    },
}

# Valeurs identiques pour tous les dossiers (remplacer par un texte fixe si besoin)
CONSTANTES = {
    "format_mobilite": "Activité de mobilité physique",
}

# Section 8.1 : une fiche par personne distincte de l'organisme d'accueil
#   (titre affiche, case "c'est la meme personne", prefixe des parametres)
RESPONSABLES_ACCUEIL = [
    ("Responsable", (), "accueil_resp"),
    ("Contact", ("accueil_resp_est_contact",), "accueil_contact"),
    ("Tuteur", ("accueil_resp_est_tuteur", "accueil_contact_est_tuteur"), "accueil_tuteur"),
    ("Contact d'urgence", ("accueil_resp_est_urgence", "accueil_contact_est_urgence",
                           "accueil_tuteur_est_urgence"), "accueil_urgence"),
]

# Tuteurs légaux : une fiche par tuteur dont le nom est renseigné
TUTEURS = [
    {
        "nom": "tuteur_1_nom",
        "prenom": "tuteur_1_prenom",
        "email": "tuteur_1_email",
        "telephone": "tuteur_1_telephone",
    },
    {
        "nom": "tuteur_2_nom",
        "prenom": "tuteur_2_prenom",
        "email": "tuteur_2_email",
        "telephone": "tuteur_2_telephone",
    },
]

# Calculés dans apply_data_transformation : pays_ville, tuteurs_legaux,
#   participant_premier_prenom, responsables_envoi, responsables_accueil


# =====================================================================
# Construction automatique (rien à modifier ici pour le mapping)
# =====================================================================


def build_enum(name: str, principale: dict, jointes: dict) -> Enum:
    """Enum attendue par PonyExpress : nom = paramètre Typst, valeur = colonne ou "Table.colonne"."""
    members = dict(principale)
    for table, columns in jointes.items():
        for param, column in columns.items():
            if param in members:
                raise ValueError(f"Paramètre déclaré deux fois : {param}")
            members[param] = f"{table}.{column}"
    return Enum(name, members, module=__name__)


def build_extra_tables(blocs: dict) -> dict:
    """Colonnes attendues dans chaque table de blocs (contrôlées par check_mapping.py)."""
    tables = {}
    for table, columns in blocs.values():
        expected = tables.setdefault(table, [BLOCK_KEY, BLOCK_ORDER])
        for column in [columns] if isinstance(columns, str) else columns.values():
            if column not in expected:
                expected.append(column)
    return tables


def build_reference_tables(references: dict) -> dict:
    """Colonnes attendues dans chaque table de reference (controlees par check_mapping.py)."""
    tables = {}
    for table, ref in references.items():
        expected = list(dict.fromkeys(ref["champs"].values()))
        if ref["lien"] and ref["lien"][1] != "id" and ref["lien"][1] not in expected:
            expected.append(ref["lien"][1])
        tables[table] = expected
    return tables


STUDENT_DATA = build_enum("STUDENT_DATA", PRINCIPALE, JOINTES)
EXTRA_TABLES = build_extra_tables(BLOCS)
EXTRA_TABLES.update(build_reference_tables(REFERENCES))


def should_be_exported(record: dict) -> bool:
    """True si la ligne doit produire un PDF (ajouter ici un filtre, ex : statut)."""
    return True


def name_pdf(record) -> str:
    return slugify(
        f"{record['participant_nom']}_{record['participant_prenom']}_{record['id']}_pedagogique"
    )


def apply_data_transformation(data: dict) -> dict:
    transformed = deepcopy(data)
    set_date(transformed, "date_debut")
    set_date(transformed, "date_fin")
    set_duree(transformed, "duree", "date_debut", "date_fin")
    set_joined(transformed, "pays_ville", [value(data, "pays"), value(data, "ville")])
    # une puce par ligne saisie dans DN
    for key in ("evaluation_format", "evaluation_criteres"):
        set_list(transformed, key, value(data, key).split("\n"))
    set_people(
        transformed, "tuteurs_legaux", [data] * len(TUTEURS), TUTEURS, required="nom"
    )
    transformed.setdefault(
        "tuteurs_legaux", []
    )  # aucun tuteur (majeur) : pas de rubrique

    apply_references(transformed, data)
    dossier = data.get("numero_dossier")
    for param, (table, columns) in BLOCS.items():
        blocks = get_blocks(table, dossier)
        if isinstance(columns, str):
            set_list(transformed, param, [block.get(columns) for block in blocks])
        else:
            set_people(transformed, param, blocks, columns)
    transformed.update(CONSTANTES)
    responsables = get_responsables_envoi(data)
    if responsables:
        transformed["responsables_envoi"] = responsables
    else:
        transformed.pop("responsables_envoi", None)
    accueil = get_responsables_accueil(data)
    if accueil:
        transformed["responsables_accueil"] = accueil
    else:
        transformed.pop("responsables_accueil", None)
    # signatures : direction de l'etablissement et responsable de l'organisme d'accueil
    transformed["signature_envoi_nom"] = transformed.get("envoi_direction_nom", "")
    transformed["signature_envoi_prenom"] = transformed.get("envoi_direction_prenom", "")
    transformed["signature_accueil_nom"] = value(data, "accueil_resp_nom")
    transformed["signature_accueil_prenom"] = value(data, "accueil_resp_prenom")
    transformed["participant_premier_prenom"] = premier_prenom(value(data, "participant_prenom"))
    transformed["signature_participant_prenom"] = transformed["participant_premier_prenom"]
    # colonne vide dans Grist : [donnee manquante] plutot qu'une case blanche
    for param in list(transformed):
        if param in STUDENT_DATA.__members__ and transformed[param] in ("", None):
            transformed.pop(param)
    return transformed


# =====================================================================
# Outils
# =====================================================================

_blocks_cache: dict[str, dict] = {}


def fetch_table(table: str) -> list[dict]:
    """Lit une table Grist entière (remplacée par check_mapping.py en mode hors-ligne)."""
    return GristService(GRIST_DOC_ID, GRIST_TEAM_SITE, GRIST_SERVER).get_table_records(
        table
    )


def get_blocks(table: str, dossier_number) -> list[dict]:
    """Blocs répétables d'un dossier, dans l'ordre. Chaque table n'est lue qu'une fois."""
    if table not in _blocks_cache:
        _blocks_cache[table] = group_blocks(fetch_table(table), BLOCK_KEY, BLOCK_ORDER)
    try:
        return _blocks_cache[table].get(int(dossier_number), [])
    except (TypeError, ValueError):
        return []


def premier_prenom(prenoms: str) -> str:
    """"Pauline, Marie, Gilda" -> "Pauline" (premier prenom seulement)."""
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
    """Assemble les valeurs renseignées ("Espagne, Madrid") ; si aucune : [donnée manquante]."""
    parts = [part for part in values if part]
    if parts:
        data[key] = separator.join(parts)
    else:
        data.pop(key, None)


def set_list(data: dict, key: str, values: list) -> None:
    """Liste de textes non vides ; si elle est vide : [donnée manquante]."""
    values = [clean_text(v) for v in values if clean_text(v)]
    if values:
        data[key] = values
    else:
        data.pop(key, None)


def set_people(
    data: dict, key: str, rows: list[dict], columns, required: str | None = None
) -> None:
    """
    Une fiche par ligne : {champ du template : colonne}.
    `columns` : un dictionnaire commun à toutes les lignes, ou une liste (un par ligne).
    Fiche ignorée si elle est vide (ou si le champ `required` est vide). Aucune fiche : [donnée manquante].
    """
    mappings = columns if isinstance(columns, list) else [columns] * len(rows)
    people = [
        {field: value(row, column) for field, column in mapping.items()}
        for row, mapping in zip(rows, mappings)
    ]
    people = [p for p in people if (p[required] if required else any(p.values()))]
    if people:
        data[key] = people
    else:
        data.pop(key, None)


_reference_cache: dict[str, list[dict]] = {}


def get_reference(table: str, lien, data: dict) -> dict | None:
    """Ligne de la table de reference correspondant au dossier (None si aucune ou ambigue)."""
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
    """Remplit les champs des tables de reference ; sans correspondance : [donnee manquante]."""
    for table, ref in REFERENCES.items():
        row = get_reference(table, ref["lien"], data) or {}
        for param, column in ref["champs"].items():
            text = value(row, column)
            if text:
                transformed[param] = text
            else:
                transformed.pop(param, None)


def is_true(row: dict, key: str) -> bool:
    """Case a cocher Grist : True, "true", "oui", 1..."""
    raw = row.get(key)
    if isinstance(raw, bool):
        return raw
    return value(row, key).lower() in ("true", "vrai", "oui", "yes", "1")


def get_responsables_envoi(data: dict) -> list[dict]:
    """Tuteur, plus le contact administratif quand ce n'est pas la meme personne."""
    people = [{
        "nom": value(data, "tuteur_nom"),
        "prenom": value(data, "tuteur_prenom"),
        "email": value(data, "tuteur_email"),
        "telephone": value(data, "tuteur_telephone"),
        "responsabilites": "Tuteur",
    }]
    if not is_true(data, "contact_admin_identique"):
        people.append({
            "nom": value(data, "contact_admin_nom"),
            "prenom": value(data, "contact_admin_prenom"),
            "email": value(data, "contact_admin_email"),
            "telephone": value(data, "contact_admin_telephone"),
            "responsabilites": "Contact administratif",
        })
    return [person for person in people if person["nom"]]


def get_responsables_accueil(data: dict) -> list[dict]:
    """Une fiche par personne : le responsable, puis celles qui sont d'autres personnes."""
    people = []
    for role, memes, prefixe in RESPONSABLES_ACCUEIL:
        if any(is_true(data, drapeau) for drapeau in memes):
            continue
        person = {
            "nom": value(data, prefixe + "_nom").upper(),
            "prenom": value(data, prefixe + "_prenom"),
            "email": value(data, prefixe + "_email"),
            "telephone": value(data, prefixe + "_telephone"),
            "responsabilites": role,
        }
        fonction = value(data, prefixe + "_fonction")
        if fonction:  # sinon « [donnée manquante] »
            person["fonction"] = fonction
        if person["nom"]:
            people.append(person)
    return people


if __name__ == "__main__":
    print("GENERATE CONTRATS PEDAGOGIQUES")
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
