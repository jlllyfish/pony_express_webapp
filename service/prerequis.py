"""
Éléments que les instructeurs doivent saisir dans les annotations privées DN avant qu'un
document puisse être généré ou envoyé.

- Kit pédagogique / contrat pédagogique + attestation : le code projet.
- Contrat financier : le code projet, le nombre de jours de voyage et les montants.

Sans eux, le PDF sortirait avec « [donnée manquante] ». Deux usages :
- la liste des dossiers affiche ce qui manque (données du cache, à titre indicatif) ;
- avant chaque génération, téléchargement ou envoi, le dossier est relu dans Grist
  (données fraîches) et refusé s'il manque quelque chose.
"""

import os

from pony_express.templates import contrat_pedagogique as kit

from service.grist_lecture import ligne_du_dossier

CODE_PROJET = ("code_projet", "Code projet")
JOURS_VOYAGE = ("nombre_de_jours_de_voyage", "Nombre de jours de voyage")
MONTANTS_INDIVIDUELS = [
    JOURS_VOYAGE,
    ("montant_frais_de_sejour", "Montant des frais de séjour"),
    ("montant_frais_de_voyage", "Montant des frais de voyage"),
    ("montant_bourse", "Montant de la bourse"),
]

REQUIS = {
    "apprenants": {
        "doc": kit.GRIST_DOC_ID,
        "table": kit.GRIST_TABLE,  # Demarche_128447_annotations
        "pedagogique": [CODE_PROJET],
        "financier": [CODE_PROJET, *MONTANTS_INDIVIDUELS],
    },
    "groupes": {
        "doc": os.environ.get("GRIST_DOC_ID_GROUPE") or kit.GRIST_DOC_ID,
        "table": "Demarche_156967_annotations",
        "pedagogique": [CODE_PROJET],
        "financier": [
            CODE_PROJET,
            JOURS_VOYAGE,
            ("montant_frais_de_voyage_par_participant", "Frais de voyage par participant"),
            ("montant_frais_de_sejour_apprenant", "Frais de séjour par apprenant"),
            ("montant_total_bourse_apprenant_voyage_sejour", "Bourse totale par apprenant"),
            ("montant_frais_de_sejour_accompagnateur", "Frais de séjour par accompagnateur"),
            ("montant_total_bourse_accompagnateur_voyage_sejour", "Bourse totale par accompagnateur"),
        ],
    },
    "personnel": {
        "doc": os.environ.get("GRIST_DOC_ID_PERSONNEL") or kit.GRIST_DOC_ID,
        "table": "Demarche_156966_annotations",
        "pedagogique": [CODE_PROJET],
        "financier": [CODE_PROJET, *MONTANTS_INDIVIDUELS],
    },
}
TYPES = ("pedagogique", "financier")


def vue_du_document(document: str) -> str:
    if document.endswith("_groupe"):
        return "groupes"
    if document.endswith("_personnel"):
        return "personnel"
    return "apprenants"


def type_du_document(document: str) -> str:
    """« pedagogique » (kit, contrat, attestation) ou « financier »."""
    return "financier" if document.startswith("financier") else "pedagogique"


def colonnes(vue: str) -> list[str]:
    """Colonnes d'annotations à lire pour la liste de la page."""
    vues = REQUIS[vue]
    return list(dict.fromkeys(col for t in TYPES for col, _ in vues[t]))


def _vide(valeur) -> bool:
    # 0 est une valeur saisie (frais nuls) ; seuls l'absence et le texte vide manquent
    return valeur is None or (isinstance(valeur, str) and not valeur.strip())


def manquants(vue: str, ligne: dict) -> dict:
    """{"pedagogique": [libellés manquants], "financier": [...]} pour une ligne d'annotations."""
    return {t: [libelle for col, libelle in REQUIS[vue][t] if _vide(ligne.get(col))] for t in TYPES}


def verifier(document: str, dossier_number) -> tuple[list[str], dict | None]:
    """Relit le dossier dans Grist. Retourne (libellés manquants pour ce document, manquants complets).

    Le second élément sert à mettre à jour l'affichage (None si le dossier est introuvable).
    """
    vue = vue_du_document(document)
    lignes = ligne_du_dossier(REQUIS[vue]["doc"], REQUIS[vue]["table"], dossier_number)
    if not lignes:
        return ["Annotations privées du dossier introuvables dans Grist"], None
    tout = manquants(vue, lignes[0])
    return tout[type_du_document(document)], tout
