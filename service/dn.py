"""
Envoi des documents vers DN (annotations privées) et synchronisation des statuts.

Deux documents, même mécanique : upload des PDF en pièces jointes des
annotations privées, coche « envoyé », ajout d'un label, statut écrit dans
Grist. Un document peut compter plusieurs PDF (kit péda + attestation) :
la coche et le statut ne valent « envoyé » que si TOUS ses PDF sont dans DN.
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
DEMARCHE_NUMBER = 128447

# Ids DN à mettre à jour si le formulaire des annotations privées change
# (chacun est surchargeable par la variable d'environnement indiquée).
DOCUMENTS = {
    "pedagogique": {
        "nom": "kit pédagogique et attestation de présence",
        "pieces": {
            "pedagogique": {
                "nom": "kit pédagogique",
                "pj": os.environ.get("DN_ANNOTATION_PJ_PEDAGOGIQUE", "Q2hhbXAtNjk5NDM1MA=="),
            },
            "attestation": {
                "nom": "attestation de présence",
                "pj": os.environ.get("DN_ANNOTATION_PJ_ATTESTATION", "Q2hhbXAtNzExNzEzMQ=="),
            },
        },
        "coche": os.environ.get("DN_ANNOTATION_ENVOYE_PEDAGOGIQUE", "Q2hhbXAtNjk2OTQ5NQ=="),
        "label": os.environ.get("DN_LABEL_PEDAGOGIQUE", "TGFiZWwtNTMxOTMx"),  # Kit péda envoyé (ENSFEA)
        "colonne_grist": "contrat_pedagogique_envoye_par_l_ensfea",
    },
    "financier": {
        "nom": "contrat financier",
        "pieces": {
            "financier": {
                "nom": "contrat financier",
                "pj": os.environ.get("DN_ANNOTATION_PJ_FINANCIER", "Q2hhbXAtNjk5NDczMg=="),
            },
        },
        "coche": os.environ.get("DN_ANNOTATION_ENVOYE_FINANCIER", "Q2hhbXAtNjk5NDY1MQ=="),
        "label": os.environ.get("DN_LABEL_FINANCIER", "TGFiZWwtNDE4Nzg1"),  # Kit financier envoyé (ENSFEA)
        "colonne_grist": "contrat_financier_envoye_par_l_ensfea",
    },
}

# Annotations voisines au libellé proche : l'app ne doit JAMAIS les modifier
ANNOTATIONS_PROTEGEES = {"Q2hhbXAtNjk5NDc1MA=="}

HEADERS = {"Content-Type": "application/json", "Authorization": f"Bearer {API_TOKEN}"}

# Fragment GraphQL commun aux requêtes sur les annotations
FRAGMENT_ANNOTATIONS = """
              id
              stringValue
              ... on PieceJustificativeChamp { files { filename } }
"""


def _doc(document: str) -> dict:
    if document not in DOCUMENTS:
        raise ValueError(f"Document inconnu : {document}")
    return DOCUMENTS[document]


def _graphql(query: str, variables: dict) -> dict:
    resp = requests.post(
        API_URL, headers=HEADERS, json={"query": query, "variables": variables}
    )
    resp.raise_for_status()
    data = resp.json()
    if "errors" in data:
        raise RuntimeError(data["errors"])
    return data["data"]


def _grist() -> GristService:
    return GristService(kit.GRIST_DOC_ID, kit.GRIST_TEAM_SITE, kit.GRIST_SERVER)


def _get_dossier_and_annotation_ids(dossier_number) -> tuple:
    grist = _grist()

    dossiers = grist.get_table_records(TABLE_DOSSIERS)
    dossier_row = next(
        (r for r in dossiers if r.get("dossier_number") == str(dossier_number)), None
    )
    if not dossier_row:
        raise ValueError(f"Dossier {dossier_number} introuvable dans {TABLE_DOSSIERS}")

    annotations = grist.get_table_records(kit.GRIST_TABLE)
    annotation_row = next(
        (r for r in annotations if r.get("dossier_number") == str(dossier_number)), None
    )
    if not annotation_row:
        raise ValueError(f"Dossier {dossier_number} introuvable dans {kit.GRIST_TABLE}")
    return dossier_row[COLONNE_DOSSIER_ID], annotation_row["id"]


def _annotations_dossier(dossier_number) -> dict:
    """Annotations d'un dossier lues en direct dans DN, indexées par id."""
    query = (
        "query($number: Int!) { dossier(number: $number) { annotations {"
        + FRAGMENT_ANNOTATIONS
        + "} } }"
    )
    data = _graphql(query, {"number": int(dossier_number)})
    return {a["id"]: a for a in data["dossier"]["annotations"]}


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
    for a in annotations:
        if a["id"] in ANNOTATIONS_PROTEGEES:
            raise RuntimeError(f"Annotation {a['id']} protégée : modification refusée")
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


