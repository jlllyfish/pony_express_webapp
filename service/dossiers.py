"""
Alimente la liste/filtre de l'interface (établissement + recherche par nom).

Réutilise les constantes déjà définies dans le template de génération
(pony_express.templates.contrat_pedagogique) pour ne pas dupliquer le nom
des tables/colonnes Grist à deux endroits différents.
"""

from pony_express.service.grist import GristService
from pony_express.service.utils import clean_text, get_date_from_timestamp
from pony_express.templates import contrat_pedagogique as kit

from service.grist_lecture import avec_repli, colonnes_jointes

# Colonnes lues dans Demarche_128447_champs pour l'affichage de la carte
CHAMP_ETABLISSEMENT = "votre_etablissement"
CHAMP_PAYS = "pays_d_accueil_nom"
CHAMP_DATE_TRAJET_ALLER = "date_de_trajet_aller"
CHAMP_DATE_TRAJET_RETOUR = "date_de_trajet_retour"
CHAMP_DATE_DEBUT = "date_debut_activite_hors_jours_de_voyage"
CHAMP_DATE_FIN = "date_fin_activite_hors_jours_de_voyage"


def _grist() -> GristService:
    return GristService(kit.GRIST_DOC_ID, kit.GRIST_TEAM_SITE, kit.GRIST_SERVER)


def _date(champ: dict, column: str) -> str:
    """Date au format jj-mm-aa ; chaîne vide si absente ou illisible."""
    try:
        return get_date_from_timestamp(champ[column])
    except (KeyError, TypeError, ValueError):
        return ""


# Colonnes lues dans la table des annotations (kit.GRIST_TABLE)
COLONNES_ANNOTATIONS = [
    "dossier_number",
    "nom_participant",
    "prenom_s_participant",
    "contrat_pedagogique_envoye_par_l_ensfea",
    "contrat_financier_envoye_par_l_ensfea",
]
COLONNES_CHAMPS = [
    CHAMP_ETABLISSEMENT, CHAMP_PAYS, CHAMP_DATE_TRAJET_ALLER,
    CHAMP_DATE_TRAJET_RETOUR, CHAMP_DATE_DEBUT, CHAMP_DATE_FIN,
]


def _lignes_completes() -> list[dict]:
    """Repli : tables entières, fusionnées par numéro de dossier."""
    grist = _grist()
    champs = {r.get("dossier_number"): r for r in grist.get_table_records(kit.TABLE_CHAMPS)}
    return [champs.get(r.get("dossier_number"), {}) | r for r in grist.get_table_records(kit.GRIST_TABLE)]


def list_dossiers() -> list[dict]:
    # Une requête SQL ciblée (colonnes ci-dessus) ; tables entières si elle échoue
    lignes = avec_repli(
        "Page Apprenants",
        lambda: colonnes_jointes(kit.GRIST_DOC_ID, kit.GRIST_TABLE, COLONNES_ANNOTATIONS,
                                 {kit.TABLE_CHAMPS: COLONNES_CHAMPS}),
        _lignes_completes,
    )

    dossiers = []
    for row in lignes:
        dossier_number = row.get("dossier_number")
        champ = row
        nom = clean_text(row.get("nom_participant"))
        prenom = kit.premier_prenom(clean_text(row.get("prenom_s_participant")))
        dossiers.append(
            {
                "dossier_number": dossier_number,
                "nom": nom,
                "prenom": prenom,
                "nom_complet": f"{nom} {prenom}".strip(),
                "etablissement": clean_text(champ.get(CHAMP_ETABLISSEMENT)) or "Non renseigné",
                "pays_accueil": clean_text(champ.get(CHAMP_PAYS)),
                "date_trajet_aller": _date(champ, CHAMP_DATE_TRAJET_ALLER),
                "date_trajet_retour": _date(champ, CHAMP_DATE_TRAJET_RETOUR),
                "date_debut_activite": _date(champ, CHAMP_DATE_DEBUT),
                "date_fin_activite": _date(champ, CHAMP_DATE_FIN),
                "envoye_pedagogique": bool(row.get("contrat_pedagogique_envoye_par_l_ensfea")),
                "envoye_financier": bool(row.get("contrat_financier_envoye_par_l_ensfea")),
                # statut de génération par document, non persisté (mémoire de la session)
                "statuts": {"pedagogique": "non_genere", "financier": "non_genere"},
            }
        )
    return dossiers


def list_etablissements(dossiers: list[dict]) -> list[str]:
    return sorted({d["etablissement"] for d in dossiers})
