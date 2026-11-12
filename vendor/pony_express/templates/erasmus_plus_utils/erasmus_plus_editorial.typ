// Mise en page « éditoriale » (variante 1) : typographie forte, filets fins, numéros en marge.
// Reprend l'API de erasmus_plus_template_utils.typ (form, forms, chap, signatures,
// erasmus_plus_layout...) : un template passe d'une mise en page à l'autre en changeant son import.
#import "erasmus_plus_template_utils.typ" : *

// ── Palette et réglages ──────────────────────────────────────────────
#let navy = rgb("#16235C")
#let jaune = rgb("#FFCC00")
#let gris = rgb("#7A8194")
#let filet = rgb("#D9DCE6")
#let encre = rgb("#1D2233")

#let num_col = 1.5cm          // colonne des numéros de titres, dans la marge gauche
#let outdent(it) = pad(left: -num_col, it)  // pleine largeur (titres, page de garde)
#let label_col = 34%          // colonne des intitulés dans les fiches
#let label_col_wide = 42%

// ── Texte anglais ────────────────────────────────────────────────────
// gris seulement : les templates l'entourent parfois de _..._ (italique)
#let englishStyling(english) = text(fill: gris, english)
#let en(t) = text(fill: gris, style: "italic", t)
#let tr(t, activate: true) = if activate and is_translatable(t) { translate(t) } else { none }

// données insérées depuis Grist : noir gras ; manquante en rouge
#let custom_data(it) = if it == missing_data { text(fill: rgb("#C0392B"), it) } else { text(fill: black, weight: "bold", it) }

// titre intermédiaire dans le corps du document (ex : annexes)
#let erasmus_title(title, translation: "") = outdent(block(above: 18pt, below: 12pt, {
  text(16pt, weight: "bold", fill: navy, title)
  if translation != "" { linebreak(); text(13pt, weight: "light", fill: gris, translation) }
}))

// ── Corps de section ─────────────────────────────────────────────────
#let chap(it, level: 1) = block(width: 100%, it)

// ── Fiches ───────────────────────────────────────────────────────────
#let form_label(title, activate_translation) = {
  text(size: 8.5pt, weight: "bold", title)
  if activate_translation {
    linebreak()
    text(size: 7.5pt, en(translate(title)))
  }
}

#let form_value(value, activate_translation) = {
  value
  if activate_translation and is_translatable(value) {
    linebreak()
    en(translate(value))
  }
}

#let form_table(fields, activate_translation: true, wide_title: false) = {
  set par(justify: false)
  table(
  columns: (if wide_title { label_col_wide } else { label_col }, 1fr),
  column-gutter: 8pt,
  inset: (x: 0pt, y: 5pt),
  stroke: (x, y) => (bottom: 0.5pt + filet),
  ..fields.pairs().map(((key, value)) => (
    form_label(key, activate_translation),
    form_value(value, activate_translation),
  )).flatten(),
)}

#let form(fields, activate_translation: true, wide_title: false) = block(
  breakable: false, width: 100%, above: 6pt, below: 10pt,
  form_table(fields, activate_translation: activate_translation, wide_title: wide_title))

// intertitre d'une fiche : RÔLE en capitales + traduction
#let role_title(title, activate_translation: true) = {
  text(8pt, weight: "bold", fill: navy, tracking: 0.08em, upper(title))
  let t = tr(title, activate: activate_translation)
  if t != none { h(4pt); text(7.5pt, en(t)) }
}

// plusieurs fiches (personnes) : deux colonnes dès qu'il y en a plus d'une
// title_key : clé affichée en intertitre au-dessus de la fiche (et retirée du tableau)
// espace_avant : marge au-dessus des fiches (réduite quand elles suivent directement un sous-titre)
#let forms(items, activate_translation: true, wide_title: false, title_key: none, espace_avant: 22pt) = {
  let fiche(fields) = block(breakable: false, width: 100%, {
    if title_key != none and title_key in fields and fields.at(title_key) != "" {
      role_title(fields.at(title_key), activate_translation: activate_translation)
      v(-2pt)
    }
    let rest = (:)
    for (key, value) in fields.pairs() {
      if title_key == none or key != title_key { rest.insert(key, value) }
    }
    form_table(rest, activate_translation: activate_translation, wide_title: wide_title)
  })
  v(espace_avant)
  block(width: 100%, above: 0pt, below: 12pt,
    grid(columns: if items.len() > 1 { (1fr, 1fr) } else { (1fr,) },
      column-gutter: 16pt, row-gutter: 14pt,
      ..items.map(fiche)))
}

