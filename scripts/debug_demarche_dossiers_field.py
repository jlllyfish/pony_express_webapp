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
  __type(name: "Demarche") {
    fields(includeDeprecated: false) {
      name
      args { name type { kind name ofType { kind name ofType { kind name } } } }
      type {
        kind
        name
        ofType { kind name }
      }
    }
  }
}
"""
resp = requests.post(API_URL, headers=HEADERS, json={"query": QUERY})
resp.raise_for_status()
fields = resp.json()["data"]["__type"]["fields"]
for f in fields:
    if f["name"] == "dossiers":
        print("Type de retour :", f["type"])
        print("Arguments :")
        for a in f["args"]:
            print(" -", a["name"], ":", a["type"])
