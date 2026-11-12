import json
import os
from copy import deepcopy
from datetime import datetime
from enum import Enum

from slugify import slugify

from pony_express.service.grist import GristService
from pony_express.service.ponyexpress import generate_pdf_from_grist
from pony_express.service.utils import clean_text, get_date_from_timestamp, group_blocks

# Accès au document Grist (même document que les mobilités apprenants)
GRIST_SERVER = os.environ["GRIST_SERVER"]
GRIST_TEAM_SITE = os.environ["GRIST_TEAM_SITE"]
GRIST_DOC_ID = os.environ["GRIST_DOC_ID"]
GRIST_PDF_COLUMN = None

# Template Typst
TEMPLATE_NAME = "contrat_pedagogique_personnel"
TEMPLATE_FILENAME = "contrat_pedagogique_personnel_template"
TEMPLATE_FOLDERNAME = "contrat_pedagogique_personnel"

# Tables OTP de la démarche « mobilité du personnel », toutes reliées par le numéro de dossier
DEMARCHE = "156966"
GRIST_TABLE = os.environ.get("GRIST_TABLE_PERSONNEL", f"Demarche_{DEMARCHE}_champs")  # table principale
TABLE_ANNOTATIONS = f"Demarche_{DEMARCHE}_annotations"
TABLE_ACQUIS = f"Demarche_{DEMARCHE}_repetable_acquis_d_apprentissage"
TABLE_ACTIVITES = f"Demarche_{DEMARCHE}_repetable_activites_et_taches"
TABLE_JOURS = f"Demarche_{DEMARCHE}_repetable_jour_d_activite"
TABLE_ETABLISSEMENTS = "Etablissements"
BLOCK_KEY = "dossier_number"  # numéro de dossier dans les tables de blocs
BLOCK_ORDER = "block_row_index"  # ordre des blocs


# =====================================================================
# RUBRIQUES : {paramètre du template Typst : colonne Grist}
# Un paramètre déclaré nulle part s'affiche « [donnée manquante] ».
# =====================================================================

