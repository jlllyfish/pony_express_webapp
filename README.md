# Pony Express — webapp (V1 : kit pédagogique)

Interface Flask autour de [Pony_express](https://github.com/jlllyfish/Pony_express) :
liste les dossiers de la démarche 128447, filtre par établissement, recherche par nom,
génère le kit pédagogique en PDF pour les dossiers sélectionnés.

L'envoi vers DN (pièce jointe des annotations privées) n'est **pas encore implémenté** —
endpoint `/api/kits/send` réservé mais renvoie 501 (Phase 3 du plan).
Le statut affiché sur les cartes (généré / envoyé) n'est pas persisté entre deux
redémarrages : c'est un TODO Phase 4 (colonnes dédiées dans Grist, comme le fait déjà
PonyExpress pour la colonne PJ côté Grist).

## Installation locale

1. PonyExpress est copié dans `vendor/pony_express` via **git subtree** (Scalingo ne
   récupère pas les sous-modules git). Ses chemins vers `templates/` et les fontes sont
   relatifs à sa racine, d'où la copie plutôt qu'une dépendance pip. Pour récupérer
   les derniers templates :

   ```sh
   git subtree pull --prefix=vendor/pony_express https://github.com/jlllyfish/Pony_express.git main --squash
   ```

2. Typst : rien à installer, le compilateur est fourni par le paquet PyPI `typst`
   (compilation dans le processus Python, voir `service/pdf.py`).

3. Installer les dépendances :

   ```sh
   poetry install
   ```

4. Copier `.env.example` en `.env` (chargé automatiquement en dev via `flask run`,
   ou à exporter toi-même) et renseigner `GRIST_API_KEY`. Vérifie que `GRIST_TABLE`
   correspond bien au nom exact de l'onglet dans le doc Grist.

5. Lancer :

   ```sh
   poetry run flask --app app run --debug
   ```

   ou directement `poetry run python app.py`.

## Déploiement Scalingo

Buildpack Python (détecté via `poetry.lock`, version dans `.python-version`), lancé par
le `Procfile` (gunicorn, 1 worker / 8 threads : le cache et le compteur d'essais de
connexion sont en mémoire, donc un seul processus).

Apps : `pony-express-pro-preprod` → `pony-express-pro` (et plus tard `-sup-…`).

1. Créer l'app (région `osc-fr1`) et ajouter l'addon PostgreSQL (fournit `DATABASE_URL`).
2. Variables d'environnement : toutes celles de `.env.example`, avec `SECRET_KEY`
   aléatoire, sans `FLASK_DEBUG` ni `PORT` (fourni par Scalingo).
   `DN_API_TOKEN` et `INSTRUCTEUR_ID` sont obligatoires au démarrage.
3. Lier le dépôt GitHub (onglet *Code*) sur la branche voulue, puis déployer.
4. Créer le premier compte :
   `scalingo --app pony-express-pro-preprod run flask --app app utilisateurs ajouter prenom.nom@exemple.fr`

**Validation de l'étape 1** : le build passe, `https://<app>.osc-fr1.scalingo.io/health`
répond `{"status":"ok"}`, `/` redirige vers `/connexion`, la connexion fonctionne et un
kit généré a les fontes Marianne.

## Comptes utilisateurs

L'application exige une connexion. Pas d'inscription libre.

**Page « Utilisateurs »** (icône dans le rail, visible des administrateurs) : inviter une personne
(compte créé + lien valable 7 jours pour choisir son mot de passe, envoyé par e-mail si SMTP est
configuré, sinon affiché une fois pour être transmis), renvoyer un lien, activer / désactiver,
donner / retirer le rôle admin, supprimer. Le plus ancien compte devient admin s'il n'y en a aucun.

**Double authentification (TOTP)**, obligatoire : après le mot de passe, code à 6 chiffres d'une
application d'authentification (FreeOTP, Aegis, Google/Microsoft Authenticator). Au premier passage,
QR code à scanner puis 10 codes de secours à usage unique. Codes rejoués refusés, 5 essais puis
blocage 15 min. Un admin peut « Réinit. 2FA » (nouvel enrôlement à la connexion suivante).
Secrets chiffrés avec `TOTP_CLE` (à définir **avant** le premier enrôlement : la changer ensuite
rend les secrets illisibles). Dépannage sans terminal si plus aucun admin ne peut se connecter :
`TOTP_OBLIGATOIRE=0` le temps de se connecter et de réinitialiser, puis remettre à 1.

**Page « Journal »** (admins) : chaque envoi vers DN et chaque téléchargement de PDF, avec l'utilisateur,
le document, le numéro de dossier (jamais le nom de l'apprenant) et le résultat. Conservé
`JOURNAL_RETENTION_JOURS` jours (365 par défaut).

En ligne de commande (`--admin` pour créer un administrateur, `utilisateurs admin <email>` pour promouvoir) :

```bash
poetry run flask --app app utilisateurs ajouter prenom.nom@exemple.fr   # demande le mot de passe (12 caractères min.)
poetry run flask --app app utilisateurs lister
poetry run flask --app app utilisateurs desactiver prenom.nom@exemple.fr
poetry run flask --app app utilisateurs activer prenom.nom@exemple.fr
poetry run flask --app app utilisateurs supprimer prenom.nom@exemple.fr
```

Sur Scalingo : `scalingo --app <app> run flask --app app utilisateurs ajouter prenom.nom@exemple.fr`.

Sans terminal (réseau qui bloque `scalingo run`) : définir la variable `PREMIER_COMPTE=prenom.nom@exemple.fr`
et redéployer. Si aucun compte n'existe, il est créé avec un mot de passe aléatoire : passer par
« Mot de passe oublié » (sans SMTP, le lien est dans les logs) pour choisir le sien, puis supprimer la variable.

- Comptes stockés dans PostgreSQL (`DATABASE_URL`, fournie par l'addon Scalingo), SQLite en local.
- Mots de passe chiffrés (scrypt), jamais stockés en clair.
- « Mot de passe oublié » : lien valable 1 h et utilisable une seule fois, envoyé par e-mail
  (variables `SMTP_*`) ; sans `SMTP_HOST`, le lien est écrit dans les logs.
- 5 essais ratés en 15 min bloquent l'adresse et l'IP pendant 15 min.
- `SECRET_KEY` obligatoire en production (sinon les sessions sont perdues à chaque redémarrage).

## Vérifier que ça marche

- `/` doit lister les dossiers réels de la 128447, filtrables par établissement.
- Taper les 3 premières lettres d'un nom réel doit faire remonter le bon dossier
  (filtrage direct sur la grille, pas de va-et-vient serveur).
- Sélectionner 1-2 dossiers, cliquer **Générer** : la carte doit passer en statut
  "généré" et proposer un lien de téléchargement.
- `/api/kits/<numero>/download` doit renvoyer le même PDF que celui déjà validé
  en CLI (Phase 1).
