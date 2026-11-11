---
title: First Run
description: Tutorial to run PonyExpress locally
---

Dans ce tutoriel, nous allons lancer PonyExpress localement pour la première fois.

This tutorial will guide you to run PonyExpress for the first time locally

## Install the needed toolss

If you use [nix](https://nixos.org/), simply rename `_shell.nix` en `shell.nix` and run `nix-shell --pure` 

If not, install : 
- python,
- [poetry](https://python-poetry.org/docs/#installation)
- [typst](https://github.com/typst/typst?tab=readme-ov-file#installation) 
- (optionnal) [task](https://taskfile.dev/docs/installation) - a userfriendly alternative to make (will allow you  to use the preconfigured scripts)

## Install the libraries

If you have task

```sh
task setup
```

else 

```sh
git clone git@gitlab.com:multi-coop/pony_express.git
cd pony_express
poetry install
```

## Allow access from the GRIST API

You need an API Key to use the GRIST API. This key is associated to your own account and **must not be shared**. 

You can find it via your grist webapp. User icon => Profile settings => API => API keys

Once copied, add it as an environnment variable, 

If you use nix, to you shell.nix file (which will be safely ignored by .gitignore) else run

```sh
 export GRIST_API_KEY="API KEY disponible via votre compte GRIST"
```

## Run the example

The example retrieve the data from this [public table](https://docs.getgrist.com/uJrM5M5P5Z4Q/ponyexpressexemple) and generate a pdf using the `templates/exemple/birthday_template.typ`

```sh
task serve_exemple
```

else 

```sh
 poetry run python src/pony_express/exemple.py
```

The generated PDF can be found in the generated folder

## Create your own PDF

See [Create your own PDF](/tutorial/2_create_your_pdf)