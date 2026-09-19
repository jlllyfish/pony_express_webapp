import os

import requests
from dotenv import load_dotenv

load_dotenv()

API_URL = os.environ.get(
    "DN_API_URL", "https://demarche.numerique.gouv.fr/api/v2/graphql"
)
API_TOKEN = os.environ["DN_API_TOKEN"]
HEADERS = {"Content-Type": "application/json", "Authorization": f"Bearer {API_TOKEN}"}
DOSSIER_NUMBER = os.environ["DOSSIER_NUMBER"]

QUERY = """
query($number: Int!) {
  dossier(number: $number) {
    annotations {
      id
      label
      ... on PieceJustificativeChamp {
        files { filename byteSize checksum url }
      }
    }
  }
}
"""

resp = requests.post(
    API_URL,
    headers=HEADERS,
    json={"query": QUERY, "variables": {"number": int(DOSSIER_NUMBER)}},
)
resp.raise_for_status()
data = resp.json()

for a in data["data"]["dossier"]["annotations"]:
    if "Contrat pédagogique" in a["label"]:
        print(a)
