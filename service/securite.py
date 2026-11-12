"""
En-têtes de sécurité HTTP et redirection vers HTTPS.

- HTTPS : toute requête arrivée en HTTP par le routeur (X-Forwarded-Proto: http) est redirigée,
  puis HSTS demande au navigateur de ne plus jamais revenir en HTTP.
- CSP : tout est servi par l'application (aucun script, style ou police externe) ;
  'unsafe-inline' reste nécessaire pour quelques petits scripts et attributs style des gabarits.
- Pas de cache navigateur pour les pages et l'API (données d'apprenants), seulement pour /static.
"""

from flask import Flask, redirect, request

CSP = "; ".join([
    "default-src 'self'",
    "script-src 'self' 'unsafe-inline'",
    "style-src 'self' 'unsafe-inline'",
    "img-src 'self' data:",
    "font-src 'self'",
    "connect-src 'self'",
    "object-src 'none'",
    "base-uri 'self'",
    "form-action 'self'",
    "frame-ancestors 'none'",
])


def init_app(app: Flask) -> None:
    @app.before_request
    def forcer_https():
        # seulement derrière le routeur : les requêtes internes (sonde, local) n'ont pas l'en-tête
        if request.headers.get("X-Forwarded-Proto") == "http":
            return redirect(request.url.replace("http://", "https://", 1), code=301)
        return None

    @app.after_request
    def entetes(reponse):
        h = reponse.headers
        h.setdefault("Content-Security-Policy", CSP)
        h.setdefault("X-Content-Type-Options", "nosniff")
        h.setdefault("X-Frame-Options", "DENY")
        h.setdefault("Referrer-Policy", "same-origin")
        h.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=(), payment=()")
        h.setdefault("Cross-Origin-Opener-Policy", "same-origin")
        if request.is_secure:
            h.setdefault("Strict-Transport-Security", "max-age=31536000")
        if not request.path.startswith("/static/"):
            h["Cache-Control"] = "no-store"
        return reponse
