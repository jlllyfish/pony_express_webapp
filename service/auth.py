"""
Authentification : connexion, déconnexion, mot de passe oublié, gestion des comptes.

- Toutes les pages et API exigent d'être connecté, sauf la connexion et le
  mot de passe oublié (et les fichiers statiques). Une API appelée sans session
  répond 401 ; une page redirige vers /connexion.
- Formulaires protégés par un jeton CSRF stocké en session.
- 5 essais de connexion ratés par adresse et par IP en 15 min, puis blocage.
- Pas d'inscription libre. Les administrateurs gèrent les comptes sur /admin/utilisateurs
  (invitation par lien valable 7 jours, activation, rôle, suppression), ou en ligne de commande :
      flask --app app utilisateurs ajouter prenom.nom@exemple.fr
      flask --app app utilisateurs lister
      flask --app app utilisateurs desactiver / activer / supprimer <email>
  Sur Scalingo : scalingo --app <app> run flask --app app utilisateurs ajouter …
"""

import logging
import os
import secrets
import time
from collections import defaultdict, deque
from datetime import timedelta, timezone
from zoneinfo import ZoneInfo

import click
from flask import (Blueprint, abort, current_app, flash, g, jsonify, redirect, render_template,
                   request, session, url_for)

from service import courriel, journal, utilisateurs as comptes

bp = Blueprint("auth", __name__)

PAGES_PUBLIQUES = {"auth.connexion", "auth.mot_de_passe_oublie", "auth.reinitialiser", "auth.bienvenue",
                   "static", "favicon", "health"}
ESSAIS_MAX, FENETRE_ESSAIS = 5, 15 * 60
_essais: dict = defaultdict(deque)


# --- CSRF ---------------------------------------------------------------------

def jeton_csrf() -> str:
    if "csrf" not in session:
        session["csrf"] = secrets.token_urlsafe(32)
    return session["csrf"]


def _verifier_csrf():
    attendu = session.get("csrf")
    if not attendu or not secrets.compare_digest(attendu, request.form.get("csrf", "")):
        abort(400, "Formulaire expiré : rechargez la page.")


# --- Limitation des essais ----------------------------------------------------

def _bloque(cle: str) -> bool:
    file = _essais[cle]
    while file and time.time() - file[0] > FENETRE_ESSAIS:
        file.popleft()
    return len(file) >= ESSAIS_MAX


def _echec(*cles):
    for cle in cles:
        _essais[cle].append(time.time())


# --- Garde globale ------------------------------------------------------------

def init_app(app):
    app.register_blueprint(bp)
    app.config.update(
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        # cookie réservé au HTTPS (Scalingo) ; SESSION_COOKIE_SECURE=0 pour du HTTP local hors mode debug
        SESSION_COOKIE_SECURE=os.environ.get("SESSION_COOKIE_SECURE", "0" if app.debug else "1") == "1",
        PERMANENT_SESSION_LIFETIME=timedelta(hours=12),
    )
    app.jinja_env.globals["csrf"] = jeton_csrf

    @app.before_request
    def exiger_connexion():
        g.utilisateur = None
        uid = session.get("uid")
        if uid:
            u = comptes.trouver_par_id(uid)
            if u and u["actif"]:
                g.utilisateur = u
            else:
                session.clear()
        if g.utilisateur or request.endpoint in PAGES_PUBLIQUES:
            return None
        if request.path.startswith("/api/"):
            return jsonify({"error": "Session expirée : reconnectez-vous."}), 401
        return redirect(url_for("auth.connexion", suivant=request.path))

    app.cli.add_command(cli_utilisateurs)
    _creer_premier_compte()


def _creer_premier_compte():
    """Amorçage sans terminal : si PREMIER_COMPTE contient un e-mail et qu'aucun compte
    n'existe, crée ce compte avec un mot de passe aléatoire inconnu. On définit ensuite
    le sien via « Mot de passe oublié » (lien envoyé par e-mail, ou écrit dans les logs)."""
    email = os.environ.get("PREMIER_COMPTE", "").strip()
    if not email or comptes.lister():
        return
    comptes.creer_invite(email, admin=True)
    logging.getLogger(__name__).warning(
        "Premier compte créé : %s. Utilisez « Mot de passe oublié » pour définir le mot de passe, "
        "puis supprimez la variable PREMIER_COMPTE.", comptes.normaliser(email)
    )


# --- Pages --------------------------------------------------------------------

@bp.route("/connexion", methods=["GET", "POST"])
def connexion():
    if request.method == "POST":
        _verifier_csrf()
        email = comptes.normaliser(request.form.get("email"))
        ip = request.headers.get("X-Forwarded-For", request.remote_addr or "").split(",")[0].strip()
        if _bloque(f"email:{email}") or _bloque(f"ip:{ip}"):
            flash("Trop de tentatives : réessayez dans 15 minutes.", "erreur")
            return render_template("connexion.html", email=email), 429
        u = comptes.authentifier(email, request.form.get("mot_de_passe", ""))
        if not u:
            _echec(f"email:{email}", f"ip:{ip}")
            flash("Adresse e-mail ou mot de passe incorrect.", "erreur")
            return render_template("connexion.html", email=email), 401
        session.clear()
        session.permanent = True
        session["uid"] = u["id"]
        session["accueil"] = True  # toast « Hay Prénom ! » au prochain affichage
        suivant = request.args.get("suivant", "")
        return redirect(suivant if suivant.startswith("/") and not suivant.startswith("//") else url_for("index"))
    if g.get("utilisateur"):
        return redirect(url_for("index"))
    return render_template("connexion.html", email="")


