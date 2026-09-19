import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

load_dotenv()

from service.dn import fetch_statuts_pj_dn

DOSSIER_NUMBER = os.environ["DOSSIER_NUMBER"]

statuts = fetch_statuts_pj_dn()
print(f"{len(statuts)} dossiers trouvés au total par fetch_statuts_pj_dn")
print(
    f"Statut pour le dossier {DOSSIER_NUMBER} :",
    statuts.get(DOSSIER_NUMBER, "ABSENT DES RÉSULTATS"),
)
