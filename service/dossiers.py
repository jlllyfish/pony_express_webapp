"""
Alimente la liste/filtre de l'interface (établissement + recherche par nom).

Réutilise les constantes déjà définies dans le template de génération
(pony_express.templates.contrat_pedagogique) pour ne pas dupliquer le nom
des tables/colonnes Grist à deux endroits différents.
"""

from pony_express.service.grist import GristService
from pony_express.service.utils import clean_text, get_date_from_timestamp
from pony_express.templates import contrat_pedagogique as kit

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


def list_dossiers() -> list[dict]:
    grist = _grist()
    main_rows = grist.get_table_records(kit.GRIST_TABLE)
    champs_by_dossier = {
        row.get("dossier_number"): row for row in grist.get_table_records(kit.TABLE_CHAMPS)
    }

    dossiers = []
    for row in main_rows:
        dossier_number = row.get("dossier_number")
        champ = champs_by_dossier.get(dossier_number, {})
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
                # statut non persisté pour l'instant (Phase 4 : colonnes dédiées dans Grist)
                "statut": "non_genere",
            }
        )
    return dossiers


def list_etablissements(dossiers: list[dict]) -> list[str]:
    return sorted({d["etablissement"] for d in dossiers})
