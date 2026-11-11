#import "../erasmus_plus_utils/erasmus_plus_editorial.typ" : *

// Contrat pédagogique Europass pour les activités de groupe (démarche 156967)

// taille des paragraphes d'introduction (FR + traduction) sous les titres
#let intro(body) = { set par(spacing: 0.55em); text(size: 8pt, body) }

// texte sur plusieurs lignes (liste de lignes) : une puce par ligne
#let puces(lignes) = if type(lignes) == array { list(tight: true, ..lignes) } else { lignes }

// texte sur plusieurs lignes : un paragraphe par ligne
#let paragraphes(lignes) = if type(lignes) == array { lignes.map(l => par(l)).join() } else { lignes }

// rubrique d'une activité : petit intitulé collé au texte qui suit
#let rubrique(label, contenu) = block(above: 11pt, below: 0pt, {
  block(below: 6pt, sticky: true, {
    text(6.5pt, weight: "bold", fill: navy, tracking: 0.08em, upper(label))
    h(4pt)
    text(6.5pt, en(translate(label)))
  })
  set list(spacing: 0.6em)
  block(above: 0pt, puces(contenu))
})

// fiche personne : nom, intitulé du poste, mail, téléphone
#let personnes(liste, prefixe) = forms(title_key: "Titre", espace_avant: 4pt,
  liste.enumerate().map(((i, p)) => (
    "Titre": if liste.len() == 1 { prefixe } else { prefixe + " " + str(i + 1) },
    "Nom": [#text(weight: "bold", upper(p.at("nom", default: missing_data))) #p.at("prenom", default: "")],
    "Intitulé du poste": p.at("fonction", default: missing_data),
    "Adresse mail": p.at("email", default: missing_data),
    "Téléphone": p.at("telephone", default: missing_data),
  )))

#let contrat_pedagogique_groupe(
  code_projet: missing_data,
  numero_europass: none,
  titre_activite: missing_data,
  date_debut: missing_data,
  date_fin: missing_data,
  duree: missing_data,
  pays_ville: missing_data,
  organisation_envoi_nom: missing_data,
  envoi_pays_ville: missing_data,
  organisation_accueil_nom: missing_data,
  accueil_pays_ville: missing_data,
  profil_participants: missing_data,
  secteur: "Enseignement et formation professionnels",
  format_mobilite: "Activité de mobilité physique",
  accompagnants: ((nom: missing_data,),),
  contacts_envoi: (),
  contacts_accueil: ((nom: missing_data,),),
  // une ligne par jour : (jour, matin, après-midi)
  calendrier: ((missing_data, missing_data, missing_data),),
  activites: ((titre: missing_data, methodes: missing_data, acquis: missing_data),),
  participants: ((missing_data, missing_data),),
  signature_envoi_nom: missing_data,
  signature_envoi_prenom: "",
  signature_envoi_fonction: none,
  signature_accueil_nom: missing_data,
  signature_accueil_prenom: "",
  signature_accueil_fonction: none,
  ..superfluous_arguments
 ) = [

#show: doc => erasmus_plus_layout(
  header_note: code_projet,
  title: "Contrat pédagogique · activités de groupe",
  show_title: false,
  doc
)

#let parts = if type(code_projet) == str { code_projet.split("-") } else { () }
#couverture(
  kicker: [EUROPASS MOBILITÉ #h(3pt)·#h(3pt) ACTIVITÉ DE GROUPE #if parts.len() >= 5 [#h(3pt)·#h(3pt) #parts.at(3) #parts.at(4)]],
  title: "Contrat pédagogique",
  translation: "Learning programme",
  participant_label: "ACTIVITÉ DE GROUPE",
  participant: text(weight: "bold", titre_activite),
  code_label: if numero_europass != none [N° Europass Mobilité] else [Code projet],
  code: if numero_europass != none { numero_europass } else { code_projet },
  cles: (
    ("Destination", pays_ville),
    ("Début", date_debut),
    ("Fin", date_fin),
    ("Durée", duree),
  ),
)

= Information sur l’activité de groupe
#chap[
  #form((
    "Organisme d’envoi": organisation_envoi_nom,
    "Pays et ville": envoi_pays_ville,
  ))
  #form((
    "Organisme d’accueil": organisation_accueil_nom,
    "Pays et ville": accueil_pays_ville,
  ))
  #form((
    "Secteur": secteur,
    "Format": format_mobilite,
  ))

  === Profil des participants
  #paragraphes(profil_participants)
]

= Accompagnateurs et contacts

== Accompagnateurs
#chap(level: 2)[ #personnes(accompagnants, "Accompagnateur") ]

#if contacts_envoi.len() > 0 [
== Autres personnes de contact dans l’organisme d’envoi
#chap(level: 2)[ #personnes(contacts_envoi, "Contact") ]
]

== Personnes de contact dans l’organisme d’accueil
#chap(level: 2)[ #personnes(contacts_accueil, "Contact") ]

= Calendrier des activités
#chap[
  #tableau(("Jour", "Matin", "Après-midi"), calendrier, columns: (14%, 1fr, 1fr))
]

= Description des activités et des acquis d’apprentissage
#chap[
  #for (i, a) in activites.enumerate() [
    #if i > 0 { v(12pt) }
    #block(breakable: false)[
      #block(above: 14pt, below: 2pt)[
        #text(12pt, weight: "bold", fill: navy)[Activité #(i + 1)#if "titre" in a [ : #a.titre]]
        #h(5pt) #text(9pt, en[Activity #(i + 1)])
      ]
      #rubrique("Méthodes et tâches", a.at("methodes", default: missing_data))
      #rubrique("Acquis d’apprentissage", a.at("acquis", default: missing_data))
    ]
  ]
]

= Liste des participants
#chap[
  #tableau(("N°", "Prénom(s) et nom(s)", "Organisme"),
    participants.enumerate().map(((i, p)) => (str(i + 1), ..p)),
    columns: (8%, 1fr, 1fr))
]

#block(breakable: false)[
= Signatures
#chap[
  #intro[
  Les signataires confirment que les informations contenues dans ce document sont correctes et complètes.

  #englishStyling[The signatories confirm that the information in this document is correct and complete.]
  ]
  #signatures((
    (titre: "Pour l’organisme d’envoi", organisme: organisation_envoi_nom,
     nom: signature_envoi_nom, prenom: signature_envoi_prenom, fonction: signature_envoi_fonction, date_label: "Date"),
    (titre: "Pour l’organisme d’accueil", organisme: organisation_accueil_nom,
     nom: signature_accueil_nom, prenom: signature_accueil_prenom, fonction: signature_accueil_fonction, date_label: "Date"),
  ))
]
]

]
