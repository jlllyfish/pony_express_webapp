import os

import requests
from dotenv import load_dotenv

load_dotenv()

API_URL = os.environ.get(
    "DN_API_URL", "https://demarche.numerique.gouv.fr/api/v2/graphql"
)
API_TOKEN = os.environ["DN_API_TOKEN"]
HEADERS = {"Content-Type": "application/json", "Authorization": f"Bearer {API_TOKEN}"}

QUERY_TYPES = """
query {
  __type(name: "Champ") {
    possibleTypes { name }
  }
}
"""

resp = requests.post(API_URL, headers=HEADERS, json={"query": QUERY_TYPES})
resp.raise_for_status()
types = resp.json()["data"]["__type"]["possibleTypes"]
print("Types implémentant Champ :", [t["name"] for t in types])

QUERY_FIELDS = """
query($name: String!) {
  __type(name: $name) {
    fields { name type { kind name ofType { kind name } } }
  }
}
"""

for t in types:
    if (
        "piece" in t["name"].lower()
        or "justif" in t["name"].lower()
        or "file" in t["name"].lower()
    ):
        resp = requests.post(
            API_URL,
            headers=HEADERS,
            json={"query": QUERY_FIELDS, "variables": {"name": t["name"]}},
        )
        resp.raise_for_status()
        fields = resp.json()["data"]["__type"]["fields"]
        print(f"\n{t['name']} :")
        for f in fields:
            print(" -", f["name"])
