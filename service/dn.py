"""
Envoi du kit pédagogique vers DN : upload en pièce jointe de l'annotation
privée, coche "envoyé par l'ENSFEA", ajout du label "Kit péda envoyé (ENSFEA)".

Reprend telle quelle la logique validée dans scripts/test_envoi_dn.py (Phase 3).
"""

import base64
import hashlib
import json
import mimetypes
import os

import requests
from pony_express.service.grist import GristService
from pony_express.templates import contrat_pedagogique as kit

API_URL = os.environ.get(
    "DN_API_URL", "https://demarche.numerique.gouv.fr/api/v2/graphql"
)
API_TOKEN = os.environ["DN_API_TOKEN"]
INSTRUCTEUR_ID = os.environ["INSTRUCTEUR_ID"]

TABLE_DOSSIERS = "Demarche_128447_dossiers"
COLONNE_DOSSIER_ID = "dossier_id"
COLONNE_ANNOTATION_ID = "contrat_pedagogique_id"

# Stables au niveau de la démarche (mêmes pour tous les dossiers, vérifié via GraphiQL)
ANNOTATION_ID_ENVOYE_PEDAGOGIQUE = "Q2hhbXAtNjk2OTQ5NQ=="
LABEL_ID = "TGFiZWwtNTMxOTMx"  # "Kit péda envoyé (ENSFEA)"

HEADERS = {"Content-Type": "application/json", "Authorization": f"Bearer {API_TOKEN}"}


def _graphql(query: str, variables: dict) -> dict:
    resp = requests.post(
        API_URL, headers=HEADERS, json={"query": query, "variables": variables}
    )
    resp.raise_for_status()
    data = resp.json()
    if "errors" in data:
        raise RuntimeError(data["errors"])
    return data["data"]


def _get_dossier_and_annotation_ids(dossier_number) -> tuple:
    grist = GristService(kit.GRIST_DOC_ID, kit.GRIST_TEAM_SITE, kit.GRIST_SERVER)

    dossiers = grist.get_table_records(TABLE_DOSSIERS)
    dossier_row = next(
        (r for r in dossiers if r.get("dossier_number") == str(dossier_number)), None
    )
    if not dossier_row:
        raise ValueError(f"Dossier {dossier_number} introuvable dans {TABLE_DOSSIERS}")
    dossier_id = dossier_row[COLONNE_DOSSIER_ID]

    annotations = grist.get_table_records(kit.GRIST_TABLE)
    annotation_row = next(
        (r for r in annotations if r.get("dossier_number") == str(dossier_number)), None
    )
    if not annotation_row:
        raise ValueError(f"Dossier {dossier_number} introuvable dans {kit.GRIST_TABLE}")
    annotation_id = annotation_row[COLONNE_ANNOTATION_ID]
    grist_row_id = annotation_row["id"]

    return dossier_id, annotation_id, grist_row_id


def _create_direct_upload(file_path: str, dossier_id: str) -> str:
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
    direct_upload = _graphql(query, variables)["createDirectUpload"]["directUpload"]

    put_headers = json.loads(direct_upload["headers"])
    put_resp = requests.put(direct_upload["url"], data=content, headers=put_headers)
    put_resp.raise_for_status()

    return direct_upload["signedBlobId"]


def _modifier_annotations(dossier_id: str, annotations: list) -> list:
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
    payload = _graphql(query, variables)["dossierModifierAnnotations"]
    if payload.get("errors"):
        raise RuntimeError(payload["errors"])
    return payload["annotations"]


def _ajouter_label(dossier_id: str) -> None:
    query = """
    mutation dossierAjouterLabel($input: DossierAjouterLabelInput!) {
      dossierAjouterLabel(input: $input) {
        errors { message }
      }
    }
    """
    variables = {"input": {"dossierId": dossier_id, "labelId": LABEL_ID}}
    payload = _graphql(query, variables)["dossierAjouterLabel"]
    errors = payload.get("errors") or []
    if errors and not all("déjà associé" in e["message"] for e in errors):
        raise RuntimeError(errors)


def _supprimer_label(dossier_id: str) -> None:
    query = """
    mutation dossierSupprimerLabel($input: DossierSupprimerLabelInput!) {
      dossierSupprimerLabel(input: $input) {
        errors { message }
      }
    }
    """
    variables = {"input": {"dossierId": dossier_id, "labelId": LABEL_ID}}
    payload = _graphql(query, variables)["dossierSupprimerLabel"]
    errors = payload.get("errors") or []
    if errors:
        raise RuntimeError(errors)


def _get_current_files(dossier_number, annotation_id: str) -> list:
    """Interroge DN pour savoir si un fichier est déjà attaché sur ce champ PJ, à l'instant présent."""
    query = """
    query($number: Int!) {
      dossier(number: $number) {
        annotations {
          id
          ... on PieceJustificativeChamp { files { filename } }
        }
      }
    }
    """
    data = _graphql(query, {"number": int(dossier_number)})
    for a in data["dossier"]["annotations"]:
        if a["id"] == annotation_id:
            return a.get("files") or []
    return []


def _marquer_envoye_dans_grist(grist_row_id, envoye: bool) -> None:
    """Écrit directement le statut d'envoi dans Grist, sans attendre le prochain cycle de sync OTP."""
    grist = GristService(kit.GRIST_DOC_ID, kit.GRIST_TEAM_SITE, kit.GRIST_SERVER)
    grist.update_grist_data(
        kit.GRIST_TABLE,
        [{"id": grist_row_id, "contrat_pedagogique_envoye_par_l_ensfea": envoye}],
    )


