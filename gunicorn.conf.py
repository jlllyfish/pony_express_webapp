"""Configuration gunicorn (chargée automatiquement depuis le dossier de l'app)."""

from gunicorn.glogging import Logger

# Requêtes automatiques réussies non journalisées : le suivi des collègues (toutes les 8 s par
# onglet ouvert) et la sonde de disponibilité noieraient les logs Scalingo.
SONDES = {"/api/evenements", "/health"}


class JournalSansSondes(Logger):
    def access(self, resp, req, environ, request_time):
        if req.path in SONDES and str(resp.status).startswith("2"):
            return
        super().access(resp, req, environ, request_time)


logger_class = JournalSansSondes
