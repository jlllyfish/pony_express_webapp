---
title: Create your own PDF
description: Use your own template and grist data
---

In ordre to create your own PDF, you will need : 

- to create a Typst template that will create a PDF with the desired layout
- configure a python script that will import the Grist data and export them as PDF

Pony express will
- import your data from grist
- create a typst file that will import and setup your template
- compile this file to a pdf and delete the intermediary file

## Typst 

Typst is an user friendly Latex alternative.
You can find the documentation [here](https://typst.app/docs/) and experiment with it in their [online app](https://typst.app/app/)

Create a folder in `templates` for your own projet.

You can use [`./templates/exemple/birthday_template.typ`](https://github.com/multi-coop/ponyexpress/blob/main/templates/exemple/birthday_template.typ) or the others files in the `templates` folder as reference.

Being a template, it can't be compiled itself. You need another file that will import it and give it its required parameters (those are the files that will be created automatically by pony_express)

For now, you can create your own to test your template independently from pony_express.
[_`./template/exemple/test_birthday.typ`_](https://github.com/multi-coop/ponyexpress/blob/main/templates/exemple/test_birthday.typ) is an exemple of such a file

To test it : 

- you can compile it ``typst compile templates/exemple/test_birthday.typ ``
- you can import both the test_birthday and the birthday_template in the typst webapp to experiment with it online
- you can use the [tinymist extension](https://marketplace.visualstudio.com/items?itemName=myriad-dreamin.tinymist) for VSCodium to have a direct preview locally
  - troubleshooting : the extension does not give you the error message. is there is no working preview, compile your file manually to display the compilation error messages

### Fonts 

You can add any font in your template folder. It will be scanned and added by PonyExpress when compiling.

## Python 

Once you have a typst template, you can now duplicate the [`src/exemple.py`](https://github.com/multi-coop/ponyexpress/blob/main/src/pony_express/templates/exemple.py) file. 

Use the included commentaries to configure the variables and functions according to your needs. For exemple :
-  which line to ignore (`should_be_exported()`),
- how to name the pdf (`name_pdf()`),
- how to transform the imported data (`apply_data_transformation()`)

You can now run it by calling 

```sh
task serve_exemple
```

```sh
poetry run python src/pony_express/exemple.py
```

The generated pdf will appear `generated`