# Table principale (GRIST_TABLE = table champs : une ligne par dossier)
PRINCIPALE = {
    "numero_dossier": "dossier_number",  # relie toutes les autres tables
    "type_activite": "type_de_mobilite_de_personnel",  # traduit par le dictionnaire
    "participant_nom": "nom",
    "participant_prenom": "prenom",
    "participant_qualification": "statut_du_participant",
    "participant_adresse": "adresse_du_participant",
    "participant_email": "adresse_electronique",
    "participant_telephone": "numero_de_telephone",
    "date_debut": "date_debut_activite_hors_jours_de_voyage",
    "date_fin": "date_fin_activite_hors_jours_de_voyage",
    # accompagnement d'apprenants (type de mobilité « Accompagnateur »)
    "accomp_debut": "date_de_debut_de_l_accompagnement",
    "accomp_fin": "date_de_fin_de_l_accompagnement",
    "accomp_nb_apprenants": "nombre_d_apprenants_a_accompagner",
    "accomp_apprenants_debut": "date_de_debut_d_activite_des_apprenants",
    "accomp_apprenants_fin": "date_de_fin_d_activite_des_apprenants",
    "pays": "pays_d_accueil",
    "ville": "ville_du_pays_d_accueil",
    "evaluation_format": "format_et_procedures_d_evaluation",
    "evaluation_criteres": "criteres_d_evaluation",
    "reconnaissance": "reconnaisance_des_acquis_d_apprentissage",
    "retour_lieu": "lieu_du_retour",
    "retour_conditions": "condition_du_retour",
    "etablissement": "votre_etablissement",  # valeur = ref_etab_DN
    # organisme d'envoi : contact administratif, tuteur, contact d'urgence
    "contact_admin_nom": "nom_contact_administratif",
    "contact_admin_prenom": "prenom_contact_administratif",
    "contact_admin_fonction": "fonction_contact_administratif",
    "contact_admin_email": "mail_contact_administratif",
    "contact_admin_telephone": "numero_de_telephone_contact_administratif",
    "tuteur_nom": "nom_tuteur",
    "urgence_identique": "le_contact_d_urgence_est_le_meme_que_le_contact_administratif",
    "urgence_nom": "nom_contact_d_urgence",
    "urgence_prenom": "prenom_contact_d_urgence",
    "urgence_fonction": "fonction_contact_d_urgence",
    "urgence_email": "mail_contact_d_urgence",
    "urgence_telephone": "numero_de_telephone_contact_d_urgence",
    # organisme d'accueil
    "organisation_accueil_nom": "nom_de_l_organisme_d_accueil",
    "organisation_accueil_adresse": "adresse_organisme_d_accueil",
    "organisation_accueil_email": "mail_organisme_d_accueil",
    "organisation_accueil_telephone": "numero_de_telephone_organisme_d_accueil",
    # organisme d'accueil : responsable, puis contact administratif / tuteur / contact d'urgence
    "accueil_resp_nom": "nom_responsable_organisme_d_accueil",
    "accueil_resp_prenom": "prenom_responsable_organisme_d_accueil",
    "accueil_resp_fonction": "fonction_responsable_organisme_d_accueil",
    "accueil_resp_email": "mail_responsable_organisme_d_accueil",
    "accueil_resp_telephone": "numero_de_telephone_responsable_organisme_d_accueil",
    "accueil_resp_est_contact": "la_personne_responsable_de_l_organisme_d_accueil_est_egalement_la_personne_contact_administratif",
    "accueil_resp_est_tuteur": "la_personne_responsable_de_l_organisme_d_accueil_est_egalement_le_tuteur",
    "accueil_resp_est_urgence": "la_personne_responsable_de_l_organisme_d_accueil_est_egalement_le_contact_d_urgence",
    "accueil_contact_est_tuteur": "la_personne_contact_administratif_de_l_organisme_d_accueil_est_egalement_le_tuteur",
    "accueil_contact_est_urgence": "la_personne_contact_administratif_de_l_organisme_d_accueil_est_egalement_le_contact_d_urgence",
    "accueil_tuteur_est_urgence": "le_tuteur_de_l_organisme_d_accueil_est_egalement_le_contact_d_urgence",
    "accueil_contact_nom": "nom_contact_administratif_1",
    "accueil_contact_prenom": "prenom_contact_administratif_1",
    "accueil_contact_fonction": "fonction_contact_administratif_1",
    "accueil_contact_email": "mail_contact_administratif_1",
    "accueil_contact_telephone": "telephone_contact_administratif",
    "accueil_tuteur_nom": "nom_tuteur_1",
    "accueil_tuteur_prenom": "prenom_tuteur",
    "accueil_tuteur_email": "mail_tuteur",
    "accueil_tuteur_telephone": "telephone_tuteur",
    "accueil_urgence_nom": "nom_contact_d_urgence_1",
    "accueil_urgence_prenom": "prenom_contact_d_urgence_1",
    "accueil_urgence_email": "mail_contact_d_urgence_1",
    "accueil_urgence_telephone": "numero_de_telephone_contact_d_urgence_1",
}

# Tables jointes : une ligne par dossier
JOINTES = {
    TABLE_ANNOTATIONS: {
        "code_projet": "code_projet",
    },
}

# Blocs répétables : plusieurs lignes par dossier
#   paramètre: (table, "colonne")              -> liste de textes
#   paramètre: (table, {champ: "colonne"})     -> liste de fiches
BLOCS = {
    "acquis_list": (TABLE_ACQUIS, "acquis"),
    "activites": (TABLE_ACTIVITES, "activite"),
    "tutorings": (TABLE_ACTIVITES, "tutorat_et_suivi_de_cette_activite"),
}

# Planning des activités : une ligne par jour (Jour 1, 2… dans l'ordre des blocs)
PLANNING = (TABLE_JOURS, {"matin": "matin", "apres_midi": "apres_midi"})

# Tables de reference : UNE ligne choisie pour le dossier
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

# Organisme d'accueil : une fiche par personne distincte
#   (titre affiche, case "c'est la meme personne", prefixe des parametres)
RESPONSABLES_ACCUEIL = [
    ("Responsable", (), "accueil_resp"),
    ("Contact administratif", ("accueil_resp_est_contact",), "accueil_contact"),
    ("Tuteur", ("accueil_resp_est_tuteur", "accueil_contact_est_tuteur"), "accueil_tuteur"),
    ("Contact d'urgence", ("accueil_resp_est_urgence", "accueil_contact_est_urgence",
                           "accueil_tuteur_est_urgence"), "accueil_urgence"),
]

