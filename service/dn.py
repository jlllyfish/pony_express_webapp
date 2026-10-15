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
import unicodedata

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

LABEL_ID = "TGFiZWwtNTMxOTMx"  # "Kit péda envoyé (ENSFEA)"
DEMARCHE_NUMBER = 128447

# Les champs d'annotation sont retrouvés par leur libellé : leurs ids changent
# quand le formulaire des annotations privées est modifié dans DN.
LABEL_PJ_FINANCIER = "Contrat financier (à récupérer pour signature)"
COLONNE_GRIST_FINANCIER = "contrat_financier_envoye_par_l_ensfea"

# Fragment GraphQL commun : assez d'infos pour reconnaître chaque champ
FRAGMENT_ANNOTATIONS = """
              id
              label
              __typename
              stringValue
              ... on PieceJustificativeChamp { files { filename } }
"""


def _norm_label(label) -> str:
    """Libellé sans accents, sans casse ni espaces superflus, pour comparer."""
    texte = str(label or "").replace("\u2019", "'")  # apostrophe typographique
    texte = unicodedata.normalize("NFD", texte).encode("ascii", "ignore").decode()
    return " ".join(texte.lower().split())


def _trouver_annotations(annotations: list) -> dict:
    """Repère, parmi les annotations d'un dossier, les trois champs utiles.
    Renvoie {"pj_pedagogique", "coche_pedagogique", "pj_financier"} -> annotation ou None."""
    pj_ped = coche_ped = pj_fin = None
    for a in annotations:
        label = _norm_label(a.get("label"))
        type_ = a.get("__typename")
        if type_ == "PieceJustificativeChamp":
            if label == _norm_label(LABEL_PJ_FINANCIER):
                pj_fin = a
            elif "contrat pedagogique" in label and pj_ped is None:
                pj_ped = a
        elif type_ == "CheckboxChamp" and "contrat pedagogique" in label and "envoye" in label:
            coche_ped = a
    return {"pj_pedagogique": pj_ped, "coche_pedagogique": coche_ped, "pj_financier": pj_fin}


def _annotations_dossier(dossier_number) -> dict:
    """Champs d'annotation utiles d'un dossier, lus en direct dans DN."""
    query = (
        "query($number: Int!) { dossier(number: $number) { annotations {"
        + FRAGMENT_ANNOTATIONS
        + "} } }"
    )
    data = _graphql(query, {"number": int(dossier_number)})
    champs = _trouver_annotations(data["dossier"]["annotations"])
    if not champs["pj_pedagogique"]:
        raise RuntimeError(
            "Champ PJ « Contrat pédagogique » introuvable dans les annotations DN du dossier"
        )
    if not champs["coche_pedagogique"]:
        raise RuntimeError(
            "Case « Contrat pédagogique envoyé… » introuvable dans les annotations DN du dossier"
        )
    return champs

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
    return dossier_id, annotation_row["id"]


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


def _marquer_envoye_dans_grist(grist_row_id, envoye: bool) -> None:
    """Écrit directement le statut d'envoi dans Grist, sans attendre le prochain cycle de sync OTP."""
    grist = GristService(kit.GRIST_DOC_ID, kit.GRIST_TEAM_SITE, kit.GRIST_SERVER)
    grist.update_grist_data(
        kit.GRIST_TABLE,
        [{"id": grist_row_id, "contrat_pedagogique_envoye_par_l_ensfea": envoye}],
    )


