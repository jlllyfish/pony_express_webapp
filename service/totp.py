"""
Double authentification par code à usage unique (TOTP, RFC 6238).

- Secret par utilisateur, chiffré en base (Fernet) avec TOTP_CLE, ou à défaut une clé
  dérivée de SECRET_KEY (changer SECRET_KEY oblige alors chacun à réenrôler son téléphone).
- Un code n'est accepté qu'une fois (on mémorise le dernier pas de 30 s utilisé).
- 10 codes de secours à usage unique, stockés hachés, en cas de téléphone perdu.
"""

import base64
import hashlib
import json
import os
import secrets
import time

import pyotp
import segno
from cryptography.fernet import Fernet, InvalidToken
from werkzeug.security import check_password_hash, generate_password_hash

EMETTEUR = "Pony Express"
NB_CODES_SECOURS = 10


def obligatoire() -> bool:
    return os.environ.get("TOTP_OBLIGATOIRE", "1") == "1"


def _fernet() -> Fernet:
    cle = os.environ.get("TOTP_CLE")
    if not cle:
        derivee = hashlib.sha256(("totp:" + os.environ.get("SECRET_KEY", "")).encode()).digest()
        cle = base64.urlsafe_b64encode(derivee).decode()
    return Fernet(cle.encode() if isinstance(cle, str) else cle)


def nouveau_secret() -> str:
    return pyotp.random_base32()


def chiffrer(secret: str) -> str:
    return _fernet().encrypt(secret.encode()).decode()


def dechiffrer(secret_chiffre: str) -> str | None:
    try:
        return _fernet().decrypt(secret_chiffre.encode()).decode()
    except (InvalidToken, ValueError):
        return None


def qr_svg(secret: str, email: str) -> str:
    """QR code à scanner avec l'application d'authentification (SVG inline)."""
    uri = pyotp.TOTP(secret).provisioning_uri(name=email, issuer_name=EMETTEUR)
    # omitsize : viewBox sans largeur/hauteur fixes, la taille est donnée par le CSS (sinon l'image est rognée)
    # bord de 4 modules (zone de silence exigée par la norme), bleu foncé sur blanc : contraste suffisant pour toutes les applis
    return segno.make(uri, error="m").svg_inline(dark="#16149a", light="#ffffff", border=4, omitsize=True)


def secret_lisible(secret: str) -> str:
    """Secret groupé par 4 caractères, pour une saisie manuelle."""
    return " ".join(secret[i:i + 4] for i in range(0, len(secret), 4))


def verifier(secret: str, code: str, dernier_pas: int | None) -> int | None:
    """Pas de temps du code s'il est valide et pas encore utilisé, sinon None.
    Tolère ±30 s de décalage d'horloge."""
    code = "".join(c for c in (code or "") if c.isdigit())
    if len(code) != 6:
        return None
    totp = pyotp.TOTP(secret)
    maintenant = int(time.time())
    for decalage in (0, -1, 1):
        instant = maintenant + decalage * totp.interval
        if secrets.compare_digest(totp.at(instant), code):
            pas = instant // totp.interval
            if dernier_pas is not None and pas <= dernier_pas:
                return None  # code déjà utilisé (rejeu)
            return pas
    return None


def generer_codes_secours() -> tuple[list[str], str]:
    """(codes en clair à afficher une fois, JSON des empreintes à stocker)."""
    codes = [f"{secrets.token_hex(2)}-{secrets.token_hex(2)}" for _ in range(NB_CODES_SECOURS)]
    return codes, json.dumps([generate_password_hash(c) for c in codes])


def utiliser_code_secours(code: str, empreintes_json: str | None) -> str | None:
    """Nouveau JSON des empreintes (code consommé) si le code de secours est valide, sinon None."""
    code = (code or "").strip().lower()
    if not empreintes_json or len(code) != 9 or code[4] != "-":
        return None
    empreintes = json.loads(empreintes_json)
    for i, empreinte in enumerate(empreintes):
        if check_password_hash(empreinte, code):
            return json.dumps(empreintes[:i] + empreintes[i + 1:])
    return None


def codes_secours_restants(empreintes_json: str | None) -> int:
    return len(json.loads(empreintes_json)) if empreintes_json else 0
