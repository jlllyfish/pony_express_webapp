#import "erasmus_translation.typ" : * 

#set text(font: "marianne")
#let blue_line =  line(length: 100%, stroke: (paint: rgb("#333399")))
#let black_line =  line(length: 100%, stroke: (paint: black))

// taille des numeros de titres (1, 2...) et de sous-titres (le 2 de 4.2)
#let heading_number_size = 20pt
#let subheading_number_size = 17pt

// espace entre deux fiches de personnes (0.65em = colle aux autres lignes)
#let people_spacing = 1.2em

#let missing_data = "[donnée manquante]"

#let custom_data(it) = if (it == missing_data) {
  text(red, it)
} else {
  text(blue, it)
}

#let label_size = 10pt              // intitules des lignes (corps : 11pt)
#let label_translation_size = 8pt  // leur traduction
#let label_row_gutter = 5pt        // espace entre l'intitule et sa traduction

#let signature_bg = rgb("#f2f2f2")  // fond des blocs de signature
#let signature_value_size = 9pt  // valeurs des signatures (corps : 11pt)
#let chap_indent = 12%       // retrait du corps de texte
#let subheading_indent = 16pt  // retrait supplementaire des sous-titres
#let heading_size = 13pt      // titres (avant : 15pt)
#let subheading_size = 11pt    // taille des sous-titres (titres : 15pt)

#let chap(it, level: 1) = block(
  width: 100%,
  inset: (left: chap_indent + if level >= 2 { subheading_indent } else { 0pt }),
  it) 

#let englishStyling(english) = {
  text(gray, [#english])
}

#let unbreakable(content) = {
  block(
    breakable: false,
    content
  )
}

#let conditionnal_content(test_mode, it) = {
  if test_mode {
    text(weight: "bold", grey, "Ce contenu apparait en mode test seulement et ne s'appliquerait pas en production" + linebreak())
    text(grey, it)
  } else {
    it
  }
}

///////////
// Forms //
///////////

#let form_item(title, value, activate_translation: true, wide_title:false) = {
  set par( 
    justify: false,
    spacing: 0.65em)

  let width = 30%
  if wide_title {width = 40%}

  // intitule et traduction dans une seule cellule : l'espacement ne depend plus de la hauteur de la valeur
  let label = {
    set par(leading: label_row_gutter)
    text(size: label_size, weight: "bold", title)
    if activate_translation {
      linebreak()
      englishStyling(text(size: label_translation_size, translate(title)))
    }
  }
  let contenu = {
    set par(leading: label_row_gutter)
    value
    if activate_translation and is_translatable(value) {
      linebreak()
      englishStyling([_#translate(value)_])
    }
  }

  {
    blue_line
    grid(
      columns: (width, 100%-width),
      column-gutter: 8pt,
      align: top,
      label, contenu
    )
  }
}

#let form(fields, activate_translation: true, wide_title: false) = {
  block(
    breakable: false,
    inset: 5pt,
    {
      for key in fields.keys() { 
        form_item(
          key, 
          fields.at(key),
          activate_translation: activate_translation, 
          wide_title: wide_title)
      }
    }
  )
  
}

// plusieurs fiches a la suite (personnes) : meme espacement qu'entre les lignes d'une fiche
// title_key : cle affichee en intertitre au-dessus de la fiche (et retiree du tableau)
#let forms(items, activate_translation: true, wide_title: false, title_key: none) = block(
  inset: 5pt,
  for fields in items {
    block(breakable: false, spacing: people_spacing, {
      if title_key != none and title_key in fields and fields.at(title_key) != "" {
        text(weight: "bold", fields.at(title_key))
        v(-0.45em)
      }
      for key in fields.keys() {
        if title_key == none or key != title_key {
          form_item(key, fields.at(key),
            activate_translation: activate_translation, wide_title: wide_title)
        }
      }
    })
  })

////////////////
// Signatures //
////////////////

