#import "../erasmus_plus_utils/erasmus_plus_editorial.typ" : * 

// taille des paragraphes d'introduction (FR + traduction) sous les titres
#let intro(body) = { set par(spacing: 0.55em); text(size: 8pt, body) }

// texte sur plusieurs lignes (liste de lignes) : une puce par ligne, sans saut de ligne
#let puces(lignes) = if type(lignes) == array { list(tight: true, ..lignes) } else { lignes }

// Contrat pédagogique Europass pour les mobilités du personnel (démarche 156966)
// même design et même structure que le contrat apprenant, sans tuteur légal ni accompagnateur

#let contrat_pedagogique_personnel(
  code_projet: missing_data,
  type_activite: missing_data,
  format_mobilite: "Activité de mobilité physique",
  date_debut: missing_data,
  date_fin: missing_data,
  duree: missing_data,
  pays_ville: missing_data,
  acquis_list: (missing_data,),
  activites: (missing_data,),
  tutorings: (missing_data,),
  participant_nom : missing_data,
  participant_prenom : missing_data,
  participant_adresse: missing_data,
  participant_email: missing_data,
  participant_telephone: missing_data,
  participant_qualification: missing_data,
  participant_premier_prenom: missing_data,
  organisation_envoi_nom: missing_data,
  organisation_envoi_adresse: missing_data,
  organisation_envoi_email: missing_data,
  organisation_envoi_telephone: missing_data,
  organisation_accueil_nom: missing_data,
  organisation_accueil_adresse: missing_data,
  organisation_accueil_email: missing_data,
  organisation_accueil_telephone: missing_data,
  responsables_accueil: (
    (nom: missing_data,
    prenom: missing_data,
    email: missing_data,
    telephone: missing_data,
    fonction: missing_data,
    responsabilites: missing_data),
  ),
  responsables_envoi: (
    (nom: missing_data,
    prenom: missing_data,
    email: missing_data,
    telephone: missing_data,
    fonction: missing_data,
    responsabilites: missing_data),
  ),
  // accompagnement d'apprenants (type de mobilité « Accompagnateur ») : (nb:, periode:, periode_apprenants:)
  accompagnement: none,
  // planning : une ligne par jour (jour, matin, après-midi)
  planning: ((missing_data, missing_data, missing_data),),
  evaluation_format: missing_data,
  evaluation_criteres: missing_data,
  reconnaissance: missing_data,
  retour_lieu: missing_data,
  retour_conditions: missing_data,
  signature_envoi_nom: missing_data,
  signature_envoi_prenom: "",
  signature_accueil_nom: missing_data,
  signature_accueil_prenom: "",
  signature_participant_prenom: "",
  ..superfluous_arguments
 ) = [

#show: doc => erasmus_plus_layout(
  header_note: code_projet,
  title: "Contrat pédagogique · mobilité du personnel",
  show_title: false,
  doc
)

// « ERASMUS+ · KA121 VET » d'après le code projet (2026-1-FR01-KA121-VET-000435983)
#let parts = if type(code_projet) == str { code_projet.split("-") } else { () }
#couverture(
  kicker: [ERASMUS+ #if parts.len() >= 5 [#h(3pt)·#h(3pt) #parts.at(3) #parts.at(4)] #h(3pt)·#h(3pt) MOBILITÉ DU PERSONNEL],
  title: "Contrat pédagogique",
  translation: "Learning agreement",
  participant: [#participant_premier_prenom #text(weight: "bold", participant_nom)],
  code: code_projet,
  cles: (
    ("Destination", pays_ville),
    ("Début", date_debut),
    ("Fin", date_fin),
    ("Durée", duree),
  ),
)

= Information sur la mobilité à des fins d’apprentissage
#chap[
    
  #form((
    "Secteur": "Enseignement et formation professionnels",
    "Type d’activité":type_activite,
  ))

]


= Participant à la mobilité à des fins d’apprentissage
#chap[

=== Participant
  #form((
      "Nom":participant_nom,
      "Prénom":participant_prenom,
      "Adresse":participant_adresse,
      "Adresse mail":participant_email,
      "Téléphone":participant_telephone,
    )
  )
  
]

== Organisme d’envoi
#chap(level: 2)[

  #form((
        "Nom de l'organisme":organisation_envoi_nom,
        "Adresse":organisation_envoi_adresse,
        "Adresse mail":organisation_envoi_email,
        "Téléphone":organisation_envoi_telephone
      ))
]

