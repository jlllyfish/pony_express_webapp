"""
Données du tableau de bord du consortium, lues dans Grist.

- Financier Erasmus : une ligne par code projet (subvention, forfaits PAMO et OS)
- Mobilités : dossiers des démarches apprenants (128447), groupes (156967)
  et personnel (156966), hors dossiers refusés ou classés sans suite
- Montants engagés : colonne montant_bourse des annotations de chaque démarche

Forfaits par participant : OS individuel × (apprenants + personnel),
OS groupe × participants des groupes, PAMO × participants PAMO.
"""

import logging
import os
import re
import time
import unicodedata
from datetime import datetime, timezone

from pony_express.service.grist import GristService
from pony_express.service.utils import clean_text
from pony_express.templates import contrat_pedagogique as kit

# Code projet sélectionné par défaut à l'ouverture du tableau de bord
CODE_PROJET_DEFAUT = "2026-1-FR01-KA121-VET-000435983"

TABLE_FINANCIER = os.environ.get("GRIST_TABLE_FINANCIER", "Financier_Erasmus")
COLONNE_MONTANT = "montant_bourse"
COLONNE_ETABLISSEMENT = "votre_etablissement"
COLONNE_DATE_DEBUT = "date_debut_activite_hors_jours_de_voyage"
COLONNE_PARTICIPANTS_GROUPE = "nombre_d_apprenants_total"
# Colonne (table champs ou annotations) repérant un participant PAMO : à renseigner
COLONNE_PAMO = os.environ.get("GRIST_COLONNE_PAMO", "")
ETATS_EXCLUS = {"refuse", "sans_suite"}

DEMARCHES = {
    "apprenants": {"numero": 128447, "doc_id": kit.GRIST_DOC_ID},
    "groupes": {"numero": 156967, "doc_id": os.environ.get("GRIST_DOC_ID_GROUPE") or kit.GRIST_DOC_ID},
    "personnel": {"numero": 156966, "doc_id": os.environ.get("GRIST_DOC_ID_PERSONNEL") or kit.GRIST_DOC_ID},
}
TYPES = tuple(DEMARCHES)

# Colonnes de Financier Erasmus (comparaison sans casse, espaces ni accents)
COLONNES_FINANCIER = {
    "projet": "projet",
    "subvention": "subvention",
    "pamo": "pamo",
    "os_indiv": "osindiv",
    "os_etab_indiv": "osetablissementindiv",
    "os_ensfea_indiv": "osensfeaindiv",
    "os_groupe": "osgroupe",
    "os_etab_groupe": "osetablissementgroupe",
    "os_ensfea_groupe": "osensfeagroupe",
}

logger = logging.getLogger(__name__)

CACHE_SECONDES = 300
_cache: dict = {"t": 0, "donnees": None}


def _cle(texte: str) -> str:
    texte = unicodedata.normalize("NFD", str(texte)).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]", "", texte.lower())


def _nombre(valeur) -> float:
    """Nombre Grist (ou texte « 1 234,50 € ») ; 0 si vide ou illisible."""
    if isinstance(valeur, (int, float)) and not isinstance(valeur, bool):
        return float(valeur)
    texte = re.sub(r"[^\d,.\-]", "", str(valeur or "")).replace(",", ".")
    try:
        return float(texte) if texte else 0.0
    except ValueError:
        return 0.0


def _vrai(valeur) -> bool:
    if isinstance(valeur, str):
        return _cle(valeur) in {"oui", "true", "vrai", "1", "x"}
    return bool(valeur)


def _annee(valeur) -> str:
    if isinstance(valeur, (int, float)) and valeur:
        return str(datetime.fromtimestamp(valeur, tz=timezone.utc).year)
    m = re.search(r"(19|20)\d{2}", str(valeur or ""))
    return m.group(0) if m else ""


def _par_dossier(rows: list[dict]) -> dict:
    return {str(r.get("dossier_number")): r for r in rows}


def _lire(grist: GristService, table: str, chrono: list) -> list[dict]:
    """Lecture d'une table Grist, chronométrée."""
    debut = time.perf_counter()
    rows = grist.get_table_records(table)
    ms = round((time.perf_counter() - debut) * 1000)
    chrono.append({"table": table, "lignes": len(rows), "ms": ms})
    logger.warning("Dashboard : %s lue en %d ms (%d lignes)", table, ms, len(rows))
    return rows


def _lire_financier(grist: GristService, chrono: list) -> list[dict]:
    projets = []
    for row in _lire(grist, TABLE_FINANCIER, chrono):
        par_cle = {_cle(k): v for k, v in row.items()}
        ligne = {nom: par_cle.get(cle) for nom, cle in COLONNES_FINANCIER.items()}
        ligne["projet"] = clean_text(ligne["projet"])
        if not ligne["projet"]:
            continue
        for nom in COLONNES_FINANCIER:
            if nom != "projet":
                ligne[nom] = _nombre(ligne[nom])
        projets.append(ligne)
    return projets