#let signature_name(nom, prenom) = if nom in (missing_data, "") {
  custom_data(missing_data)
} else {
  custom_data(text(weight: "bold", upper(nom)) + if prenom not in (missing_data, "") [ #prenom ])
}

#let signature(title, name, prenom: "", activate_translation: true, wide_title: true) = {
  box(fill: signature_bg, outset:(x: 6pt, y: 6pt),
  [
    === #title
    #form((
        "Nom" : text(size: signature_value_size, signature_name(name, prenom)),
        "Date et lieu":"",
        "Signature":"",

    ),
      activate_translation: activate_translation,
      wide_title: wide_title
    )]
  )
}

// une cellule = ("Titre", "Nom") ; ou plusieurs signataires alternatifs, separes par "ou" :
//   (("Tuteur legal 1", "..."), ("Tuteur legal 2", "..."))
#let signatures(cellules, activate_translation: true) = {
  let signatures_list = ()
  for cellule in cellules {
    if type(cellule.at(0)) == str {
      signatures_list.push(signature(cellule.at(0), cellule.at(1),
        prenom: cellule.at(2, default: ""), activate_translation: activate_translation))
    } else {
      let bloc = ()
      for signataire in cellule {
        if bloc.len() > 0 {
          bloc.push(align(center, "ou"))
        }
        bloc.push(signature(signataire.at(0), signataire.at(1),
          prenom: signataire.at(2, default: ""), activate_translation: activate_translation))
      }
      signatures_list.push(stack(spacing: 20pt, ..bloc))
    }
  }
  grid(columns: (1fr, 1fr),
  gutter: 20pt,
  ..signatures_list
  )
}

#let erasmus_title(title, translation: "") = {

    text(16pt, strong(title)) 

    if translation != "" {
      [\ ] + englishStyling(strong[#text(16pt, translation)])
    }
  }

////////////
// Layout //
////////////

#let erasmus_plus_layout(title: "", translation: "", activate_translation: true, header_note: none, doc) = {
  set text(font: "Marianne")
  
  let moow_logo = image("assets/header_logo.png",
  alt: "Move occitanie over the world by ENSFEA")

  let erasmus_logo = image("assets/footer_logo.png",
    alt: "Erasmus +, enrichit les vies, ouvre les esprits. Financé par l'Union Européenne",)

  let header = {
    grid(
      columns: (1fr, 3fr),
      gutter: 1em,
      moow_logo,
      erasmus_logo
    )
    black_line
    if header_note != none {
      v(-0.4em)
      align(right, text(9pt, header_note))
    }
        align(center, erasmus_title(title, translation: translation))
  }

  set document(
    title: [#title],
    author: "MOOW By ENSFEA",
  )

  set page(
    numbering: "- 1/1 -",
    margin: (top: 150pt, right: 15%),
    header-ascent: 15%,
    header: {header},
  )

  set heading(numbering: "1.1")

  show heading.where(level: 1): it => {

    let titleBlock = {
      text(heading_size, it.body) 
      if (activate_translation) {
        linebreak()
        v(-0.9em)
        englishStyling(text(heading_size - 2pt, translate(it.body)))
      }
    }

    pad(y: 10pt,
      grid(
        columns: (1fr, 9fr),
        column-gutter: 10pt,
        align(right, text(heading_number_size, counter(heading).display())),
        align(horizon, titleBlock), 
    ))
  }

  show heading.where(level: 2): it => {
    let titleBlock = {
      text(subheading_size, it.body)
      if (activate_translation) {
        linebreak()
        v(-0.9em)
        englishStyling(text(subheading_size - 2pt, translate(it.body)))
      }
    }

    pad(y: 10pt, left: subheading_indent,
      grid(
        columns: (1fr, 9fr),
        column-gutter: 10pt,
        align(right, text(subheading_number_size, counter(heading).display())),
        align(horizon, titleBlock),
      )
    )
  }

  show heading.where(level: 3): it => {
    strong(it.body)
    
    if (activate_translation) {
      linebreak()
      englishStyling[#translate(it)]
    }
  }

  // un titre ne reste jamais seul en bas de page (regle placee apres les autres : appliquee en premier)
  show heading: it => block(sticky: true, it)

  set par(
    justify: true,
  )

  doc
}

}

