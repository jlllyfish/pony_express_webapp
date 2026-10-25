"""
Calculs du tableau de bord du consortium Erasmus+.

Ce fichier regroupe TOUTES les règles de calcul, sans aucun accès à Grist :
pour changer une règle, une colonne ou un forfait, c'est ici.
(La lecture des tables Grist et la mémoire de 5 min sont dans dashboard.py.)

Sommaire
  1. Sources : tables et colonnes Grist utilisées
  2. Conversions : lecture des valeurs Grist (nombres, dates, cases vides)
  3. Mobilités : un dossier DN -> une mobilité (ou exclu)
  4. Filtres : établissement, code projet, année, type
  5. Indicateurs : compteurs, montants engagés, PAMO, soutien organisationnel
  6. Assemblage : la réponse envoyée à l'interface

Tester une règle en ligne de commande :
    python -m service.dashboard_calculs
"""

import json
import os
import re
import unicodedata
from datetime import datetime, timezone

# =====================================================================
# 1. SOURCES : tables et colonnes Grist
# =====================================================================

# Code projet sélectionné par défaut à l'ouverture du tableau de bord
CODE_PROJET_DEFAUT = "2026-1-FR01-KA121-VET-000435983"

# Une démarche DN par type de mobilité. Pour chacune, trois tables Grist :
# Demarche_<numero>_champs, _annotations et _dossiers (reliées par dossier_number).
DEMARCHES = {
    "apprenants": {"numero": 128447, "libelle": "Apprenants"},
    "personnel": {"numero": 156966, "libelle": "Personnel"},
    "groupes": {"numero": 156967, "libelle": "Groupes"},
}
TYPES = tuple(DEMARCHES)

# Table des montants du projet : une ligne par code projet.
TABLE_FINANCIER = os.environ.get("GRIST_TABLE_FINANCIER", "Financier_Erasmus")

# Colonnes de Financier Erasmus. Comparaison sans casse, espaces, « _ » ni accents :
# « OS _Ensfea_indiv » et « OS_Ensfea_indiv » sont la même colonne.
COLONNES_FINANCIER = {
    "projet": "Projet",                                    # code projet
    "subvention": "Subvention",                            # subvention accordée (€)
    "pamo": "PAMO",                                        # forfait PAMO par participant (€)
    "os_indiv": "OS_indiv",                                # forfait OS individuel (€) = étab + ENSFEA
    "os_etab_indiv": "OS_Etablissement_indiv",             # part établissement du forfait OS individuel
    "os_ensfea_indiv": "OS_Ensfea_indiv",                  # part ENSFEA du forfait OS individuel
    "os_groupe": "OS_groupe",                              # forfait OS groupe (€) = étab + ENSFEA
    "os_etab_groupe": "OS_Etablissement_groupe",           # part établissement du forfait OS groupe
    "os_ensfea_groupe": "OS_Ensfea_groupe",                # part ENSFEA du forfait OS groupe
}

# Colonnes des démarches (table entre parenthèses)
COL_ETAT = "state"                                         # (_dossiers) état DN du dossier
COL_ETABLISSEMENT = "votre_etablissement"                  # (_champs) établissement d'envoi
COL_DATE_DEBUT = "date_debut_activite_hors_jours_de_voyage"  # (_champs) donne l'année
COL_MONTANT = "montant_bourse"                             # (_annotations) bourse engagée (€)
COL_EFFECTIF_GROUPE = "nombre_d_apprenants_total"          # (_champs, groupes) participants du groupe
COL_PAMO_APPRENANT = "critere_participant_s_ayant_moins_d_opportunites"  # (_annotations, apprenants)
COL_PAMO_GROUPE = "nombre_de_pamo"                         # (_champs, groupes)

# Dossiers DN non comptés (ni mobilité, ni bourse, ni forfait)
ETATS_EXCLUS = {"refuse", "sans_suite"}


def colonnes_lues(type_mob: str) -> dict:
    """Colonnes à lire dans Grist pour une démarche, par table (les autres ne sont pas lues).
    À compléter si une nouvelle règle utilise une autre colonne."""
    champs = [COL_ETABLISSEMENT, COL_DATE_DEBUT]
    annotations = [COL_MONTANT]
    if type_mob == "groupes":
        champs += [COL_EFFECTIF_GROUPE, COL_PAMO_GROUPE]
    if type_mob == "apprenants":
        annotations += [COL_PAMO_APPRENANT]
    return {"champs": champs, "annotations": annotations, "dossiers": [COL_ETAT]}