== Organisme d’accueil
#chap(level: 2)[
  
  #form((
        "Nom de l'organisme":organisation_accueil_nom,
        "Adresse":organisation_accueil_adresse,
        "Adresse mail":organisation_accueil_email,
        "Téléphone":organisation_accueil_telephone
      )
    )
]

= Contexte d’apprentissage
#chap[

  #intro[
  Au sein de l’organisme d’envoi, le participant occupe actuellement la fonction de :

  #englishStyling[At the sending organisation, the participant is currently working in the following capacity :]
  ]

  === Personnel
  #form((
    "Titre qualification / profession": participant_qualification,
    "Format de mobilité": format_mobilite,
  ),wide_title: true)

  #if accompagnement != none [
    === Accompagnement d’apprenants
    #form((
      "Nombre d’apprenants accompagnés": accompagnement.nb,
      "Période d’accompagnement": accompagnement.periode,
      "Période d’activité des apprenants": accompagnement.periode_apprenants,
    ), wide_title: true)
  ]

]
= Acquis d’apprentissage
#chap[

  #intro[
  Les parties ont convenu que les acquis d’apprentissage suivants devraient être atteints au cours de la mobilité à des fins d’apprentissage :
  
  _#englishStyling[The parties have agreed that the following learning outcomes should be achieved during the learning mobility :]_
  ]

  #for acquis in acquis_list {
    [- #acquis]
  }

]
  
= Programme d’apprentissage et tâches

#chap[
  #intro[
  Pour atteindre les acquis d’apprentissage convenus, le participant réalisera les activités et tâches suivantes au cours de son activité de mobilité.
  
  _#englishStyling[To achieve the agreed learning outcomes, the participant will complete the following activities and tasks during their mobility activity.]_
  ]
    
  #for activity in activites {
    [- #activity]
  }
]

= Planning des activités
#chap[
  #tableau(("Jour", "Matin", "Après-midi"), planning, columns: (16%, 1fr, 1fr))
]

= Suivi et tutorat du participant durant l’activité

#chap[
  #for tutoring in tutorings {
    [- #tutoring]
  }
]

== Personnes responsables au sein de l’organisme d’accueil

#chap(level: 2)[

  #forms(title_key: "Responsabilités", responsables_accueil.map(personne => (
    "Nom": personne.nom,
    "Prénom":personne.prenom,
    "Adresse mail":personne.email,
    "Téléphone":personne.telephone,
    "Fonction":personne.at("fonction", default: missing_data),
    "Responsabilités":personne.responsabilites,
  )))

]


== Personnes responsables au sein de l’organisme d’envoi

#chap(level: 2)[
  // le tuteur n'a que son nom dans DN : seules les informations renseignées sont affichées
  #forms(title_key: "Responsabilités", responsables_envoi.map(personne => {
    let fiche = ("Nom": personne.at("nom", default: missing_data))
    for (cle, libelle) in (("prenom", "Prénom"), ("email", "Adresse mail"), ("telephone", "Téléphone"), ("fonction", "Fonction")) {
      if cle in personne { fiche.insert(libelle, personne.at(cle)) }
    }
    fiche.insert("Responsabilités", personne.responsabilites)
    fiche
  }))
]

= Évaluation des acquis d’apprentissage
#chap[
  === Format et procédures d’évaluation
  #puces(evaluation_format)

  === Critères d’évaluation
  #puces(evaluation_criteres)
]

= Reconnaissance des acquis d’apprentissage
#chap[#reconnaissance]

= Réintégration dans l’organisme d’envoi
#chap[
  === Lieu du retour
  #retour_lieu

  === Conditions du retour
  #retour_conditions
]

= Disposition supplémentaires
#chap[Sans objet]

// titre, texte et signatures restent ensemble (saut de page si besoin)
#block(breakable: false)[
= Signatures

#chap[
  #intro[
  Les signataires confirment qu’ils ont compris et approuvent le contenu de cet accord.
  
  #englishStyling[The signatories confirm that they understood and approve the content of this agreement.]
  ]

  #signatures((
    ("Organisme d’envoi", signature_envoi_nom, signature_envoi_prenom, organisation_envoi_nom),
    ("Organisme d’accueil", signature_accueil_nom, signature_accueil_prenom, organisation_accueil_nom),
    ("Participant", participant_nom, signature_participant_prenom),
  ))
]
]

]