def _lire_mobilites(grists: dict, chrono: list) -> list[dict]:
    """Une ligne par dossier retenu : type, établissement, année, participants, montant, PAMO."""
    mobilites = []
    for type_mob, dem in DEMARCHES.items():
        grist = grists[dem["doc_id"]]
        prefixe = f"Demarche_{dem['numero']}"
        champs = _par_dossier(_lire(grist, f"{prefixe}_champs", chrono))
        annotations = _par_dossier(_lire(grist, f"{prefixe}_annotations", chrono))
        dossiers = _par_dossier(_lire(grist, f"{prefixe}_dossiers", chrono))
        for numero, champ in champs.items():
            etat = clean_text(dossiers.get(numero, {}).get("state"))
            if etat in ETATS_EXCLUS:
                continue
            annot = annotations.get(numero, {})
            participants = 1
            if type_mob == "groupes":
                participants = int(_nombre(champ.get(COLONNE_PARTICIPANTS_GROUPE)))
            pamo = 0
            if COLONNE_PAMO:
                source = champ if COLONNE_PAMO in champ else annot
                valeur = source.get(COLONNE_PAMO)
                # case à cocher (1 participant) ou nombre de participants PAMO
                pamo = int(_nombre(valeur)) if isinstance(valeur, (int, float)) and not isinstance(valeur, bool) else int(_vrai(valeur))
            mobilites.append({
                "type": type_mob,
                "etablissement": clean_text(champ.get(COLONNE_ETABLISSEMENT)) or "Non renseigné",
                "annee": _annee(champ.get(COLONNE_DATE_DEBUT)),
                "participants": participants,
                "montant": _nombre(annot.get(COLONNE_MONTANT)),
                "pamo": pamo,
            })
    return mobilites


def _charger(rafraichir: bool = False) -> dict:
    if not rafraichir and _cache["donnees"] and time.time() - _cache["t"] < CACHE_SECONDES:
        return {**_cache["donnees"], "chargement": {**_cache["donnees"]["chargement"], "memoire": True}}
    debut = time.perf_counter()
    chrono: list = []
    grists = {
        doc: GristService(doc, kit.GRIST_TEAM_SITE, kit.GRIST_SERVER)
        for doc in {d["doc_id"] for d in DEMARCHES.values()}
    }
    donnees = {
        "projets": _lire_financier(grists[kit.GRIST_DOC_ID], chrono),
        "mobilites": _lire_mobilites(grists, chrono),
    }
    donnees["chargement"] = {
        "ms": round((time.perf_counter() - debut) * 1000),
        "tables": chrono,
        "memoire": False,
    }
    logger.warning("Dashboard : lecture Grist totale %d ms", donnees["chargement"]["ms"])
    _cache.update(t=time.time(), donnees=donnees)
    return donnees


def donnees_dashboard(
    etablissement: str = "", code_projet: str = "", annee: str = "", type_mobilite: str = "",
    rafraichir: bool = False,
) -> dict:
    donnees = _charger(rafraichir)
    projets, toutes = donnees["projets"], donnees["mobilites"]
    types = (type_mobilite,) if type_mobilite in TYPES else TYPES

    # Un seul projet aujourd'hui : toutes les mobilités lui sont rattachées
    retenus = [p for p in projets if not code_projet or p["projet"] == code_projet]
    mobilites = [
        m for m in toutes
        if (not etablissement or m["etablissement"] == etablissement)
        and (not annee or m["annee"] == annee)
        and m["type"] in types
        and (retenus or not projets)
    ]

    def compte(type_mob, lignes=mobilites):
        return sum(1 for m in lignes if m["type"] == type_mob)

    par_etab = {}
    for m in mobilites:
        e = par_etab.setdefault(m["etablissement"], {t: 0 for t in TYPES} | {"montant": 0.0})
        e[m["type"]] += 1
        e["montant"] += m["montant"]
    par_etablissement = sorted(
        (
            {"nom": nom, "mobilites": sum(e[t] for t in TYPES), **{t: e[t] for t in TYPES},
             "montant_engage": round(e["montant"])}
            for nom, e in par_etab.items()
        ),
        key=lambda e: (-e["mobilites"], e["nom"]),
    )

    def somme_projets(cle):
        return sum(p[cle] for p in retenus)

    # Forfaits : moyenne si plusieurs projets sélectionnés (identiques en pratique)
    def forfait(cle):
        return somme_projets(cle) / len(retenus) if retenus else 0

    participants_indiv = sum(m["participants"] for m in mobilites if m["type"] in ("apprenants", "personnel"))
    participants_groupes = sum(m["participants"] for m in mobilites if m["type"] == "groupes")
    participants_pamo = sum(m["pamo"] for m in mobilites)

    return {
        "exemple": False,
        "chargement": donnees["chargement"],
        "filtres": {
            "etablissements": sorted({m["etablissement"] for m in toutes}),
            "codes_projet": [p["projet"] for p in projets],
            "code_projet_defaut": CODE_PROJET_DEFAUT,
            "annees": sorted({m["annee"] for m in toutes if m["annee"]}, reverse=True),
            "types": [
                {"valeur": "apprenants", "libelle": "Apprenants"},
                {"valeur": "personnel", "libelle": "Personnel"},
                {"valeur": "groupes", "libelle": "Groupes"},
            ],
        },
        "totaux": {
            "mobilites": len(mobilites),
            "apprenants": compte("apprenants"),
            "personnel": compte("personnel"),
            "groupes": compte("groupes"),
            "participants_groupes": participants_groupes,
        },
        "par_etablissement": par_etablissement,
        "statut": None,  # public / privé : pas encore de source
        "subvention": {
            "accordee": round(somme_projets("subvention")),
            "engagee": round(sum(m["montant"] for m in mobilites)),
            "versee": None,  # pas encore de source
            "pamo": round(forfait("pamo") * participants_pamo),
            "pamo_forfait": forfait("pamo"),
            "pamo_participants": participants_pamo if COLONNE_PAMO else None,
            "os_etablissement": round(
                forfait("os_etab_indiv") * participants_indiv + forfait("os_etab_groupe") * participants_groupes
            ),
            "os_ensfea": round(
                forfait("os_ensfea_indiv") * participants_indiv + forfait("os_ensfea_groupe") * participants_groupes
            ),
            "participants_indiv": participants_indiv,
            "participants_groupes": participants_groupes,
        },
    }
