"""
Script isolé (Phase 3, indépendant de l'app Flask) : upload d'un PDF dans le
champ PJ de l'annotation privée "kit pédagogique" d'un dossier de test, et
coche l'annotation "contrat_pedagogique_envoye_par_l_ensfea" dans la foulée.

Usage :
  DN_API_TOKEN=xxx INSTRUCTEUR_ID=xxx DOSSIER_NUMBER=33896137 \
    poetry run python scripts/test_envoi_dn.py chemin/vers/kit.pdf
  (GRIST_* viennent de .env, chargé automatiquement)
"""

import base64
import hashlib
import json
import mimetypes
import os
import sys

import requests
from dotenv import load_dotenv

load_dotenv()

from pony_express.service.grist import GristService
from pony_express.templates import contrat_pedagogique as kit

API_URL = os.environ.get(
    "DN_API_URL", "https://demarche.numerique.gouv.fr/api/v2/graphql"
)
API_TOKEN = os.environ["DN_API_TOKEN"]
INSTRUCTEUR_ID = os.environ["INSTRUCTEUR_ID"]
DOSSIER_NUMBER = os.environ[
    "DOSSIER_NUMBER"
]  # texte, pas int : Grist le stocke en texte

TABLE_DOSSIERS = "Demarche_128447_dossiers"
COLONNE_DOSSIER_ID = "dossier_id"
COLONNE_ANNOTATION_ID = "contrat_pedagogique_id"
LABEL_ID = "TGFiZWwtNTMxOTMx"  # "Kit péda envoyé (ENSFEA)"

# ⚠️ propre à ce dossier de test — à terme, à lire par dossier depuis Grist
# (probablement une colonne du style contrat_pedagogique_envoye_par_l_ensfea_id
# dans Demarche_128447_annotations, comme contrat_pedagogique_id)
ANNOTATION_ID_ENVOYE_PEDAGOGIQUE = "Q2hhbXAtNjk2OTQ5NQ=="

HEADERS = {"Content-Type": "application/json", "Authorization": f"Bearer {API_TOKEN}"}


def graphql(query: str, variables: dict) -> dict:
    resp = requests.post(
        API_URL, headers=HEADERS, json={"query": query, "variables": variables}
    )
    resp.raise_for_status()
    data = resp.json()
    if "errors" in data:
        raise RuntimeError(data["errors"])
    return data["data"]


def get_dossier_and_annotation_ids(dossier_number: str) -> tuple[str, str]:
    """Retrouve dossierId (DN) et annotationId (champ PJ kit pédagogique) via Grist."""
    grist = GristService(kit.GRIST_DOC_ID, kit.GRIST_TEAM_SITE, kit.GRIST_SERVER)

    dossiers = grist.get_table_records(TABLE_DOSSIERS)
    dossier_row = next(
        (r for r in dossiers if r.get("dossier_number") == dossier_number), None
    )
    if not dossier_row:
        raise ValueError(f"Dossier {dossier_number} introuvable dans {TABLE_DOSSIERS}")
    dossier_id = dossier_row[COLONNE_DOSSIER_ID]

    annotations = grist.get_table_records(kit.GRIST_TABLE)
    annotation_row = next(
        (r for r in annotations if r.get("dossier_number") == dossier_number), None
    )
    if not annotation_row:
        raise ValueError(f"Dossier {dossier_number} introuvable dans {kit.GRIST_TABLE}")
    annotation_id = annotation_row[COLONNE_ANNOTATION_ID]

    return dossier_id, annotation_id


def create_direct_upload(file_path: str, dossier_id: str) -> str:
    """Étape 1-2 : décrit le fichier à DN, puis l'upload sur l'URL fournie. Retourne le signedBlobId."""
    filename = os.path.basename(file_path)
    content_type = mimetypes.guess_type(filename)[0] or "application/pdf"
    with open(file_path, "rb") as f:
        content = f.read()
    checksum = base64.b64encode(hashlib.md5(content).digest()).decode()

    query = """
    mutation createDirectUpload($input: CreateDirectUploadInput!) {
      createDirectUpload(input: $input) {
        directUpload { url headers blobId signedBlobId }
      }
    }
    """
    variables = {
        "input": {
            "filename": filename,
            "byteSize": len(content),
            "checksum": checksum,
            "contentType": content_type,
            "dossierId": dossier_id,
        }
    }
    direct_upload = graphql(query, variables)["createDirectUpload"]["directUpload"]

    put_headers = json.loads(direct_upload["headers"])
    put_resp = requests.put(direct_upload["url"], data=content, headers=put_headers)
    put_resp.raise_for_status()

    return direct_upload["signedBlobId"]


def modifier_annotations(dossier_id: str, annotations: list) -> list:
    """annotations : liste de {"id": ..., "value": {...}} — batché en un seul appel."""
    query = """
    mutation dossierModifierAnnotations($input: DossierModifierAnnotationsInput!) {
      dossierModifierAnnotations(input: $input) {
        annotations { id stringValue }
        errors { message }
      }
    }
    """
    variables = {
        "input": {
            "dossierId": dossier_id,
            "instructeurId": INSTRUCTEUR_ID,
            "annotations": annotations,
        }
    }
    payload = graphql(query, variables)["dossierModifierAnnotations"]
    if payload.get("errors"):
        raise RuntimeError(payload["errors"])
    return payload["annotations"]


def ajouter_label(dossier_id: str, label_id: str) -> None:
    query = """
    mutation dossierAjouterLabel($input: DossierAjouterLabelInput!) {
      dossierAjouterLabel(input: $input) {
        errors { message }
      }
    }
    """
    variables = {"input": {"dossierId": dossier_id, "labelId": label_id}}
    payload = graphql(query, variables)["dossierAjouterLabel"]
    errors = payload.get("errors") or []
    if errors and not all("déjà associé" in e["message"] for e in errors):
        raise RuntimeError(errors)
    if errors:
        print("Label déjà présent, rien à faire")


if __name__ == "__main__":
    pdf_path = sys.argv[1]

    dossier_id, annotation_id = get_dossier_and_annotation_ids(DOSSIER_NUMBER)
    print(f"dossier_id={dossier_id} annotation_id={annotation_id}")

    # Vide l'annotation PJ avant de réattacher : la pièce jointe s'ajoute plutôt
    # que remplace (comportement typique d'un has_many_attached ActiveStorage),
    # sinon on accumule un fichier de plus à chaque régénération/renvoi.
    modifier_annotations(
        dossier_id, [{"id": annotation_id, "value": {"pieceJustificative": []}}]
    )
    print("Ancienne PJ vidée")

    signed_blob_id = create_direct_upload(pdf_path, dossier_id)
    print(f"signedBlobId={signed_blob_id}")

    result = modifier_annotations(
        dossier_id,
        [
            {"id": annotation_id, "value": {"pieceJustificative": [signed_blob_id]}},
            {"id": ANNOTATION_ID_ENVOYE_PEDAGOGIQUE, "value": {"checkbox": True}},
        ],
    )
    print("OK, annotations mises à jour :", result)
    ajouter_label(dossier_id, LABEL_ID)
    print("Label ajouté")
