import os

import requests
from dotenv import load_dotenv

load_dotenv()

API_URL = os.environ.get(
    "DN_API_URL", "https://demarche.numerique.gouv.fr/api/v2/graphql"
)
API_TOKEN = os.environ["DN_API_TOKEN"]
HEADERS = {"Content-Type": "application/json", "Authorization": f"Bearer {API_TOKEN}"}

INTROSPECTION = """
query TypeIntrospection($name: String!) {
  __type(name: $name) {
    name
    kind
    inputFields {
      name
      type { kind name ofType { kind name ofType { kind name ofType { kind name } } } }
    }
    fields {
      name
      type { kind name ofType { kind name ofType { kind name } } }
    }
    enumValues { name }
  }
}
"""


def unwrap(t):
    """Retourne (nom_du_type_de_base, description_lisible) en dépilant NON_NULL/LIST."""
    wrappers = []
    while t and t.get("kind") in ("NON_NULL", "LIST"):
        wrappers.append(t["kind"])
        t = t.get("ofType")
    name = t.get("name") if t else "?"
    label = name
    for w in reversed(wrappers):
        label = f"[{label}]" if w == "LIST" else f"{label}!"
    return name, label


def describe(name, seen=None, indent=0):
    seen = seen or set()
    if name in seen or indent > 2:
        return
    seen.add(name)

    resp = requests.post(
        API_URL,
        headers=HEADERS,
        json={"query": INTROSPECTION, "variables": {"name": name}},
    )
    resp.raise_for_status()
    data = resp.json()
    t = data.get("data", {}).get("__type")
    pad = "  " * indent
    if not t:
        print(f"{pad}{name} : introuvable dans le schéma")
        return

    print(f"{pad}{name} ({t['kind']})")
    if t.get("enumValues"):
        print(f"{pad}  valeurs : {[v['name'] for v in t['enumValues']]}")

    to_recurse = []
    for f in t.get("inputFields") or t.get("fields") or []:
        base_name, label = unwrap(f["type"])
        print(f"{pad}  - {f['name']}: {label}")
        if base_name and base_name not in ("String", "ID", "Int", "Float", "Boolean"):
            to_recurse.append(base_name)

    for child in to_recurse:
        describe(child, seen, indent + 1)


if __name__ == "__main__":
    describe("DossierModifierAnnotationsInput")
    print()
    describe("DossierModifierAnnotationsPayload")
