import os

import requests
from dotenv import load_dotenv

load_dotenv()

API_URL = os.environ.get(
    "DN_API_URL", "https://demarche.numerique.gouv.fr/api/v2/graphql"
)
API_TOKEN = os.environ["DN_API_TOKEN"]
HEADERS = {"Content-Type": "application/json", "Authorization": f"Bearer {API_TOKEN}"}

QUERY_ROOT = """
query {
  __schema {
    queryType { fields { name } }
  }
}
"""
resp = requests.post(API_URL, headers=HEADERS, json={"query": QUERY_ROOT})
resp.raise_for_status()
print(
    "Champs de la query racine :",
    [f["name"] for f in resp.json()["data"]["__schema"]["queryType"]["fields"]],
)

QUERY_TYPE = """
query($name: String!) {
  __type(name: $name) {
    fields { name type { kind name ofType { kind name } } }
  }
}
"""
resp = requests.post(
    API_URL,
    headers=HEADERS,
    json={"query": QUERY_TYPE, "variables": {"name": "Demarche"}},
)
resp.raise_for_status()
data = resp.json()
t = data.get("data", {}).get("__type")
if t:
    print("\nChamps du type Demarche :")
    for f in t["fields"]:
        print(" -", f["name"])
else:
    print("\nType Demarche introuvable :", data)
