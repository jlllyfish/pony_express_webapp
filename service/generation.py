"""
Génère le kit pédagogique pour des dossiers précis, en réutilisant tel quel
le mapping et les transformations déjà validés dans
pony_express.templates.contrat_pedagogique (Phase 1).

On ne réutilise pas generate_pdf_from_grist() directement : cette fonction
génère pour TOUS les dossiers filtrés par should_be_exported, alors que
l'UI doit pouvoir cibler une sélection précise.
"""

from pony_express.service.grist import GristService
from pony_express.service.pdf import generate_pdf
from pony_express.service.utils import TEMPLATES_FOLDER_PATH
from pony_express.templates import contrat_pedagogique as kit


def generate_kit_pedagogique(dossier_numbers: list) -> dict:
    """Génère le PDF pour chaque dossier demandé. Retourne {dossier_number: chemin_pdf}."""
    grist = GristService(kit.GRIST_DOC_ID, kit.GRIST_TEAM_SITE, kit.GRIST_SERVER)
    records = grist.get_grist_data(kit.GRIST_TABLE, kit.STUDENT_DATA, kit.should_be_exported)

    wanted = {str(n) for n in dossier_numbers}
    results = {}
    for record in records:
        if str(record.get("numero_dossier")) not in wanted:
            continue
        transformed = kit.apply_data_transformation(record)
        pdf_path = generate_pdf(
            transformed,
            TEMPLATES_FOLDER_PATH + kit.TEMPLATE_FOLDERNAME,
            kit.TEMPLATE_FILENAME,
            kit.TEMPLATE_NAME,
            kit.name_pdf(transformed),
        )
        results[record["numero_dossier"]] = pdf_path
    return results