def _ajouter_label(dossier_id: str, label_id: str) -> None:
    query = """
    mutation dossierAjouterLabel($input: DossierAjouterLabelInput!) {
      dossierAjouterLabel(input: $input) {
        errors { message }
      }
    }
    """
    variables = {"input": {"dossierId": dossier_id, "labelId": label_id}}
    payload = _graphql(query, variables)["dossierAjouterLabel"]
    errors = payload.get("errors") or []
    if errors and not all("déjà associé" in e["message"] for e in errors):
        raise RuntimeError(errors)


def _supprimer_label(dossier_id: str, label_id: str) -> None:
    query = """
    mutation dossierSupprimerLabel($input: DossierSupprimerLabelInput!) {
      dossierSupprimerLabel(input: $input) {
        errors { message }
      }
    }
    """
    variables = {"input": {"dossierId": dossier_id, "labelId": label_id}}
    payload = _graphql(query, variables)["dossierSupprimerLabel"]
    errors = payload.get("errors") or []
    if errors:
        raise RuntimeError(errors)


def _marquer_envoye_dans_grist(grist_row_id, colonne: str, envoye: bool) -> None:
    """Écrit directement le statut d'envoi dans Grist, sans attendre le prochain cycle de sync OTP."""
    _grist().update_grist_data(kit.GRIST_TABLE, [{"id": grist_row_id, colonne: envoye}])


