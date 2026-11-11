from typing import Callable

from pony_express.service.pdf import generate_pdf
from pony_express.service.grist import GristService
from pony_express.service.utils import TEMPLATES_FOLDER_PATH


# Main Function
def generate_pdf_from_grist(
        grist_doc_id,
        grist_team_site,
        grist_table,
        data_enum,
        template_foldername,
        template_filename,
        template_name,
        should_be_exported: Callable[[dict], bool],
        apply_data_transformation: Callable[[dict], dict],
        name_pdf: Callable[[dict], str],
        grist_self_hosted_server: None | str = None,
        grist_pdf_column: None | str = None
):
    grist_service = GristService(grist_doc_id, grist_team_site, grist_self_hosted_server)
    records = grist_service.get_grist_data(grist_table, data_enum, should_be_exported)
    data_to_upload = []
    for record in records:
        transformed_record = apply_data_transformation(record)
        pdf_path = generate_pdf(
            transformed_record,
            TEMPLATES_FOLDER_PATH + template_foldername,
            template_filename,
            template_name,
            name_pdf(transformed_record)
        )
        if grist_pdf_column :
            pdf_id = grist_service.upload_attachments(pdf_path)
            data_to_upload.append( {'id': record['id'], grist_pdf_column: ["L", pdf_id]})
    if data_to_upload and grist_pdf_column:
        grist_service.update_grist_data(grist_table, data_to_upload)