# =====================================================================
# 2. CONVERSIONS : valeurs Grist -> valeurs Python
# =====================================================================

def cle(texte) -> str:
    """Nom de colonne simplifié pour comparaison : « OS _Ensfea_indiv » -> « osensfeaindiv »."""
    texte = unicodedata.normalize("NFD", str(texte)).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]", "", texte.lower())


def texte(valeur) -> str:
    return " ".join(str(valeur).split()) if valeur is not None else ""


def nombre(valeur) -> float:
    """Nombre Grist, ou texte « 1 234,50 € » ; 0 si vide ou illisible."""
    if isinstance(valeur, bool):
        return float(valeur)
    if isinstance(valeur, (int, float)):
        return float(valeur)
    brut = re.sub(r"[^\d,.\-]", "", str(valeur or "")).replace(",", ".")
    try:
        return float(brut) if brut else 0.0
    except ValueError:
        return 0.0


def est_renseigne(valeur) -> bool:
    """Faux si la cellule est vide : None, "", espaces, liste de choix vide (["L"] dans l'API Grist)."""
    if valeur is None:
        return False
    if isinstance(valeur, str) and valeur.strip().startswith("["):
        try:  # liste de choix renvoyée en texte par une requête SQL : '["L","Handicap"]'
            valeur = json.loads(valeur)
        except ValueError:
            pass
    if isinstance(valeur, list):
        return any(v != "L" and texte(v) for v in valeur)
    return bool(texte(valeur))


def annee(valeur) -> str:
    """Année d'une date Grist (horodatage en secondes) ou d'un texte « 2026-03-14 »."""
    if isinstance(valeur, (int, float)) and not isinstance(valeur, bool) and valeur:
        return str(datetime.fromtimestamp(valeur, tz=timezone.utc).year)
    m = re.search(r"(19|20)\d{2}", str(valeur or ""))
    return m.group(0) if m else ""


# =====================================================================
# 3. MOBILITÉS : un dossier DN -> une mobilité
# =====================================================================

def est_compte(dossier: dict) -> bool:
    """Un dossier est compté sauf s'il est refusé ou classé sans suite."""
    return texte(dossier.get(COL_ETAT)) not in ETATS_EXCLUS


def participants(type_mob: str, champ: dict) -> int:
    """Participants d'une mobilité : 1 pour un apprenant ou un personnel,
    l'effectif déclaré (nombre_d_apprenants_total) pour un groupe."""
    if type_mob == "groupes":
        return int(nombre(champ.get(COL_EFFECTIF_GROUPE)))
    return 1


def participants_pamo(type_mob: str, champ: dict, annot: dict) -> int:
    """Participants ouvrant droit au forfait PAMO (moins d'opportunités) :
    - apprenant : 1 si le critère PAMO est renseigné dans les annotations, 0 s'il est vide
    - groupe    : nombre_de_pamo saisi dans le formulaire
    - personnel : 0 (pas de PAMO)"""
    if type_mob == "apprenants":
        return 1 if est_renseigne(annot.get(COL_PAMO_APPRENANT)) else 0
    if type_mob == "groupes":
        return int(nombre(champ.get(COL_PAMO_GROUPE)))
    return 0


def mobilite(type_mob: str, champ: dict, annot: dict, dossier: dict) -> dict | None:
    """Une mobilité à partir des 3 lignes Grist d'un dossier ; None si le dossier n'est pas compté."""
    if not est_compte(dossier):
        return None
    return {
        "type": type_mob,
        "etablissement": texte(champ.get(COL_ETABLISSEMENT)) or "Non renseigné",
        "annee": annee(champ.get(COL_DATE_DEBUT)),
        "participants": participants(type_mob, champ),
        "participants_pamo": participants_pamo(type_mob, champ, annot),
        "montant": nombre(annot.get(COL_MONTANT)),
    }


def mobilites_jointes(type_mob: str, rows: list) -> list[dict]:
    """Mobilités d'une démarche à partir de lignes déjà jointes (champs + annotations + dossiers)."""
    return [m for row in rows if (m := mobilite(type_mob, row, row, row))]