def fetch_statuts_pj_dn() -> dict:
    """Un seul passage paginé sur la démarche. Pour chaque dossier et chaque document :
    {dossier_number: {"dossier_id": str, "pedagogique": {...}, "financier": {...}}}
    avec pour chaque document {"pj_trouvee", "a_un_fichier", "coche_dn"}.
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
            par_id = {a["id"]: a for a in node["annotations"]}
            info = {"dossier_id": node["id"]}
            for document, conf in DOCUMENTS.items():
                pjs = [par_id.get(p["pj"]) for p in conf["pieces"].values()]
                coche = par_id.get(conf["coche"])
                info[document] = {
                    # toutes les PJ du document existent dans le formulaire DN
                    "pj_trouvee": all(pj is not None for pj in pjs),
                    # « envoyé » seulement si TOUTES les PJ ont un fichier
                    "a_un_fichier": all(pj and pj.get("files") for pj in pjs),
                    "coche_dn": bool(coche and str(coche.get("stringValue")).lower() == "true"),
                }
            resultats[str(node["number"])] = info
        if not page["pageInfo"]["hasNextPage"]:
            break
        after = page["pageInfo"]["endCursor"]
    return resultats


def synchroniser_statuts_pj_avec_dn() -> dict:
    """Pour chaque document, corrige deux écarts selon la réalité DN (fichier attaché ou non) :
    1. Grist vs DN : le statut affiché dans l'appli doit refléter DN.
    2. Coche/label DN sans fichier : décochés et retirés.
    Un document dont la PJ est introuvable dans DN n'est jamais modifié.
    """
    statuts_dn = fetch_statuts_pj_dn()
    grist = _grist()
    lignes = grist.get_table_records(kit.GRIST_TABLE)

    corriges = {document: [] for document in DOCUMENTS}
    updates = {}
    erreurs = {}
    for row in lignes:
        dossier_number = row.get("dossier_number")
        info = statuts_dn.get(dossier_number)
        if not info:
            continue
        for document, conf in DOCUMENTS.items():
            etat = info[document]
            if not etat["pj_trouvee"]:
                continue

            if etat["a_un_fichier"] != bool(row.get(conf["colonne_grist"])):
                updates.setdefault(row["id"], {"id": row["id"]})[conf["colonne_grist"]] = etat[
                    "a_un_fichier"
                ]
                corriges[document].append(dossier_number)

            if not etat["a_un_fichier"] and etat["coche_dn"]:
                try:
                    _modifier_annotations(
                        info["dossier_id"],
                        [{"id": conf["coche"], "value": {"checkbox": False}}],
                    )
                    _supprimer_label(info["dossier_id"], conf["label"])
                except Exception as exc:  # noqa: BLE001
                    erreurs[f"{dossier_number} ({conf['nom']})"] = str(exc)

    if updates:
        grist.update_grist_data(kit.GRIST_TABLE, list(updates.values()))

    # Une PJ introuvable sur tous les dossiers : son id a sans doute changé dans DN
    for document, conf in DOCUMENTS.items():
        if statuts_dn and not any(i[document]["pj_trouvee"] for i in statuts_dn.values()):
            ids = ", ".join(p["pj"] for p in conf["pieces"].values())
            erreurs[conf["nom"]] = f"Annotations PJ introuvables dans DN : {ids}"

    return {
        "verifies": len(statuts_dn),
        "corriges": corriges["pedagogique"],
        "corriges_financier": corriges["financier"],
        "erreurs": erreurs,
    }


def envoyer_document(document: str, dossier_number, pdf_paths: dict) -> None:
    """Envoie les PDF d'un document vers DN pour un dossier : PJ + coche + label + statut Grist.
    pdf_paths = {pdf: chemin}, ex : {"pedagogique": ..., "attestation": ...}.

    Une PJ qui a déjà un fichier dans DN n'est pas renvoyée (l'API DN n'a
    aucune mutation de suppression : renvoyer ajouterait un doublon). On
    complète seulement celles qui manquent ; si toutes sont déjà remplies,
    l'envoi est refusé. Nettoyage éventuel : à la main, côté instructeur DN.
    """
    conf = _doc(document)
    dossier_id, grist_row_id = _get_dossier_and_annotation_ids(dossier_number)

    annotations = _annotations_dossier(dossier_number)
    if conf["coche"] not in annotations:
        raise RuntimeError(f"Case {conf['coche']} ({conf['nom']}) introuvable dans DN")

    a_envoyer, deja_la = [], []
    for pdf, piece in conf["pieces"].items():
        pj = annotations.get(piece["pj"])
        if pj is None:
            raise RuntimeError(f"Annotation PJ {piece['pj']} ({piece['nom']}) introuvable dans DN")
        fichiers = pj.get("files") or []
        if fichiers:
            deja_la.append(f"{piece['nom']} : {fichiers[0]['filename']}")
        else:
            a_envoyer.append((pdf, piece))

    if not a_envoyer:
        raise RuntimeError(
            "Déjà présent dans DN :<br>" + "<br>".join(deja_la) + "<br> "
            "Supprime le fichier manuellement côté instructeur DN avant de renvoyer.<br> "
            "l'API ne permet pas de remplacer une pièce jointe existante."
        )

    # Confirmé incomplet côté DN : Grist peut être remis à jour même avant l'envoi
    # (utile si l'envoi échoue plus loin : le statut reste honnête).
    _marquer_envoye_dans_grist(grist_row_id, conf["colonne_grist"], False)

    modifications = []
    for pdf, piece in a_envoyer:
        signed_blob_id = _create_direct_upload(pdf_paths[pdf], dossier_id)
        modifications.append(
            {"id": piece["pj"], "value": {"pieceJustificative": [signed_blob_id]}}
        )
    # Toutes les PJ sont maintenant remplies (déjà là + envoyées) : on coche
    modifications.append({"id": conf["coche"], "value": {"checkbox": True}})
    _modifier_annotations(dossier_id, modifications)

    _ajouter_label(dossier_id, conf["label"])

    _marquer_envoye_dans_grist(grist_row_id, conf["colonne_grist"], True)


def envoyer_kit_pedagogique(dossier_number, pdf_path: str) -> None:
    """Compatibilité : ancien nom utilisé par les scripts."""
    envoyer_document("pedagogique", dossier_number, {"pedagogique": pdf_path})