# Calculés dans apply_data_transformation : pays_ville, duree, participant_premier_prenom,
#   planning, responsables_envoi, responsables_accueil, signatures


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
EXTRA_TABLES = build_extra_tables(BLOCS | {"planning": PLANNING})
EXTRA_TABLES.update(build_reference_tables(REFERENCES))


def should_be_exported(record: dict) -> bool:
    """True si la ligne doit produire un PDF (ajouter ici un filtre, ex : statut)."""
    return True


def name_pdf(record) -> str:
    return slugify(
        f"{record['participant_nom']}_{record['participant_prenom']}_{record['id']}_pedagogique_personnel"
    )


def apply_data_transformation(data: dict) -> dict:
    transformed = deepcopy(data)
    set_date(transformed, "date_debut")
    set_date(transformed, "date_fin")
    set_duree(transformed, "duree", "date_debut", "date_fin")
    # rubrique « Accompagnement d'apprenants » seulement pour un accompagnateur
    if value(data, "type_activite").casefold().startswith("accompagnat"):
        for key in ("accomp_debut", "accomp_fin", "accomp_apprenants_debut", "accomp_apprenants_fin"):
            set_date(transformed, key)
        transformed["accompagnement"] = {
            "nb": value(data, "accomp_nb_apprenants") or "[donnée manquante]",
            "periode": periode(transformed, "accomp_debut", "accomp_fin"),
            "periode_apprenants": periode(transformed, "accomp_apprenants_debut", "accomp_apprenants_fin"),
        }
    # champ « adresse » de DN : objet JSON -> libellé lisible
    adresse = adresse_lisible(value(data, "participant_adresse"))
    if adresse:
        transformed["participant_adresse"] = adresse
    set_joined(transformed, "pays_ville", [value(data, "pays"), value(data, "ville")])
    # une puce par ligne saisie dans DN
    for key in ("evaluation_format", "evaluation_criteres"):
        set_list(transformed, key, value(data, key).split("\n"))

    apply_references(transformed, data)
    dossier = data.get("numero_dossier")
    for param, (table, columns) in BLOCS.items():
        blocks = get_blocks(table, dossier)
        if isinstance(columns, str):
            set_list(transformed, param, [block.get(columns) for block in blocks])
        else:
            set_people(transformed, param, blocks, columns)
    # planning : (Jour n, matin, après-midi)
    table, colonnes = PLANNING
    jours = get_blocks(table, dossier)
    planning = [(f"Jour {i}", value(j, colonnes["matin"]), value(j, colonnes["apres_midi"]))
                for i, j in enumerate(jours, start=1)]
    if planning:
        transformed["planning"] = planning
    else:
        transformed.pop("planning", None)
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


def periode(data: dict, debut: str, fin: str) -> str:
    """« du 19.10.2026 au 23.10.2026 » (dates déjà passées par set_date) ; manquante si une date l'est."""
    if debut in data and fin in data:
        return f"du {data[debut]} au {data[fin]}"
    return "[donnée manquante]"


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


def get_responsables_envoi(data: dict) -> list[dict]:
    """Contact administratif, tuteur, puis contact d'urgence s'il est une autre personne."""
    people = [{
        "nom": value(data, "contact_admin_nom").upper(),
        "prenom": value(data, "contact_admin_prenom"),
        "fonction": value(data, "contact_admin_fonction"),
        "email": value(data, "contact_admin_email"),
        "telephone": value(data, "contact_admin_telephone"),
        "responsabilites": "Contact administratif",
    }, {
        # DN ne demande que le nom du tuteur
        "nom": value(data, "tuteur_nom"),
        "responsabilites": "Tuteur",
    }]
    if not is_true(data, "urgence_identique"):
        people.append({
            "nom": value(data, "urgence_nom").upper(),
            "prenom": value(data, "urgence_prenom"),
            "fonction": value(data, "urgence_fonction"),
            "email": value(data, "urgence_email"),
            "telephone": value(data, "urgence_telephone"),
            "responsabilites": "Contact d'urgence",
        })
    return [{k: v for k, v in p.items() if v} for p in people if p["nom"]]


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