def fetch_statuts_pj_dn() -> dict:
    """Interroge DN en un seul passage paginé pour savoir, pour chaque dossier
    de la démarche, si un fichier est réellement attaché au champ PJ kit
    pédagogique ET l'état réel de la coche "envoyé". Retourne
    {dossier_number (str): {"a_un_fichier": bool, "coche_dn": bool, "dossier_id": str}}.
    """
    query = (
        """
    query($demarcheNumber: Int!, $after: String) {
      demarche(number: $demarcheNumber) {
        dossiers(first: 100, after: $after) {
          pageInfo { hasNextPage endCursor }
          nodes {
            id
            number
            annotations {"""
        + FRAGMENT_ANNOTATIONS
        + """}
          }
        }
      }
    }
    """
    )
    resultats = {}
    after = None
    while True:
        data = _graphql(query, {"demarcheNumber": DEMARCHE_NUMBER, "after": after})
        page = data["demarche"]["dossiers"]
        for node in page["nodes"]:
            champs = _trouver_annotations(node["annotations"])
            pj = champs["pj_pedagogique"]
            coche = champs["coche_pedagogique"]
            pj_financier = champs["pj_financier"]
            a_un_fichier = bool(pj and pj.get("files"))
            coche_dn = bool(coche and str(coche.get("stringValue")).lower() == "true")
            resultats[str(node["number"])] = {
                "a_un_fichier": a_un_fichier,
                # None = champ PJ financier introuvable sur ce dossier : on ne touche à rien
                "financier_a_un_fichier": (
                    bool(pj_financier.get("files")) if pj_financier else None
                ),
                "coche_dn": coche_dn,
                "pj_pedagogique_trouve": pj is not None,
                "coche_id": coche["id"] if coche else None,
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
    corriges_financier = []
    updates = []
    erreurs = {}
    for row in annotations:
        dossier_number = row.get("dossier_number")
        info = statuts_dn.get(dossier_number)
        if not info:
            continue

        # Contrat financier : la case Grist doit refléter la présence d'un fichier dans DN
        financier_dn = info["financier_a_un_fichier"]
        if financier_dn is not None and financier_dn != bool(row.get(COLONNE_GRIST_FINANCIER)):
            updates.append({"id": row["id"], COLONNE_GRIST_FINANCIER: financier_dn})
            corriges_financier.append(dossier_number)

        if not info["pj_pedagogique_trouve"]:
            continue  # champ introuvable : on ne touche pas au statut pédagogique
        a_un_fichier = info["a_un_fichier"]
        coche_dn = info["coche_dn"]
        dossier_id = info["dossier_id"]
        valeur_grist = bool(row.get("contrat_pedagogique_envoye_par_l_ensfea"))

        if a_un_fichier != valeur_grist:
            update = next((u for u in updates if u["id"] == row["id"]), None)
            if update is None:
                update = {"id": row["id"]}
                updates.append(update)
            update["contrat_pedagogique_envoye_par_l_ensfea"] = a_un_fichier
            corriges.append(dossier_number)

        if not a_un_fichier and coche_dn and info["coche_id"]:
            try:
                _modifier_annotations(
                    dossier_id,
                    [
                        {
                            "id": info["coche_id"],
                            "value": {"checkbox": False},
                        }
                    ],
                )
                _supprimer_label(dossier_id)
            except Exception as exc:  # noqa: BLE001
                erreurs[dossier_number] = str(exc)

    if updates:
        grist.update_grist_data(kit.GRIST_TABLE, updates)

    if statuts_dn and not any(i["pj_pedagogique_trouve"] for i in statuts_dn.values()):
        erreurs["contrat_pedagogique"] = (
            "Champ PJ « Contrat pédagogique » introuvable dans les annotations DN"
        )

    # Si aucun dossier n'a le champ PJ financier, son libellé a sans doute changé dans DN
    financier_trouve = any(i["financier_a_un_fichier"] is not None for i in statuts_dn.values())
    if statuts_dn and not financier_trouve:
        erreurs["contrat_financier"] = (
            f"Champ PJ « {LABEL_PJ_FINANCIER} » introuvable dans les annotations DN"
        )

    return {
        "verifies": len(statuts_dn),
        "corriges": corriges,
        "corriges_financier": corriges_financier,
        "erreurs": erreurs,
    }


def envoyer_kit_pedagogique(dossier_number, pdf_path: str) -> None:
    """Envoie le kit pédagogique généré vers DN pour un dossier : PJ + coche + label + statut Grist.

    Bloque l'envoi si un fichier est déjà attaché côté DN (vérifié en direct,
    pas via le statut Grist qui peut être périmé) : l'API DN n'a aucune
    mutation de suppression de pièce jointe, donc renvoyer sans avoir
    supprimé l'ancien fichier ajouterait un doublon plutôt que de le
    remplacer. Nettoyage : à la main, côté interface instructeur DN.
    """
    dossier_id, grist_row_id = _get_dossier_and_annotation_ids(dossier_number)

    champs = _annotations_dossier(dossier_number)
    fichiers_existants = champs["pj_pedagogique"].get("files") or []
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
            {
                "id": champs["pj_pedagogique"]["id"],
                "value": {"pieceJustificative": [signed_blob_id]},
            },
            {"id": champs["coche_pedagogique"]["id"], "value": {"checkbox": True}},
        ],
    )

    _ajouter_label(dossier_id)

    _marquer_envoye_dans_grist(grist_row_id, True)
