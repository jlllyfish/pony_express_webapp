"""Contrat pédagogique Europass pour les activités de groupe (démarche DN 156967)."""
import os
import re
from copy import deepcopy

from slugify import slugify

from pony_express.service.grist import GristService
from pony_express.service.ponyexpress import generate_pdf_from_grist
from pony_express.service.utils import clean_text, group_blocks

# outils communs (sans effet de bord sur les tables de ce module)
from pony_express.templates.contrat_financier import (
    build_enum, build_reference_tables, set_date, set_duree, set_joined, value,
)

# Accès au document Grist (même document que les mobilités individuelles)
GRIST_SERVER = os.environ["GRIST_SERVER"]
GRIST_TEAM_SITE = os.environ["GRIST_TEAM_SITE"]
GRIST_DOC_ID = os.environ["GRIST_DOC_ID"]
GRIST_PDF_COLUMN = None

# Tables OTP de la démarche de groupe, reliées par le numéro de dossier
DEMARCHE = "156967"
GRIST_TABLE = os.environ.get("GRIST_TABLE_GROUPE", f"Demarche_{DEMARCHE}_champs")  # table principale
TABLE_ANNOTATIONS = f"Demarche_{DEMARCHE}_annotations"
TABLE_ACTIVITES = f"Demarche_{DEMARCHE}_repetable_description_des_activites_et_des_acquis_d_apprentissage"
TABLE_JOURS = f"Demarche_{DEMARCHE}_repetable_jour_d_activite"
TABLE_ACCOMPAGNATEURS = f"Demarche_{DEMARCHE}_repetable_autre_s_accompagnateur_s"
TABLE_ETABLISSEMENTS = "Etablissements"
BLOCK_KEY = "dossier_number"
BLOCK_ORDER = "block_row_index"

# Template Typst
TEMPLATE_NAME = "contrat_pedagogique_groupe"
TEMPLATE_FILENAME = "contrat_pedagogique_groupe_template"
TEMPLATE_FOLDERNAME = "contrat_pedagogique_groupe"


# =====================================================================
# RUBRIQUES : {paramètre du template Typst : colonne Grist}
# Un paramètre déclaré nulle part s'affiche « [donnée manquante] ».
# =====================================================================

# Table principale (GRIST_TABLE = table champs : une ligne par dossier)
PRINCIPALE = {
    "numero_dossier": "dossier_number",
    "etablissement": "votre_etablissement",  # valeur = ref_etab_DN
    # accompagnateur référent
    "ref_nom": "nom_accompagnateur_referent",
    "ref_prenom": "prenom_accompagnateur_referent",
    "ref_email": "mail_accompagnateur_referent",
    "ref_telephone": "telephone_accompagnateur_referent",
    "ref_fonction": "intitule_du_poste_accompagnateur_referent",
    # profil du groupe
    "nb_apprenants": "nombre_d_apprenants_total",
    "nb_filles": "nombre_de_filles",
    "age_moyen": "age_moyen_des_apprenants",
    "profil_texte": "profil_des_participants",
    # un participant par ligne, dans chaque établissement
    "participants_envoi": "liste_des_participants_de_l_etablissement_d_envoi",
    "participants_accueil": "liste_des_participants_de_l_etablissement_d_accueil",
    "date_debut": "date_debut_activite_hors_jours_de_voyage",
    "date_fin": "date_fin_activite_hors_jours_de_voyage",
    "pays": "pays_d_accueil_nom",
    "pays_libelle": "pays_d_accueil",  # « Italie (IT) »
    "ville": "ville_pays_d_accueil",
    # autre personne de contact de l'organisme d'envoi
    "contact_envoi_nom": "nom",
    "contact_envoi_prenom": "prenom",
    "contact_envoi_fonction": "intitule_du_poste",
    "contact_envoi_email": "mail",
    "contact_envoi_telephone": "numero_de_telephone",
    # organisme d'accueil et son responsable
    "organisation_accueil_nom": "nom_de_l_organisme_d_accueil",
    "accueil_resp_nom": "nom_responsable_organisme_d_accueil",
    "accueil_resp_prenom": "prenom_responsable_organisme_d_accueil",
    "accueil_resp_fonction": "intitule_du_poste_1",
    "accueil_resp_email": "mail_responsable_organisme_d_accueil",
    "accueil_resp_telephone": "telephone_responsable_organisme_d_accueil",
}