def mobilites_demarche(type_mob: str, champs: list, annotations: list, dossiers: list) -> list[dict]:
    """Toutes les mobilités d'une démarche (tables reliées par dossier_number)."""
    def par_dossier(rows):
        return {str(r.get("dossier_number")): r for r in rows}

    annot, doss = par_dossier(annotations), par_dossier(dossiers)
    resultat = []
    for numero, champ in par_dossier(champs).items():
        m = mobilite(type_mob, champ, annot.get(numero, {}), doss.get(numero, {}))
        if m:
            resultat.append(m)
    return resultat


def projets(rows: list) -> list[dict]:
    """Lignes de Financier Erasmus -> [{projet, subvention, pamo, os_...}] (montants en nombres)."""
    cles = {nom: cle(col) for nom, col in COLONNES_FINANCIER.items()}
    resultat = []
    for row in rows:
        par_cle = {cle(k): v for k, v in row.items()}
        ligne = {nom: par_cle.get(c) for nom, c in cles.items()}
        ligne["projet"] = texte(ligne["projet"])
        if ligne["projet"]:
            resultat.append({k: (v if k == "projet" else nombre(v)) for k, v in ligne.items()})
    return resultat


# =====================================================================
# 4. FILTRES
# =====================================================================

def filtrer(mobilites: list, projets_retenus: list, etablissement="", annee_choisie="", types=TYPES) -> list:
    """Mobilités retenues par les filtres.
    Un seul projet aujourd'hui : toutes les mobilités lui sont rattachées. Si le code projet
    choisi n'existe pas dans Financier Erasmus, aucune mobilité n'est retenue."""
    if not projets_retenus:
        return []
    return [
        m for m in mobilites
        if (not etablissement or m["etablissement"] == etablissement)
        and (not annee_choisie or m["annee"] == annee_choisie)
        and m["type"] in types
    ]


# =====================================================================
# 5. INDICATEURS
# =====================================================================

def forfait(projets_retenus: list, nom: str) -> float:
    """Forfait (€ par participant) du projet retenu ; moyenne si plusieurs projets."""
    return sum(p[nom] for p in projets_retenus) / len(projets_retenus) if projets_retenus else 0.0


def subvention_accordee(projets_retenus: list) -> float:
    """Somme des subventions des projets retenus."""
    return sum(p["subvention"] for p in projets_retenus)


def montant_engage(mobilites: list) -> float:
    """Somme des bourses (montant_bourse) des mobilités retenues."""
    return sum(m["montant"] for m in mobilites)


def nb_participants(mobilites: list, types: tuple) -> int:
    return sum(m["participants"] for m in mobilites if m["type"] in types)


def montant_pamo(mobilites: list, projets_retenus: list) -> dict:
    """PAMO = forfait PAMO × participants PAMO (apprenants avec critère + nombre_de_pamo des groupes)."""
    nb = sum(m["participants_pamo"] for m in mobilites)
    f = forfait(projets_retenus, "pamo")
    return {"montant": f * nb, "forfait": f, "participants": nb}


def soutien_organisationnel(mobilites: list, projets_retenus: list) -> dict:
    """Soutien organisationnel (OS), part établissement et part ENSFEA :
        OS établissement = OS_Etablissement_indiv × participants individuels
                         + OS_Etablissement_groupe × participants des groupes
        OS ENSFEA        = OS_Ensfea_indiv × participants individuels
                         + OS_Ensfea_groupe × participants des groupes
        OS total         = OS établissement + OS ENSFEA
    Participants individuels = apprenants + personnel (1 par dossier)."""
    indiv = nb_participants(mobilites, ("apprenants", "personnel"))
    groupes = nb_participants(mobilites, ("groupes",))
    etab = forfait(projets_retenus, "os_etab_indiv") * indiv + forfait(projets_retenus, "os_etab_groupe") * groupes
    ensfea = forfait(projets_retenus, "os_ensfea_indiv") * indiv + forfait(projets_retenus, "os_ensfea_groupe") * groupes
    return {"etablissement": etab, "ensfea": ensfea, "total": etab + ensfea,
            "participants_indiv": indiv, "participants_groupes": groupes}


def par_etablissement(mobilites: list) -> list[dict]:
    """Par établissement : nombre de mobilités par type et montant engagé, du plus grand au plus petit."""
    lignes: dict = {}
    for m in mobilites:
        e = lignes.setdefault(m["etablissement"], {t: 0 for t in TYPES} | {"montant": 0.0})
        e[m["type"]] += 1
        e["montant"] += m["montant"]
    return sorted(
        ({"nom": nom, "mobilites": sum(e[t] for t in TYPES), **{t: e[t] for t in TYPES},
          "montant_engage": round(e["montant"])} for nom, e in lignes.items()),
        key=lambda e: (-e["mobilites"], e["nom"]),
    )


