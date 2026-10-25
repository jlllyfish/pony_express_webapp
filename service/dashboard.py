"""
Données du tableau de bord du consortium.

Pour l'instant : DONNÉES D'EXEMPLE (« exemple »: True), dans la forme
définitive attendue par l'interface. La jonction avec Grist remplacera
le contenu de donnees_dashboard() sans changer cette forme.
"""

EXEMPLE_ETABLISSEMENTS = [
    # (établissement, statut, apprenants, personnel, groupes, montant engagé en €)
    ("EPLEFPA Toulouse", "public", 152, 18, 12, 187_600),
    ("EPLEFPA Lozère", "public", 120, 14, 7, 145_300),
    ("Nîmes-Rodilhan", "public", 108, 13, 7, 131_900),
    ("Perpignan-Roussillon", "public", 98, 12, 7, 120_600),
    ("Lycée Saint-Joseph", "prive", 82, 9, 5, 99_000),
    ("EPLEFPA Aveyron", "public", 74, 9, 5, 90_700),
    ("Autres établissements", "prive", 131, 23, 3, 162_400),
]


TYPES = ("apprenants", "personnel", "groupes")

# Code projet sélectionné par défaut à l'ouverture du tableau de bord
CODE_PROJET_DEFAUT = "2026-1-FR01-KA121-VET-000435983"


def donnees_dashboard(
    etablissement: str = "", code_projet: str = "", annee: str = "", type_mobilite: str = ""
) -> dict:
    types = (type_mobilite,) if type_mobilite in TYPES else TYPES
    lignes = []
    for nom, statut, app, pers, grp, montant in EXEMPLE_ETABLISSEMENTS:
        if etablissement and nom != etablissement:
            continue
        nb = {"apprenants": app, "personnel": pers, "groupes": grp}
        retenu = {t: (nb[t] if t in types else 0) for t in TYPES}
        total = app + pers + grp
        part = sum(retenu.values()) / total if total else 0
        lignes.append({"nom": nom, "statut": statut, **retenu, "montant": montant * part})

    def somme(cle):
        return sum(l[cle] for l in lignes)

    engage = round(somme("montant"))
    part = engage / 937_500
    return {
        "exemple": True,
        "filtres": {
            "etablissements": [l[0] for l in EXEMPLE_ETABLISSEMENTS],
            "codes_projet": [CODE_PROJET_DEFAUT],
            "code_projet_defaut": CODE_PROJET_DEFAUT,
            "annees": ["2026", "2025"],
            "types": [
                {"valeur": "apprenants", "libelle": "Apprenants"},
                {"valeur": "personnel", "libelle": "Personnel"},
                {"valeur": "groupes", "libelle": "Groupes"},
            ],
        },
        "totaux": {
            "mobilites": somme("apprenants") + somme("personnel") + somme("groupes"),
            "apprenants": somme("apprenants"),
            "personnel": somme("personnel"),
            "groupes": somme("groupes"),
            "participants_groupes": round(612 * somme("groupes") / 46),
        },
        "par_etablissement": [
            {
                "nom": l["nom"],
                "mobilites": l["apprenants"] + l["personnel"] + l["groupes"],
                "apprenants": l["apprenants"],
                "personnel": l["personnel"],
                "groupes": l["groupes"],
                "montant_engage": round(l["montant"]),
            }
            for l in lignes
        ],
        "statut": {
            "public": sum(l["apprenants"] + l["personnel"] + l["groupes"] for l in lignes if l["statut"] == "public"),
            "prive": sum(l["apprenants"] + l["personnel"] + l["groupes"] for l in lignes if l["statut"] == "prive"),
        },
        "subvention": {
            "accordee": round(1_250_000 * (part if etablissement or type_mobilite else 1)),
            "engagee": engage,
            "versee": round(612_000 * part),
            # soutien à l'inclusion des participants avec moins d'opportunités
            "pamo": round(48_600 * part),
            # soutien organisationnel : part établissements + part ENSFEA
            "os_etablissement": round(113_100 * part),
            "os_ensfea": round(28_300 * part),
        },
    }
