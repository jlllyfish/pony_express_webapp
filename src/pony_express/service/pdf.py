import os
import pathlib
import subprocess

ROOT_PATH = pathlib.Path(__file__).resolve().parents[3]
generated_file_path = str(ROOT_PATH / "generated") + os.sep
fonts_path = str(ROOT_PATH / "templates")

def generate_pdf(data: dict, template_folder: str, template_file_name: str, template_name: str,
                 generated_file_name: str):
    os.makedirs(generated_file_path, exist_ok=True)
    generated_file = generated_file_path + generated_file_name
    typ_file = generated_file + ".typ"
    pdf_file = generated_file + ".pdf"
    call_to_template = create_call_to_template_string(template_name, data)
    # import relatif en "/" : pas de chemin "D:\..." (échappements) dans la chaîne Typst
    template_path = os.path.join(template_folder, template_file_name + ".typ")
    import_path = os.path.relpath(template_path, generated_file_path).replace(os.sep, "/")
    with open(typ_file, "w", encoding="utf-8") as file:
        file.write(f'#import "{import_path}": *\n' + call_to_template)
    subprocess.run(["typst", "compile", "--root", str(ROOT_PATH), typ_file, "--font-path", fonts_path], check=True)
    os.remove(typ_file)  # conservé si typst échoue, pour debug
    return pdf_file


def create_call_to_template_string(template_name, data):
    call_to_template = f"#{template_name}("
    for key, value in data.items():
        param = f"{key}:{to_typst_string(value)},"
        call_to_template += param
    call_to_template += ")"
    return call_to_template

def to_typst_string(param: any) -> str :
    if isinstance(param, list):
      return list_to_string(param)
    elif isinstance(param, dict):
      return dict_to_string(param)
    elif isinstance(param, tuple):
      return list_to_string(param)
    elif param is None:
      return '""'
    else :
      return '"' + str(param).replace('\\', '\\\\').replace('"', '\\"') + '"'

def list_to_string(py_list: list | tuple) -> str:
    typst_list = "("
    for item in py_list:
        typst_list += to_typst_string(item)
        typst_list += ","
    typst_list += ")"
    return typst_list

def dict_to_string(py_dict: dict) -> str:
    typst_dict = "("
    for key, value in py_dict.items():
        typst_dict += key + ":" + to_typst_string(value)
        typst_dict += ","
    typst_dict += ")"
    return typst_dict

