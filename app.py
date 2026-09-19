import os

from dotenv import load_dotenv

load_dotenv()  # doit précéder les imports ci-dessous : ils lisent os.environ au chargement

from flask import Flask, jsonify, render_template, request, send_file

from service.dn import envoyer_kit_pedagogique, synchroniser_statuts_pj_avec_dn
from service.dossiers import list_dossiers, list_etablissements
from service.generation import generate_kit_pedagogique

app = Flask(__name__)

# Pas de base de données : le doc Grist est la source de vérité.
# Ce cache mémoire évite de retaper Grist à chaque requête ; un restart le reconstruit.
_cache = {"dossiers": None}


def get_dossiers(refresh: bool = False):
    if _cache["dossiers"] is None or refresh:
        _cache["dossiers"] = list_dossiers()
    return _cache["dossiers"]


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/api/dossiers")
def api_dossiers():
    """Liste des dossiers + valeurs distinctes pour le filtre établissement."""
    dossiers = get_dossiers(refresh=request.args.get("refresh") == "1")
    return jsonify(
        {
            "dossiers": dossiers,
            "etablissements": list_etablissements(dossiers),
        }
    )


@app.post("/api/dossiers/sync-dn")
def api_sync_dn():
    """Vérifie en un seul passage groupé si le statut Grist correspond à la réalité DN, corrige si besoin."""
    try:
        resultat = synchroniser_statuts_pj_avec_dn()
    except Exception as exc:  # noqa: BLE001
        return jsonify({"error": str(exc)}), 500
    return jsonify(resultat)


@app.post("/api/kits/generate")
def api_generate():
    """Génère le kit pédagogique pour les dossiers sélectionnés (liste de dossier_number)."""
    payload = request.get_json(force=True) or {}
    dossier_numbers = payload.get("dossier_numbers", [])
    if not dossier_numbers:
        return jsonify({"error": "aucun dossier sélectionné"}), 400
    try:
        results = generate_kit_pedagogique(dossier_numbers)
    except Exception as exc:  # noqa: BLE001 - on renvoie l'erreur telle quelle pour debug en V1
        return jsonify({"error": str(exc)}), 500
    return jsonify({"generated": list(results.keys())})


@app.get("/api/kits/<dossier_number>/download")
def api_download(dossier_number):
    try:
        results = generate_kit_pedagogique([dossier_number])
    except Exception as exc:  # noqa: BLE001
        return jsonify({"error": str(exc)}), 500
    path = results.get(dossier_number) or results.get(int(dossier_number))
    if not path:
        return jsonify(
            {"error": "dossier introuvable ou filtré par should_be_exported"}
        ), 404
    return send_file(path, as_attachment=True)


@app.post("/api/kits/send")
def api_send():
    """Régénère le kit (données fraîches) puis l'envoie vers DN pour chaque dossier sélectionné."""
    payload = request.get_json(force=True) or {}
    dossier_numbers = payload.get("dossier_numbers", [])
    if not dossier_numbers:
        return jsonify({"error": "aucun dossier sélectionné"}), 400

    try:
        pdf_paths = generate_kit_pedagogique(dossier_numbers)
    except Exception as exc:  # noqa: BLE001
        return jsonify({"error": f"génération échouée : {exc}"}), 500

    sent, failed = [], {}
    for dossier_number in dossier_numbers:
        path = pdf_paths.get(dossier_number) or pdf_paths.get(str(dossier_number))
        if not path:
            failed[dossier_number] = "PDF non généré (filtré par should_be_exported ?)"
            continue
        try:
            envoyer_kit_pedagogique(dossier_number, path)
            sent.append(dossier_number)
        except Exception as exc:  # noqa: BLE001
            failed[dossier_number] = str(exc)

    status_code = 200 if not failed else 207  # 207 Multi-Status : succès partiel
    return jsonify({"sent": sent, "failed": failed}), status_code


if __name__ == "__main__":
    app.run(debug=True, port=int(os.environ.get("PORT", 5000)))
