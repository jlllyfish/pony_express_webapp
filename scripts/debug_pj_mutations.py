import os

import requests
from dotenv import load_dotenv

load_dotenv()

API_URL = os.environ.get(
    "DN_API_URL", "https://demarche.numerique.gouv.fr/api/v2/graphql"
)
API_TOKEN = os.environ["DN_API_TOKEN"]
HEADERS = {"Content-Type": "application/json", "Authorization": f"Bearer {API_TOKEN}"}

QUERY = """
query {
  __schema {
    mutationType {
      fields { name }
    }
  }
}
"""

resp = requests.post(API_URL, headers=HEADERS, json={"query": QUERY})
resp.raise_for_status()
data = resp.json()
names = [f["name"] for f in data["data"]["__schema"]["mutationType"]["fields"]]

keywords = [
    "annotation",
    "piece",
    "justificat",
    "fichier",
    "attachment",
    "supprim",
    "retir",
    "detach",
    "delete",
]
matches = [n for n in names if any(k in n.lower() for k in keywords)]

print(f"{len(names)} mutations au total")
print("Mutations pertinentes pour les pièces jointes/annotations :")
for m in sorted(matches):
    print(" -", m)