// ── Tableau ──────────────────────────────────────────────────────────
// entetes : intitulés français (traduits par le dictionnaire) ; lignes : liste de lignes (listes de cellules)
// l'en-tête se répète si le tableau continue sur la page suivante
#let tableau(entetes, lignes, columns: auto, activate_translation: true) = {
  set par(justify: false)
  table(
    columns: if columns == auto { (1fr,) * entetes.len() } else { columns },
    // plus d'air entre le filet de l'en-tête et la première ligne
    inset: (x, y) => (x: 6pt, top: if y == 1 { 11pt } else { 6pt }, bottom: 6pt),
    stroke: (x, y) => (bottom: if y == 0 { 1.2pt + navy } else { 0.5pt + filet }),
    table.header(..entetes.map(h => {
      text(7.5pt, weight: "bold", fill: navy, tracking: 0.06em, upper(h))
      let t = tr(h, activate: activate_translation)
      if t != none { linebreak(); text(7pt, en(t)) }
    })),
    ..lignes.flatten(),
  )
}

// ── Signatures ───────────────────────────────────────────────────────
#let signature_name(nom, prenom) = if nom in (missing_data, "") {
  missing_data
} else {
  text(weight: "bold", upper(nom)) + if prenom not in (missing_data, "") [ #prenom ]
}

// valeur : texte pré-rempli au-dessus de la ligne (ex : date de fin de stage)
#let zone_signature(label, hauteur, activate_translation, valeur: none) = {
  // hauteur fixe : la ligne reste au même niveau, valeur pré-remplie ou non
  block(width: 100%, height: hauteur, above: 0pt, below: 0pt,
    align(bottom, if valeur != none { pad(bottom: 3pt, text(9pt, weight: "bold", valeur)) }))
  line(length: 100%, stroke: 0.5pt + filet)
  v(-6pt)
  text(7pt, fill: gris)[#label #if activate_translation and is_translatable(label) [· #en(translate(label))]]
}

#let signature(title, name, prenom: "", organisme: none, fonction: none, adresse: none,
                date: none, date_label: "Date et lieu", activate_translation: true) = block(
  breakable: false, width: 100%,
  stroke: (left: 2pt + jaune), inset: (left: 10pt, y: 4pt), {
    set par(justify: false)
    set text(hyphenate: false)
    text(8pt, weight: "bold", title)
    let t = tr(title, activate: activate_translation)
    if t != none { h(4pt); text(7pt, en(t)) }
    linebreak()
    if organisme != none { text(9.5pt, weight: "medium", fill: navy, organisme); linebreak() }
    if adresse != none { text(8pt, fill: gris, adresse); linebreak() }
    text(9pt, signature_name(name, prenom))
    if fonction != none { linebreak(); text(8.5pt, fill: gris, fonction) }
    zone_signature(date_label, 0.8cm, activate_translation, valeur: date)
    zone_signature("Signature et cachet", 2.5cm, activate_translation)
  })

// une cellule = ("Titre", "Nom", "Prénom"[, "Organisme"[, "Fonction"]]) ; ou plusieurs signataires alternatifs, séparés par « ou » :
//   (("Tuteur légal 1", ...), ("Tuteur légal 2", ...))
//   ou une fiche (titre: ..., nom: ..., prenom:, organisme:, fonction:, adresse:, date:, date_label:)
//   ou un dictionnaire { "Titre": nom, ... }
#let signatures(cellules, activate_translation: true) = {
  let items = if type(cellules) == dictionary { cellules.pairs() } else { cellules }
  let blocs = items.map(cellule => {
    if type(cellule) == dictionary {
      let f = cellule
      signature(f.titre, f.at("nom", default: missing_data), prenom: f.at("prenom", default: ""),
        organisme: f.at("organisme", default: none), fonction: f.at("fonction", default: none),
        adresse: f.at("adresse", default: none), date: f.at("date", default: none),
        date_label: f.at("date_label", default: "Date et lieu"), activate_translation: activate_translation)
    } else if type(cellule.at(0)) == str {
      signature(cellule.at(0), cellule.at(1), prenom: cellule.at(2, default: ""),
        organisme: cellule.at(3, default: none), fonction: cellule.at(4, default: none),
        activate_translation: activate_translation)
    } else {
      stack(spacing: 6pt, ..cellule.map(s => signature(s.at(0), s.at(1), prenom: s.at(2, default: ""),
        activate_translation: activate_translation)).intersperse(text(8pt, fill: gris, "ou")))
    }
  })
  // insécable : un titre placé juste avant (sticky) suit les signatures sur la page suivante
  block(breakable: false, above: 10pt,
    grid(columns: (1fr, 1fr), column-gutter: 16pt, row-gutter: 20pt, ..blocs))
}

