import os
import sys

import requests
from dotenv import load_dotenv

load_dotenv()

API_URL = os.environ.get(
    "DN_API_URL", "https://demarche.numerique.gouv.fr/api/v2/graphql"
)
API_TOKEN = os.environ["DN_API_TOKEN"]
HEADERS = {"Content-Type": "application/json", "Authorization": f"Bearer {API_TOKEN}"}

QUERY = """
query($number: Int!) {
  dossier(number: $number) {
    annotations { id label }
  }
}
"""

for number in sys.argv[1:]:
    resp = requests.post(
        API_URL,
        headers=HEADERS,
        json={"query": QUERY, "variables": {"number": int(number)}},
    )
    resp.raise_for_status()
    data = resp.json()
    print(f"--- dossier {number} ---")
    if "errors" in data:
        print("erreurs:", data["errors"])
        continue
    for a in data["data"]["dossier"]["annotations"]:
        print(a)
