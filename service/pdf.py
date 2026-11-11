"""
Compilation Typst dans le processus Python (paquet PyPI `typst`), à la place
du binaire `typst` appelé en ligne de commande par Pony_express : Scalingo ne
fournit pas ce binaire, le paquet PyPI embarque le compilateur.

Chaque génération écrit dans son propre sous-dossier (uuid) de `generated/` :
deux utilisateurs qui génèrent le même document en même temps ne s'écrasent pas.
Le nettoyage de ces dossiers viendra à l'étape 4 du plan.
"""

import os
import uuid

import typst

from pony_express.service.pdf import ROOT_PATH, create_call_to_template_string, fonts_path

GENERATED_PATH = ROOT_PATH / "generated"


def generate_pdf(data: dict, template_folder: str, template_file_name: str, template_name: str,
                 generated_file_name: str) -> str:
    """Même signature que pony_express.service.pdf.generate_pdf ; retourne le chemin du PDF."""
    dossier = GENERATED_PATH / uuid.uuid4().hex
    dossier.mkdir(parents=True, exist_ok=True)
    typ_file = dossier / f"{generated_file_name}.typ"
    pdf_file = dossier / f"{generated_file_name}.pdf"

    template_path = os.path.join(template_folder, template_file_name + ".typ")
    # import relatif en "/" : pas de chemin "D:\..." (échappements) dans la chaîne Typst
    import_path = os.path.relpath(template_path, dossier).replace(os.sep, "/")
    typ_file.write_text(
        f'#import "{import_path}": *\n' + create_call_to_template_string(template_name, data),
        encoding="utf-8",
    )
    typst.compile(str(typ_file), output=str(pdf_file), root=str(ROOT_PATH), font_paths=[fonts_path])
    typ_file.unlink()  # conservé si la compilation échoue, pour debug
    return str(pdf_file)