@bp.post("/deconnexion")
def deconnexion():
    _verifier_csrf()
    session.clear()
    return redirect(url_for("auth.connexion"))


@bp.route("/mot-de-passe-oublie", methods=["GET", "POST"])
def mot_de_passe_oublie():
    if request.method == "POST":
        _verifier_csrf()
        email = comptes.normaliser(request.form.get("email"))
        u = comptes.trouver(email)
        if u and u["actif"]:
            lien = url_for("auth.reinitialiser", jeton=comptes.jeton_reinitialisation(u, current_app.secret_key),
                           _external=True)
            courriel.envoyer(
                email,
                "Pony Express : réinitialisation du mot de passe",
                f"Bonjour {comptes.prenom_depuis_email(email)},\n\n"
                f"Pour choisir un nouveau mot de passe, ouvrez ce lien (valable 1 heure) :\n{lien}\n\n"
                "Si vous n'êtes pas à l'origine de cette demande, ignorez ce message.\n",
            )
        # Même réponse que le compte existe ou non : on ne révèle pas les adresses inscrites
        flash("Si un compte existe pour cette adresse, un lien de réinitialisation vient d'être envoyé.", "info")
        return redirect(url_for("auth.connexion"))
    return render_template("mot_de_passe_oublie.html")


@bp.route("/reinitialiser/<jeton>", methods=["GET", "POST"])
def reinitialiser(jeton):
    return _choisir_mot_de_passe(jeton, "reinitialisation")


@bp.route("/bienvenue/<jeton>", methods=["GET", "POST"])
def bienvenue(jeton):
    """Lien d'invitation (7 jours) : la personne invitée choisit son premier mot de passe."""
    return _choisir_mot_de_passe(jeton, "invitation")


def _choisir_mot_de_passe(jeton: str, usage: str):
    u = comptes.utilisateur_du_jeton(jeton, current_app.secret_key, usage)
    if not u:
        flash("Ce lien n'est plus valide : demandez-en un nouveau.", "erreur")
        return redirect(url_for("auth.mot_de_passe_oublie"))
    invitation = usage == "invitation"
    if request.method == "POST":
        _verifier_csrf()
        mdp, confirmation = request.form.get("mot_de_passe", ""), request.form.get("confirmation", "")
        erreur = comptes.verifier_mot_de_passe_robuste(mdp) or (
            "Les deux mots de passe ne correspondent pas." if mdp != confirmation else None)
        if erreur:
            flash(erreur, "erreur")
            return render_template("reinitialiser.html", invitation=invitation, email=u["email"]), 400
        comptes.changer_mot_de_passe(u["id"], mdp)
        flash("Mot de passe enregistré : vous pouvez vous connecter.", "info")
        return redirect(url_for("auth.connexion"))
    return render_template("reinitialiser.html", invitation=invitation, email=u["email"])


# --- Administration des comptes -------------------------------------------------

@bp.app_template_filter("paris")
def heure_paris(dt) -> str:
    """Date stockée en UTC (naïve en SQLite) -> « jj/mm/aaaa hh:mm » heure de Paris."""
    if not dt:
        return "—"
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(ZoneInfo("Europe/Paris")).strftime("%d/%m/%Y %H:%M")

def _admin_requis():
    if not (g.get("utilisateur") and g.utilisateur.get("admin")):
        abort(403)


def _envoyer_invitation(u: dict) -> dict:
    """Crée un lien d'invitation (7 jours), l'envoie par e-mail si SMTP est configuré,
    et le retourne pour affichage unique à l'administrateur (à transmettre soi-même sinon)."""
    lien = url_for("auth.bienvenue",
                   jeton=comptes.jeton_reinitialisation(u, current_app.secret_key, "invitation"), _external=True)
    envoye = bool(os.environ.get("SMTP_HOST"))
    try:
        courriel.envoyer(
            u["email"],
            "Pony Express : votre accès",
            f"Bonjour {comptes.prenom_depuis_email(u['email'])},\n\n"
            f"Un compte Pony Express vient d'être créé pour vous. Pour choisir votre mot de passe, "
            f"ouvrez ce lien (valable 7 jours) :\n{lien}\n",
        )
    except Exception:  # noqa: BLE001 - SMTP en panne : l'administrateur transmet le lien lui-même
        logging.getLogger(__name__).exception("Envoi de l'invitation impossible")
        envoye = False
    return {"email": u["email"], "lien": lien, "envoye": envoye}


@bp.get("/admin/utilisateurs")
def admin_utilisateurs():
    _admin_requis()
    return render_template(
        "admin_utilisateurs.html",
        comptes=comptes.lister(),
        moi=g.utilisateur["id"],
        invitation=session.pop("invitation", None),
    )


