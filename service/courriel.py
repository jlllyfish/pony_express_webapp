"""
Envoi d'e-mails (lien « mot de passe oublié »).

Réglages par variables d'environnement :
    SMTP_HOST, SMTP_PORT (587 par défaut), SMTP_USER, SMTP_PASSWORD,
    SMTP_FROM (adresse d'expéditeur), SMTP_TLS (starttls par défaut, « ssl » ou « non »)

Sans SMTP_HOST (développement), le message n'est pas envoyé : il est écrit dans les logs.
"""

import logging
import os
import smtplib
import ssl
from email.message import EmailMessage

logger = logging.getLogger(__name__)


def envoyer(destinataire: str, sujet: str, texte: str) -> None:
    hote = os.environ.get("SMTP_HOST")
    if not hote:
        logger.warning("E-mail NON envoyé (SMTP_HOST absent) à %s — %s\n%s", destinataire, sujet, texte)
        return

    msg = EmailMessage()
    msg["From"] = os.environ.get("SMTP_FROM") or os.environ.get("SMTP_USER", "")
    msg["To"] = destinataire
    msg["Subject"] = sujet
    msg.set_content(texte)

    port = int(os.environ.get("SMTP_PORT", "587"))
    mode = os.environ.get("SMTP_TLS", "starttls").lower()
    contexte = ssl.create_default_context()
    if mode == "ssl":
        serveur = smtplib.SMTP_SSL(hote, port, context=contexte, timeout=20)
    else:
        serveur = smtplib.SMTP(hote, port, timeout=20)
        if mode != "non":
            serveur.starttls(context=contexte)
    with serveur:
        if os.environ.get("SMTP_USER"):
            serveur.login(os.environ["SMTP_USER"], os.environ.get("SMTP_PASSWORD", ""))
        serveur.send_message(msg)
