"""
Compilation Typst dans le processus Python (paquet PyPI `typst`), à la place
du binaire `typst` appelé en ligne de commande par Pony_express : Scalingo ne
fournit pas ce binaire, le paquet PyPI embarque le compilateur.

Chaque génération écrit dans son propre sous-dossier (uuid) de `generated/` :
deux utilisateurs qui génèrent le même document en même temps ne s'écrasent pas.
Les PDF ne servent que le temps d'une requête (téléchargement ou envoi DN) : la route
les supprime ensuite avec `supprimer`, et `purger_anciens` balaie les restes (requête
interrompue, erreur) à chaque génération. Aucune donnée d'apprenant ne reste sur le disque.
"""

import os
import shutil
import time
import uuid

from pathlib import Path

import typst

from pony_express.service.pdf import ROOT_PATH, create_call_to_template_string, fonts_path

GENERATED_PATH = ROOT_PATH / "generated"


def generate_pdf(data: dict, template_folder: str, template_file_name: str, template_name: str,
                 generated_file_name: str) -> str:
    """Même signature que pony_express.service.pdf.generate_pdf ; retourne le chemin du PDF."""
    purger_anciens()
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


def supprimer(*chemins) -> None:
    """Supprime le dossier de génération de chaque PDF (jamais en dehors de generated/)."""
    for chemin in chemins:
        if not chemin:
            continue
        dossier = Path(chemin).resolve().parent
        if dossier.parent == GENERATED_PATH.resolve():
            shutil.rmtree(dossier, ignore_errors=True)


def purger_anciens(age_max_secondes: int = 15 * 60) -> None:
    """Filet de sécurité : supprime les dossiers de génération oubliés."""
    if not GENERATED_PATH.exists():
        return
    limite = time.time() - age_max_secondes
    for dossier in GENERATED_PATH.iterdir():
        try:
            if dossier.is_dir() and dossier.stat().st_mtime < limite:
                shutil.rmtree(dossier, ignore_errors=True)
        except FileNotFoundError:
            pass  # supprimé entre-temps par une autre requête
