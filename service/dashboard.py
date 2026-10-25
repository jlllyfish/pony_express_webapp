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


def donnees_dashboard(etablissement: str = "", code_projet: str = "", annee: str = "") -> dict:
    lignes = [l for l in EXEMPLE_ETABLISSEMENTS if not etablissement or l[0] == etablissement]
    apprenants = sum(l[2] for l in lignes)
    personnel = sum(l[3] for l in lignes)
    groupes = sum(l[4] for l in lignes)
    engage = sum(l[5] for l in lignes)
    part = engage / 937_500 if lignes else 0
    return {
        "exemple": True,
        "filtres": {
            "etablissements": [l[0] for l in EXEMPLE_ETABLISSEMENTS],
            "codes_projet": ["2026-1-FR01-KA121-VET-000123456"],
            "annees": ["2026", "2025"],
        },
        "totaux": {
            "mobilites": apprenants + personnel + groupes,
            "apprenants": apprenants,
            "personnel": personnel,
            "groupes": groupes,
            "participants_groupes": round(612 * part),
        },
        "par_etablissement": [
            {"nom": l[0], "mobilites": l[2] + l[3] + l[4], "montant_engage": l[5]} for l in lignes
        ],
        "statut": {
            "public": sum(l[2] + l[3] + l[4] for l in lignes if l[1] == "public"),
            "prive": sum(l[2] + l[3] + l[4] for l in lignes if l[1] == "prive"),
        },
        "subvention": {
            "accordee": round(1_250_000 * part),
            "engagee": engage,
            "versee": round(612_000 * part),
        },
    }