@bp.get("/admin/journal")
def admin_journal():
    _admin_requis()
    filtre_utilisateur = request.args.get("utilisateur") or None
    filtre_resultat = request.args.get("resultat") or None
    return render_template(
        "admin_journal.html",
        entrees=journal.lister(utilisateur=filtre_utilisateur, resultat=filtre_resultat),
        comptes=comptes.lister(),
        filtre_utilisateur=filtre_utilisateur,
        filtre_resultat=filtre_resultat,
    )


@bp.post("/admin/utilisateurs")
def admin_ajouter():
    _admin_requis()
    _verifier_csrf()
    try:
        u = comptes.creer_invite(request.form.get("email", ""), admin=request.form.get("admin") == "1")
    except ValueError as exc:
        flash(str(exc), "erreur")
        return redirect(url_for("auth.admin_utilisateurs"))
    session["invitation"] = _envoyer_invitation(u)
    flash(f"Compte créé : {u['email']}", "info")
    return redirect(url_for("auth.admin_utilisateurs"))


@bp.post("/admin/utilisateurs/<int:uid>/<action>")
def admin_action(uid, action):
    _admin_requis()
    _verifier_csrf()
    u = comptes.trouver_par_id(uid)
    if not u:
        abort(404)
    if uid == g.utilisateur["id"] and action in {"desactiver", "supprimer", "retirer-admin"}:
        flash("Vous ne pouvez pas faire cela sur votre propre compte.", "erreur")
        return redirect(url_for("auth.admin_utilisateurs"))
    if action == "lien":
        session["invitation"] = _envoyer_invitation(u)
        flash(f"Nouveau lien pour {u['email']} (l'ancien reste valable jusqu'au changement de mot de passe).", "info")
    elif action in {"activer", "desactiver"}:
        comptes.activer(u["email"], action == "activer")
        flash(f"Compte {'activé' if action == 'activer' else 'désactivé'} : {u['email']}", "info")
    elif action in {"admin", "retirer-admin"}:
        comptes.definir_admin(u["email"], action == "admin")
        flash(f"{u['email']} : {'administrateur' if action == 'admin' else 'utilisateur'}", "info")
    elif action == "supprimer":
        comptes.supprimer(u["email"])
        flash(f"Compte supprimé : {u['email']}", "info")
    else:
        abort(404)
    return redirect(url_for("auth.admin_utilisateurs"))


def accueil_a_afficher() -> str | None:
    """Prénom à saluer une seule fois après la connexion, sinon None."""
    if g.get("utilisateur") and session.pop("accueil", False):
        return comptes.prenom_depuis_email(g.utilisateur["email"])
    return None


# --- Ligne de commande --------------------------------------------------------

@click.group("utilisateurs", help="Gestion des comptes Pony Express.")
def cli_utilisateurs():
    pass


@cli_utilisateurs.command("ajouter")
@click.argument("email")
@click.option("--admin", is_flag=True, help="Donne accès à la page de gestion des comptes.")
def cli_ajouter(email, admin):
    # click.prompt écrit sur la sortie standard : l'invite s'affiche aussi via `scalingo run`
    # (getpass écrit sur /dev/tty, invisible depuis un terminal Windows)
    mdp = click.prompt("Mot de passe (12 caractères min.)", hide_input=True,
                       confirmation_prompt="Confirmation")
    try:
        comptes.creer(email, mdp, admin=admin)
    except ValueError as exc:
        raise click.ClickException(str(exc))
    click.echo(f"Compte créé : {comptes.normaliser(email)}")


@cli_utilisateurs.command("lister")
def cli_lister():
    for u in comptes.lister():
        etat = ("actif" if u["actif"] else "désactivé") + (" · admin" if u["admin"] else "")
        derniere = u["derniere_connexion"].strftime("%d/%m/%Y %H:%M") if u["derniere_connexion"] else "jamais"
        click.echo(f"{u['email']:<45} {etat:<18} dernière connexion : {derniere}")


@cli_utilisateurs.command("admin")
@click.argument("email")
@click.option("--retirer", is_flag=True, help="Retire le rôle administrateur.")
def cli_admin(email, retirer):
    ok = comptes.definir_admin(email, not retirer)
    click.echo(("Rôle administrateur " + ("retiré." if retirer else "donné.")) if ok else "Compte introuvable.")


@cli_utilisateurs.command("desactiver")
@click.argument("email")
def cli_desactiver(email):
    click.echo("Compte désactivé." if comptes.activer(email, False) else "Compte introuvable.")


@cli_utilisateurs.command("activer")
@click.argument("email")
def cli_activer(email):
    click.echo("Compte activé." if comptes.activer(email, True) else "Compte introuvable.")


@cli_utilisateurs.command("supprimer")
@click.argument("email")
@click.confirmation_option(prompt="Supprimer définitivement ce compte ?")
def cli_supprimer(email):
    click.echo("Compte supprimé." if comptes.supprimer(email) else "Compte introuvable.")