// ── Page de garde ────────────────────────────────────────────────────
// cles : ((intitulé, valeur), ...) — bandeau de chiffres clés (traductions par le dictionnaire)
#let couverture(kicker: "ERASMUS+", title: "", translation: "", participant: none,
                code: none, cles: (), activate_translation: true, compact: false,
                participant_label: "PARTICIPANT·E", code_label: "Code projet") = outdent({
  // compact : page de garde resserrée (document d'une page)
  let (t_size, sous, nom, gap) = if compact { (20pt, 12pt, 13pt, 6pt) } else { (27pt, 15pt, 17pt, 10pt) }
  text(8pt, weight: "bold", fill: navy, tracking: 0.12em, kicker)
  v(6pt)
  // titre sur une ligne : corps réduit si besoin
  layout(size => context {
    let t(s) = text(s, weight: "bold", fill: navy, tracking: -0.02em, title)
    let w = measure(t(t_size)).width
    t(if w > size.width { t_size * (size.width / w) * 0.98 } else { t_size })
  })
  if translation != "" { v(-6pt); text(sous, weight: "light", fill: gris, translation) }
  v(gap)
  grid(columns: (1fr, auto), align: bottom,
    [#text(7.5pt, fill: gris, tracking: 0.1em, participant_label) \ #text(nom, weight: "medium", fill: encre, participant)],
    if code != none { text(8pt, fill: gris)[#code_label \ #text(fill: navy, weight: "bold", code)] })
  v(gap)
  let cle((label, valeur)) = {
    text(7pt, fill: gris, tracking: 0.08em, upper(label))
    let t = tr(label, activate: activate_translation)
    if t != none { h(3pt); text(6.5pt, en(t)) }
    linebreak()
    v(-2pt)
    text(12pt, weight: "bold", fill: navy, valeur)
  }
  set par(justify: false)
  block(width: 100%, stroke: (top: 2pt + navy, bottom: 0.5pt + filet), inset: (y: gap), below: gap + 4pt,
    grid(columns: (1.4fr,) + (1fr,) * calc.max(cles.len() - 1, 0), column-gutter: 12pt, ..cles.map(cle)))
})

// ── Mise en page ─────────────────────────────────────────────────────
// show_title : titre en tête de la première page (false si le template appelle #couverture)
#let erasmus_plus_layout(title: "", translation: "", activate_translation: true, header_note: none,
                         show_title: true, footer_extra: none, doc) = {
  set text(font: "Marianne", size: 9.5pt, fill: encre)
  set par(leading: 0.8em, spacing: 1.2em, justify: true)
  set list(marker: text(fill: navy, "•"), spacing: 0.9em)
  show footnote.entry: set text(size: 6pt)

  set document(title: [#title], author: "MOOW By ENSFEA")

  set page(
    paper: "a4",
    margin: (left: 1.8cm + num_col, right: 1.8cm, top: 3.1cm, bottom: 1.8cm),
    header: outdent({
      grid(columns: (1fr, auto), align: (left + horizon, right + horizon),
        image("assets/header_logo.png", height: 1.15cm, alt: "Move occitanie over the world by ENSFEA"),
        image("assets/footer_logo.png", height: 0.75cm,
          alt: "Erasmus +, enrichit les vies, ouvre les esprits. Financé par l'Union Européenne"))
      v(-2pt)
      line(length: 100%, stroke: 0.5pt + filet)
    }),
    // footer_extra : mention légale en petit au-dessus du pied de page (ex : Europass)
    footer: outdent({
      if footer_extra != none { block(below: 4pt, text(6pt, fill: gris, footer_extra)) }
      text(7.5pt, fill: gris)[#header_note #h(1fr) #title · #context counter(page).display("1/1", both: true)]
    }),
  )

  set heading(numbering: "1.1")

  show heading: set par(justify: false)
  show heading.where(level: 1): it => block(above: 24pt, below: 10pt, outdent(grid(
    columns: (num_col, 1fr),
    text(24pt, weight: "light", fill: navy, counter(heading).display()),
    {
      v(4pt)
      text(12.5pt, weight: "bold", fill: navy, it.body)
      let t = tr(it.body, activate: activate_translation)
      if t != none { linebreak(); text(9pt, en(t)) }
      v(-4pt)
      line(length: 100%, stroke: 1.2pt + navy)
    })))

  show heading.where(level: 2): it => block(above: 32pt, below: 12pt, {
    text(11.5pt, weight: "bold", fill: navy, counter(heading).display() + h(6pt) + it.body)
    let t = tr(it.body, activate: activate_translation)
    if t != none { h(6pt); text(9pt, en(t)) }
  })

  show heading.where(level: 3): it => block(above: 10pt, below: 2pt,
    role_title(it.body, activate_translation: activate_translation))

  // un titre ne reste jamais seul en bas de page (règle placée après les autres : appliquée en premier)
  // espacement porté par ce bloc extérieur (celui des blocs internes ne s'applique pas)
  show heading: it => block(sticky: true,
    above: if it.level == 1 { 28pt } else if it.level == 2 { 30pt } else { 20pt },
    below: if it.level <= 2 { 12pt } else { 14pt },
    it)

  if show_title and title != "" {
    outdent(block(below: 18pt, {
      set par(justify: false)
      text(22pt, weight: "bold", fill: navy, tracking: -0.01em, title)
      if translation != "" { linebreak(); v(-4pt); text(13pt, weight: "light", fill: gris, translation) }
    }))
  }

  doc
}