DEMARCHE_NUMBER = 128447
ANNOTATION_ID_PJ_PEDAGOGIQUE = (
    "Q2hhbXAtNjk2OTQ5Ng=="  # "Contrat pédagogique" (le vrai champ PJ)
)


def fetch_statuts_pj_dn() -> dict:
    """Interroge DN en un seul passage paginé pour savoir, pour chaque dossier
    de la démarche, si un fichier est réellement attaché au champ PJ kit
    pédagogique ET l'état réel de la coche "envoyé". Retourne
    {dossier_number (str): {"a_un_fichier": bool, "coche_dn": bool, "dossier_id": str}}.
    """
    query = """
    query($demarcheNumber: Int!, $after: String) {
      demarche(number: $demarcheNumber) {
        dossiers(first: 100, after: $after) {
          pageInfo { hasNextPage endCursor }
          nodes {
            id
            number
            annotations {
              id
              stringValue
              ... on PieceJustificativeChamp { files { filename } }
            }
          }
        }
      }
    }
    """
    resultats = {}
    after = None
    while True:
        data = _graphql(query, {"demarcheNumber": DEMARCHE_NUMBER, "after": after})
        page = data["demarche"]["dossiers"]
        for node in page["nodes"]:
            pj = next(
                (
                    a
                    for a in node["annotations"]
                    if a["id"] == ANNOTATION_ID_PJ_PEDAGOGIQUE
                ),
                None,
            )
            coche = next(
                (
                    a
                    for a in node["annotations"]
                    if a["id"] == ANNOTATION_ID_ENVOYE_PEDAGOGIQUE
                ),
                None,
            )
            a_un_fichier = bool(pj and pj.get("files"))
            coche_dn = bool(coche and str(coche.get("stringValue")).lower() == "true")
            resultats[str(node["number"])] = {
                "a_un_fichier": a_un_fichier,
                "coche_dn": coche_dn,
                "dossier_id": node["id"],
            }
        if not page["pageInfo"]["hasNextPage"]:
            break
        after = page["pageInfo"]["endCursor"]
    return resultats


def synchroniser_statuts_pj_avec_dn() -> dict:
    """Corrige deux écarts indépendants, chacun selon la réalité DN (fichiers) :
    1. Grist vs DN — le statut affiché dans l'appli doit refléter DN.
    2. La coche/label DN vs DN — pas de coche "envoyé" ni de label sans fichier
       réellement attaché, même si Grist était déjà à jour de son côté.
    """
    statuts_dn = fetch_statuts_pj_dn()

    grist = GristService(kit.GRIST_DOC_ID, kit.GRIST_TEAM_SITE, kit.GRIST_SERVER)
    annotations = grist.get_table_records(kit.GRIST_TABLE)

    corriges = []
    updates = []
    erreurs = {}
    for row in annotations:
        dossier_number = row.get("dossier_number")
        info = statuts_dn.get(dossier_number)
        if not info:
            continue

        a_un_fichier = info["a_un_fichier"]
        coche_dn = info["coche_dn"]
        dossier_id = info["dossier_id"]
        valeur_grist = bool(row.get("contrat_pedagogique_envoye_par_l_ensfea"))

        if a_un_fichier != valeur_grist:
            updates.append(
                {
                    "id": row["id"],
                    "contrat_pedagogique_envoye_par_l_ensfea": a_un_fichier,
                }
            )
            corriges.append(dossier_number)

        if not a_un_fichier and coche_dn:
            try:
                _modifier_annotations(
                    dossier_id,
                    [
                        {
                            "id": ANNOTATION_ID_ENVOYE_PEDAGOGIQUE,
                            "value": {"checkbox": False},
                        }
                    ],
                )
                _supprimer_label(dossier_id)
            except Exception as exc:  # noqa: BLE001
                erreurs[dossier_number] = str(exc)

    if updates:
        grist.update_grist_data(kit.GRIST_TABLE, updates)

    return {"verifies": len(statuts_dn), "corriges": corriges, "erreurs": erreurs}


def envoyer_kit_pedagogique(dossier_number, pdf_path: str) -> None:
    """Envoie le kit pédagogique généré vers DN pour un dossier : PJ + coche + label + statut Grist.

    Bloque l'envoi si un fichier est déjà attaché côté DN (vérifié en direct,
    pas via le statut Grist qui peut être périmé) : l'API DN n'a aucune
    mutation de suppression de pièce jointe, donc renvoyer sans avoir
    supprimé l'ancien fichier ajouterait un doublon plutôt que de le
    remplacer. Nettoyage : à la main, côté interface instructeur DN.
    """
    dossier_id, annotation_id, grist_row_id = _get_dossier_and_annotation_ids(
        dossier_number
    )

    fichiers_existants = _get_current_files(dossier_number, annotation_id)
    if fichiers_existants:
        raise RuntimeError(
            f"Un fichier est déjà attaché dans DN :<br>{fichiers_existants[0]['filename']}.<br> "
            "Supprime-le manuellement côté instructeur DN avant de renvoyer.<br> "
            "l'API ne permet pas de remplacer une pièce jointe existante."
        )

    # Confirmé vide côté DN : Grist peut être remis à jour même avant l'envoi
    # (utile si l'envoi échoue plus loin : le statut reste honnête).
    _marquer_envoye_dans_grist(grist_row_id, False)

    signed_blob_id = _create_direct_upload(pdf_path, dossier_id)

    _modifier_annotations(
        dossier_id,
        [
            {"id": annotation_id, "value": {"pieceJustificative": [signed_blob_id]}},
            {"id": ANNOTATION_ID_ENVOYE_PEDAGOGIQUE, "value": {"checkbox": True}},
        ],
    )

    _ajouter_label(dossier_id)

    _marquer_envoye_dans_grist(grist_row_id, True)
