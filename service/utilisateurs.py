"""
Comptes utilisateurs : table « utilisateurs » (PostgreSQL sur Scalingo, SQLite en local).

- mot de passe jamais stocké en clair : empreinte scrypt (werkzeug)
- lien « mot de passe oublié » signé et valable 1 h, sans table de jetons :
  il contient une empreinte du hash actuel, donc il devient invalide dès que
  le mot de passe change (usage unique)

Base : DATABASE_URL (Scalingo la fournit avec l'addon PostgreSQL), sinon
SQLite dans instance/pony_express.db.
"""

import hashlib
import os
from datetime import datetime, timezone
from pathlib import Path

from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from sqlalchemy import Boolean, Column, DateTime, Integer, MetaData, String, Table, create_engine, func, select
from werkzeug.security import check_password_hash, generate_password_hash

DUREE_LIEN_SECONDES = 3600
LONGUEUR_MIN_MDP = 12

metadata = MetaData()
utilisateurs = Table(
    "utilisateurs",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("email", String(254), unique=True, nullable=False),
    Column("mot_de_passe", String(255), nullable=False),
    Column("actif", Boolean, nullable=False, default=True),
    Column("cree_le", DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)),
    Column("derniere_connexion", DateTime(timezone=True)),
)

_engine = None


def _url_base() -> str:
    url = os.environ.get("DATABASE_URL") or os.environ.get("SCALINGO_POSTGRESQL_URL")
    if url:
        # Scalingo / Heroku : postgres:// -> pilote psycopg 3
        for prefixe in ("postgres://", "postgresql://"):
            if url.startswith(prefixe):
                return "postgresql+psycopg://" + url[len(prefixe):]
        return url
    dossier = Path(__file__).resolve().parent.parent / "instance"
    dossier.mkdir(exist_ok=True)
    return f"sqlite:///{dossier / 'pony_express.db'}"


def engine():
    global _engine
    if _engine is None:
        _engine = create_engine(_url_base(), pool_pre_ping=True)
        metadata.create_all(_engine)  # crée la table au premier lancement
    return _engine


def normaliser(email: str) -> str:
    return (email or "").strip().lower()


def prenom_depuis_email(email: str) -> str:
    """« jean-marc.dupont@… » -> « Jean-Marc » (partie avant le premier point)."""
    local = normaliser(email).split("@")[0]
    brut = local.split(".")[0] if "." in local else local
    return "-".join(p.capitalize() for p in brut.split("-") if p) or "à vous"


def verifier_mot_de_passe_robuste(mdp: str) -> str | None:
    """Message d'erreur si le mot de passe est trop faible, sinon None."""
    if len(mdp or "") < LONGUEUR_MIN_MDP:
        return f"Le mot de passe doit contenir au moins {LONGUEUR_MIN_MDP} caractères."
    return None


# --- Lecture / écriture -------------------------------------------------------

def trouver(email: str) -> dict | None:
    with engine().connect() as cx:
        ligne = cx.execute(select(utilisateurs).where(utilisateurs.c.email == normaliser(email))).mappings().first()
    return dict(ligne) if ligne else None


def trouver_par_id(uid: int) -> dict | None:
    with engine().connect() as cx:
        ligne = cx.execute(select(utilisateurs).where(utilisateurs.c.id == uid)).mappings().first()
    return dict(ligne) if ligne else None


def lister() -> list[dict]:
    with engine().connect() as cx:
        return [dict(l) for l in cx.execute(select(utilisateurs).order_by(utilisateurs.c.email)).mappings()]


def creer(email: str, mot_de_passe: str) -> None:
    erreur = verifier_mot_de_passe_robuste(mot_de_passe)
    if erreur:
        raise ValueError(erreur)
    if "@" not in normaliser(email):
        raise ValueError("Adresse e-mail invalide.")
    if trouver(email):
        raise ValueError("Un compte existe déjà pour cette adresse.")
    with engine().begin() as cx:
        cx.execute(utilisateurs.insert().values(
            email=normaliser(email), mot_de_passe=generate_password_hash(mot_de_passe), actif=True))


def changer_mot_de_passe(uid: int, mot_de_passe: str) -> None:
    erreur = verifier_mot_de_passe_robuste(mot_de_passe)
    if erreur:
        raise ValueError(erreur)
    with engine().begin() as cx:
        cx.execute(utilisateurs.update().where(utilisateurs.c.id == uid)
                   .values(mot_de_passe=generate_password_hash(mot_de_passe)))


def activer(email: str, actif: bool) -> bool:
    with engine().begin() as cx:
        r = cx.execute(utilisateurs.update().where(utilisateurs.c.email == normaliser(email)).values(actif=actif))
    return r.rowcount > 0


def supprimer(email: str) -> bool:
    with engine().begin() as cx:
        r = cx.execute(utilisateurs.delete().where(utilisateurs.c.email == normaliser(email)))
    return r.rowcount > 0


def authentifier(email: str, mot_de_passe: str) -> dict | None:
    """Utilisateur si e-mail + mot de passe corrects et compte actif, sinon None."""
    u = trouver(email)
    if not u or not u["actif"] or not check_password_hash(u["mot_de_passe"], mot_de_passe or ""):
        return None
    with engine().begin() as cx:
        cx.execute(utilisateurs.update().where(utilisateurs.c.id == u["id"])
                   .values(derniere_connexion=func.now()))
    return u


# --- Lien de réinitialisation ---------------------------------------------------

def _serialiseur(secret: str) -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(secret, salt="reinitialisation-mot-de-passe")


def _empreinte(u: dict) -> str:
    return hashlib.sha256(u["mot_de_passe"].encode()).hexdigest()[:16]


def jeton_reinitialisation(u: dict, secret: str) -> str:
    return _serialiseur(secret).dumps({"id": u["id"], "e": _empreinte(u)})


def utilisateur_du_jeton(jeton: str, secret: str) -> dict | None:
    """Utilisateur si le lien est valide, non expiré et pas encore utilisé."""
    try:
        data = _serialiseur(secret).loads(jeton, max_age=DUREE_LIEN_SECONDES)
    except (BadSignature, SignatureExpired):
        return None
    u = trouver_par_id(data.get("id"))
    if not u or not u["actif"] or data.get("e") != _empreinte(u):
        return None
    return u