# =====================================================================
# 6. ASSEMBLAGE : réponse de /api/dashboard
# =====================================================================

def indicateurs(tous_projets: list, toutes_mobilites: list,
                etablissement="", code_projet="", annee_choisie="", type_mobilite="") -> dict:
    types = (type_mobilite,) if type_mobilite in TYPES else TYPES
    retenus = [p for p in tous_projets if not code_projet or p["projet"] == code_projet]
    mob = filtrer(toutes_mobilites, retenus, etablissement, annee_choisie, types)
    pamo = montant_pamo(mob, retenus)
    os_ = soutien_organisationnel(mob, retenus)

    def compte(type_mob):
        return sum(1 for m in mob if m["type"] == type_mob)

    return {
        "exemple": False,
        "filtres": {
            "etablissements": sorted({m["etablissement"] for m in toutes_mobilites}),
            "codes_projet": [p["projet"] for p in tous_projets],
            "code_projet_defaut": CODE_PROJET_DEFAUT,
            "annees": sorted({m["annee"] for m in toutes_mobilites if m["annee"]}, reverse=True),
            "types": [{"valeur": t, "libelle": DEMARCHES[t]["libelle"]} for t in ("apprenants", "personnel", "groupes")],
        },
        "totaux": {
            "mobilites": len(mob),
            "apprenants": compte("apprenants"),
            "personnel": compte("personnel"),
            "groupes": compte("groupes"),
            "participants_groupes": os_["participants_groupes"],
        },
        "par_etablissement": par_etablissement(mob),
        "statut": None,  # public / privé : pas encore de source
        "subvention": {
            "accordee": round(subvention_accordee(retenus)),
            "engagee": round(montant_engage(mob)),
            "versee": None,  # pas encore de source
            "pamo": round(pamo["montant"]),
            "pamo_forfait": pamo["forfait"],
            "pamo_participants": pamo["participants"],
            "os_etablissement": round(os_["etablissement"]),
            "os_ensfea": round(os_["ensfea"]),
            "participants_indiv": os_["participants_indiv"],
            "participants_groupes": os_["participants_groupes"],
        },
    }


if __name__ == "__main__":
    # Exemple chiffré : vérifie les règles sans Grist
    financier = projets([{"Projet": CODE_PROJET_DEFAUT, "Subvention": 1_000_000, "PAMO": 125,
                          "OS_indiv": 350, "OS_Etablissement_indiv": 133, "OS _Ensfea_indiv": 217,
                          "OS_groupe": 100, "OS_Etablissement_groupe": 66, "OS_Ensfea_groupe": 34}])
    mob = (
        mobilites_demarche("apprenants",
                           [{"dossier_number": 1, COL_ETABLISSEMENT: "Lycée A"},
                            {"dossier_number": 2, COL_ETABLISSEMENT: "Lycée A"},
                            {"dossier_number": 3, COL_ETABLISSEMENT: "Lycée B"}],
                           [{"dossier_number": 1, COL_MONTANT: 2000, COL_PAMO_APPRENANT: "Difficultés économiques"},
                            {"dossier_number": 2, COL_MONTANT: "1 500,50", COL_PAMO_APPRENANT: None},
                            {"dossier_number": 3, COL_MONTANT: 900}],
                           [{"dossier_number": 3, COL_ETAT: "refuse"}])
        + mobilites_demarche("groupes",
                             [{"dossier_number": 9, COL_ETABLISSEMENT: "Lycée B",
                               COL_EFFECTIF_GROUPE: 12, COL_PAMO_GROUPE: 3}],
                             [{"dossier_number": 9, COL_MONTANT: 10_000}], [])
    )
    s = indicateurs(financier, mob)["subvention"]
    assert s["engagee"] == round(2000 + 1500.5 + 10_000)              # dossier 3 refusé
    assert s["pamo"] == 125 * (1 + 3)                                  # 1 apprenant + 3 en groupe
    assert s["os_etablissement"] == 133 * 2 + 66 * 12
    assert s["os_ensfea"] == 217 * 2 + 34 * 12
    print("Règles vérifiées :", s)
