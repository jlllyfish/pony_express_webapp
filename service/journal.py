"""
Journal des actions (traçabilité) : qui a envoyé ou téléchargé quel document, quand, avec quel résultat.

- Même base que les comptes (PostgreSQL sur Scalingo, SQLite en local).
- Minimisation : on garde le numéro de dossier DN, jamais le nom de l'apprenant.
- Rétention : les entrées de plus de JOURNAL_RETENTION_JOURS (365 par défaut) sont purgées.
- Ne bloque jamais l'action journalisée : une erreur d'écriture est seulement loguée.
"""

import logging
import os
from datetime import datetime, timedelta, timezone

from sqlalchemy import Column, DateTime, Integer, String, Table, select

from service.utilisateurs import engine, metadata

logger = logging.getLogger(__name__)

journal = Table(
    "journal",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("horodatage", DateTime(timezone=True), nullable=False, index=True,
           default=lambda: datetime.now(timezone.utc)),
    Column("utilisateur", String(254), nullable=False),
    Column("action", String(30), nullable=False),  # envoi | telechargement
    Column("document", String(60)),
    Column("dossier", String(30)),
    Column("resultat", String(10), nullable=False),  # ok | erreur
    Column("message", String(500)),
)

_pret = False


def _engine():
    global _pret
    eng = engine()
    if not _pret:
        journal.create(eng, checkfirst=True)
        _pret = True
    return eng


def ecrire(utilisateur: str, action: str, document: str | None, dossier, resultat: str,
           message: str | None = None) -> None:
    try:
        retention = int(os.environ.get("JOURNAL_RETENTION_JOURS", "365"))
        with _engine().begin() as cx:
            cx.execute(journal.insert().values(
                utilisateur=utilisateur, action=action, document=document,
                dossier=str(dossier) if dossier is not None else None,
                resultat=resultat, message=(message or "")[:500] or None,
            ))
            cx.execute(journal.delete().where(
                journal.c.horodatage < datetime.now(timezone.utc) - timedelta(days=retention)))
    except Exception:  # noqa: BLE001
        logger.exception("Écriture du journal impossible")


def lister(limite: int = 300, utilisateur: str | None = None, resultat: str | None = None) -> list[dict]:
    requete = select(journal).order_by(journal.c.horodatage.desc(), journal.c.id.desc()).limit(limite)
    if utilisateur:
        requete = requete.where(journal.c.utilisateur == utilisateur)
    if resultat:
        requete = requete.where(journal.c.resultat == resultat)
    with _engine().connect() as cx:
        return [dict(l) for l in cx.execute(requete).mappings()]