# Tables jointes : une ligne par dossier
JOINTES = {
    TABLE_ANNOTATIONS: {
        "code_projet": "code_projet",
    },
}

# Table de blocs répétables : une ligne par activité
BLOCS = {
    "activites": (TABLE_ACTIVITES, {"titre": "titre_de_l_activite", "activite": "activite", "acquis": "acquis"}),
    # calendrier : une ligne par jour d'activité (Jour 1, 2… dans l'ordre des blocs)
    "calendrier": (TABLE_JOURS, {"matin": "matin", "apres_midi": "apres_midi"}),
    # autres accompagnateurs (après le référent)
    "accompagnants": (TABLE_ACCOMPAGNATEURS, {
        "nom": "nom", "prenom": "prenom", "fonction": "intitule_du_poste",
        "email": "adresse_electronique", "telephone": "numero_de_telephone",
    }),
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

# Valeurs identiques pour tous les dossiers
CONSTANTES = {
    "secteur": "Enseignement et formation professionnels",
    "format_mobilite": "Activité de mobilité physique",
    "signature_envoi_fonction": "Directeur·rice",
}

# Calculés dans apply_data_transformation :
#   titre_activite (pas de colonne : « Mobilité de groupe – ville (pays) »), pays_ville, duree,
#   envoi_pays_ville (ville tirée de l'adresse de l'établissement), accueil_pays_ville,
#   profil_participants, participants, calendrier, accompagnants, contacts_envoi, contacts_accueil,
#   activites, signatures


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
    return slugify(f"groupe_{record.get('numero_dossier', record['id'])}_{record.get('ville', '')}_pedagogique")


def apply_data_transformation(data: dict) -> dict:
    transformed = deepcopy(data)
    set_date(transformed, "date_debut")
    set_date(transformed, "date_fin")
    set_duree(transformed, "duree", "date_debut", "date_fin")
    pays, ville = value(data, "pays"), value(data, "ville")
    set_joined(transformed, "pays_ville", [value(data, "pays_libelle") or pays, ville])
    set_joined(transformed, "accueil_pays_ville", [pays, ville])
    set_joined(transformed, "titre_activite", [f"Mobilité de groupe – {ville}" if ville else "", f"({pays})" if pays else ""], " ")

    apply_references(transformed, data)
    ville_envoi = ville_depuis_adresse(transformed.get("organisation_envoi_adresse", ""))
    set_joined(transformed, "envoi_pays_ville", ["France", ville_envoi])

    # profil : chiffres clés puis texte libre (un paragraphe par ligne)
    chiffres = []
    if value(data, "nb_apprenants"):
        filles = value(data, "nb_filles")
        chiffres.append(f"{value(data, 'nb_apprenants')} apprenants" + (f" dont {filles} filles" if filles else ""))
    if value(data, "age_moyen"):
        chiffres.append(f"âge moyen : {value(data, 'age_moyen')} ans")
    profil = ([" · ".join(chiffres)] if chiffres else []) + lignes(value(data, "profil_texte"))
    set_or_drop(transformed, "profil_participants", profil)

    envoi = transformed.get("organisation_envoi_nom", "")
    accueil = transformed.get("organisation_accueil_nom", "")
    set_or_drop(transformed, "participants",
                [(nom, envoi) for nom in lignes(value(data, "participants_envoi"))]
                + [(nom, accueil) for nom in lignes(value(data, "participants_accueil"))])
    jours = get_blocks(TABLE_JOURS, data.get("numero_dossier"))
    set_or_drop(transformed, "calendrier", [
        (f"Jour {i}", " ".join(lignes(clean_text(j.get("matin")))), " ".join(lignes(clean_text(j.get("apres_midi")))))
        for i, j in enumerate(jours, start=1)])

    # accompagnateur référent, puis les autres (répétable)
    _, colonnes = BLOCS["accompagnants"]
    autres = [{champ: value(b, col) for champ, col in colonnes.items()}
              for b in get_blocks(TABLE_ACCOMPAGNATEURS, data.get("numero_dossier"))]
    autres = [{k: v for k, v in p.items() if v} for p in autres if value(p, "nom")]
    set_or_drop(transformed, "accompagnants", personnes(data, "ref") + autres)
    set_or_drop(transformed, "contacts_envoi", personnes(data, "contact_envoi"), vide=[])
    set_or_drop(transformed, "contacts_accueil", personnes(data, "accueil_resp"))

    blocks = get_blocks(TABLE_ACTIVITES, data.get("numero_dossier"))
    set_or_drop(transformed, "activites", [activite(b) for b in blocks if clean_text(b.get("activite"))])

    transformed.update(CONSTANTES)
    transformed["signature_envoi_nom"] = transformed.get("envoi_direction_nom", "")
    transformed["signature_envoi_prenom"] = transformed.get("envoi_direction_prenom", "")
    transformed["signature_accueil_nom"] = value(data, "accueil_resp_nom")
    transformed["signature_accueil_prenom"] = value(data, "accueil_resp_prenom")
    if value(data, "accueil_resp_fonction"):
        transformed["signature_accueil_fonction"] = value(data, "accueil_resp_fonction")

    # colonne vide ou absente de Grist : [donnée manquante] plutôt qu'une case blanche
    for param in list(transformed):
        val = transformed[param]
        if val in ("", None) and (param in STUDENT_DATA.__members__ or param.startswith("signature_")):
            transformed.pop(param)
        elif isinstance(val, str) and val.endswith(" is not in GRIST"):
            transformed.pop(param)
    return transformed


# =====================================================================
# Outils
# =====================================================================


def lignes(texte: str) -> list[str]:
    """Texte multiligne -> lignes non vides, nettoyées."""
    return [l.strip() for l in texte.split("\n") if l.strip()]


def activite(block: dict) -> dict:
    """
    Bloc répétable -> {titre, methodes, acquis}.
    titre : colonne titre_de_l_activite. activite : texte coupé à la saisie, recollé en un paragraphe.
    acquis : une puce par élément séparé par « ; ».
    """
    titre = " ".join(lignes(clean_text(block.get("titre_de_l_activite"))))
    methodes = lignes(clean_text(block.get("activite")))
    acquis = [a.strip() for a in " ".join(lignes(clean_text(block.get("acquis")))).split(";") if a.strip()]
    acquis = [a[0].upper() + a[1:] for a in acquis]  # majuscule en début de puce
    fiche = {"methodes": " ".join(methodes), "acquis": acquis if len(acquis) > 1 else " ".join(acquis)}
    if titre:
        fiche["titre"] = titre
    return {k: v for k, v in fiche.items() if v}


def personnes(data: dict, prefixe: str) -> list[dict]:
    """Une fiche si le nom est renseigné : nom, prénom, fonction, mail, téléphone."""
    fiche = {champ: value(data, f"{prefixe}_{champ}") for champ in ("nom", "prenom", "fonction", "email", "telephone")}
    fiche = {k: v for k, v in fiche.items() if v}
    return [fiche] if fiche.get("nom") else []


def ville_depuis_adresse(adresse: str) -> str:
    """« Chemin des Canaux, 30230 Rodilhan » -> « Rodilhan »."""
    trouve = re.search(r"\b\d{5}\s+(.+)$", adresse.strip())
    return trouve.group(1).strip() if trouve else ""


def set_or_drop(data: dict, key: str, valeurs: list, vide=None) -> None:
    """Liste non vide -> paramètre ; sinon `vide` (ou [donnée manquante] si vide=None)."""
    if valeurs:
        data[key] = valeurs
    elif vide is not None:
        data[key] = vide
    else:
        data.pop(key, None)


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
    print("GENERATE CONTRATS PEDAGOGIQUES DE GROUPE")
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
