r"""
Liste les colonnes (identifiant + libellé) des tables Grist utiles au mapping, dans colonnes_grist.txt.

Usage (PowerShell, depuis le dossier du projet) :
    .\lancer.ps1 -colonnes
    .\lancer.ps1 -colonnes -tables "Demarche_128447_annotations,Etablissements"
    .\lancer.ps1 -colonnes -tables "Demarche_156966"     (toutes les tables qui commencent par ce nom)
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))
from pony_express.service.grist import GristService  # noqa: E402

DEFAUT = [
    os.environ.get("GRIST_TABLE", "Demarche_128447_annotations"),
    "Demarche_128447_champs",
    "Etablissements",
]

tables = sys.argv[1].split(",") if len(sys.argv) > 1 and sys.argv[1] else DEFAUT
grist = GristService(os.environ["GRIST_DOC_ID"], os.environ["GRIST_TEAM_SITE"], os.environ["GRIST_SERVER"]).grist

# un nom incomplet (ex : Demarche_156966) = toutes les tables du document qui commencent par ce nom
status, toutes = grist.list_tables()
existantes = [t["id"] for t in toutes] if status == 200 else []
etendues = []
for table in tables:
    table = table.strip()
    trouvees = [t for t in existantes if t == table] or [t for t in existantes if t.startswith(table)]
    etendues += trouvees or [table]
tables = list(dict.fromkeys(etendues))

lignes = []
for table in tables:
    table = table.strip()
    status, cols = grist.list_cols(table)
    if status != 200:
        lignes.append(f"## {table} : lecture impossible (HTTP {status})")
        continue
    lignes.append(f"## {table} ({len(cols)} colonnes)")
    for col in cols:
        label = col.get("fields", {}).get("label", "")
        lignes.append(f"{col['id']}\t{label}")
    lignes.append("")

sortie = os.path.join(os.path.dirname(__file__), "colonnes_grist.txt")
with open(sortie, "w", encoding="utf-8") as f:
    f.write("\n".join(lignes))
print("\n".join(lignes))
print(f"\n-> {sortie}")
