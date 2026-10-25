"""
Génère les documents (kit pédagogique, contrat financier) pour des dossiers
précis, en réutilisant tels quels le mapping et les transformations des
templates Pony_express.

On ne réutilise pas generate_pdf_from_grist() directement : cette fonction
génère pour TOUS les dossiers filtrés par should_be_exported, alors que
l'UI doit pouvoir cibler une sélection précise.
"""

from pony_express.service.grist import GristService
from pony_express.service.pdf import generate_pdf
from pony_express.service.utils import TEMPLATES_FOLDER_PATH
from pony_express.templates import (
    attestation_presence,
    contrat_financier,
    contrat_financier_groupe,
    contrat_pedagogique,
    contrat_pedagogique_groupe,
)

# PDF -> (module du template, Enum de mapping Grist)
TEMPLATES = {
    "pedagogique": (contrat_pedagogique, contrat_pedagogique.STUDENT_DATA),
    "attestation": (attestation_presence, attestation_presence.STUDENT_DATA),
    "financier": (contrat_financier, contrat_financier.PERSON_DATA),
    "pedagogique_groupe": (contrat_pedagogique_groupe, contrat_pedagogique_groupe.STUDENT_DATA),
    "financier_groupe": (contrat_financier_groupe, contrat_financier_groupe.STUDENT_DATA),
}

# Document traité dans l'interface -> PDF produits ensemble
PIECES = {
    "pedagogique": ["pedagogique", "attestation"],
    "financier": ["financier"],
    "pedagogique_groupe": ["pedagogique_groupe"],
    "financier_groupe": ["financier_groupe"],
}


def generate_document(document: str, dossier_numbers: list) -> dict:
    """Génère le PDF du document pour chaque dossier demandé. Retourne {dossier_number: chemin_pdf}."""
    if document not in TEMPLATES:
        raise ValueError(f"Document inconnu : {document}")
    tpl, mapping = TEMPLATES[document]

    grist = GristService(tpl.GRIST_DOC_ID, tpl.GRIST_TEAM_SITE, tpl.GRIST_SERVER)
    records = grist.get_grist_data(tpl.GRIST_TABLE, mapping, tpl.should_be_exported)

    wanted = {str(n) for n in dossier_numbers}
    results = {}
    for record in records:
        if str(record.get("numero_dossier")) not in wanted:
            continue
        transformed = tpl.apply_data_transformation(record)
        pdf_path = generate_pdf(
            transformed,
            TEMPLATES_FOLDER_PATH + tpl.TEMPLATE_FOLDERNAME,
            tpl.TEMPLATE_FILENAME,
            tpl.TEMPLATE_NAME,
            tpl.name_pdf(transformed),
        )
        results[record["numero_dossier"]] = pdf_path
    return results


def generate_pieces(document: str, dossier_numbers: list) -> dict:
    """Génère tous les PDF d'un document (ex : kit péda + attestation).
    Retourne {dossier_number (str): {pdf: chemin}} pour les dossiers dont
    TOUS les PDF ont pu être générés."""
    if document not in PIECES:
        raise ValueError(f"Document inconnu : {document}")
    par_pdf = {
        pdf: {str(k): v for k, v in generate_document(pdf, dossier_numbers).items()}
        for pdf in PIECES[document]
    }
    resultats = {}
    for n in {str(n) for n in dossier_numbers}:
        chemins = {pdf: par_pdf[pdf].get(n) for pdf in PIECES[document]}
        if all(chemins.values()):
            resultats[n] = chemins
    return resultats


def generate_kit_pedagogique(dossier_numbers: list) -> dict:
    """Compatibilité : ancien nom utilisé par les scripts."""
    return generate_document("pedagogique", dossier_numbers)
