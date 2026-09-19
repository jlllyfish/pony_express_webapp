from dotenv import load_dotenv

load_dotenv()

from pony_express.service.grist import GristService
from pony_express.templates import contrat_pedagogique as kit

grist = GristService(kit.GRIST_DOC_ID, kit.GRIST_TEAM_SITE, kit.GRIST_SERVER)
rows = grist.get_table_records("Demarche_128447_dossiers")

print(f"{len(rows)} lignes")
if rows:
    print("Colonnes :", list(rows[0].keys()))
    print("Première ligne :", rows[0])
