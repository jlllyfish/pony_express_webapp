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

1. Vendoriser PonyExpress (nécessaire : ses chemins vers `templates/` et les fontes
   sont relatifs à sa propre racine de repo, donc il ne peut pas être une simple
   dépendance pip installée dans site-packages) :

   ```sh
   git submodule add https://github.com/jlllyfish/Pony_express.git vendor/pony_express
   ```

2. Installer `typst` (binaire, pas le wrapper pip) — voir
   https://github.com/typst/typst?tab=readme-ov-file#installation

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

## Vérifier que ça marche

- `/` doit lister les dossiers réels de la 128447, filtrables par établissement.
- Taper les 3 premières lettres d'un nom réel doit faire remonter le bon dossier
  (filtrage direct sur la grille, pas de va-et-vient serveur).
- Sélectionner 1-2 dossiers, cliquer **Générer** : la carte doit passer en statut
  "généré" et proposer un lien de téléchargement.
- `/api/kits/<numero>/download` doit renvoyer le même PDF que celui déjà validé
  en CLI (Phase 1).
