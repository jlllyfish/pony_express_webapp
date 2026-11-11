#import "../erasmus_plus_utils/erasmus_plus_editorial.typ" : *

// taille des paragraphes d'introduction (FR + traduction) sous les titres
#let intro(body) = { set par(spacing: 0.5em, leading: 0.65em); text(size: 8pt, body) }

// Attestation de présence Europass pour les activités de groupe (démarche 156967)

#let attestation_presence_groupe(
  code_projet: missing_data,
  date_debut: missing_data,
  date_fin: missing_data,
  date_debut_en: missing_data,  // format américain mm/dd/yyyy
  date_fin_en: missing_data,
  duree: missing_data,
  pays_ville: missing_data,
  titre_activite: missing_data,
  // une ligne par personne : (prénom(s) et nom(s), organisme) — participants et accompagnateurs
  participants: ((missing_data, missing_data),),
  organisation_envoi_nom: missing_data,
  organisation_envoi_adresse: missing_data,
  envoi_direction_nom: missing_data,
  envoi_direction_prenom: "",
  organisation_accueil_nom: missing_data,
  organisation_accueil_adresse: missing_data,
  accueil_resp_nom: missing_data,
  accueil_resp_prenom: "",
  date_signature_accueil: none,  // pré-remplie : date de fin de stage
  ..superfluous_arguments
 ) = [

#show: doc => erasmus_plus_layout(
  header_note: code_projet,
  title: "Attestation de présence · activité de groupe",
  show_title: false,
  footer_extra: [L’Europass Mobilité est un document européen standard répertoriant les résultats d’une période à des fins d’apprentissage passée à l’étranger par un participant. #emph[Europass Mobility is a standard European document which records the results of a period that a person has spent abroad for learning purposes.] © European Union, 2005-2023 | https://europa.eu/europass/],
  doc
)

#couverture(
  kicker: [EUROPASS MOBILITÉ #h(3pt)·#h(3pt) ACTIVITÉ DE GROUPE],
  title: "Attestation de présence",
  translation: "Certificate of attendance",
  participant_label: "ACTIVITÉ DE GROUPE",
  participant: text(weight: "bold", titre_activite),
  code: code_projet,
  cles: (
    ("Destination", pays_ville),
    ("Début", date_debut),
    ("Fin", date_fin),
    ("Durée", duree),
  ),
  compact: true,
)

= Attestation de participation
#chap[
  #intro[
  Après la mobilité : la signature de l’organisme d’envoi ou de l’organisme d’accueil est obligatoire.

  _#englishStyling[Post-mobility: signature of either sending organisation or hosting organisation is obligatory.]_
  #v(4pt)
  Les organisations soussignées certifient la validité et l’exactitude des informations contenues dans le présent document.

  _#englishStyling[The undersigned organisation(s) certify the validity and accuracy of the information contained in this document.]_
  #v(4pt)
  Les signataires confirment que les participants ont participé à l’activité de mobilité de groupe décrite dans le contrat pédagogique Erasmus+ annexé et qu’ils ont atteint les acquis d’apprentissage spécifiés.

  _#englishStyling[The signatories confirm that the participants have attended the learning mobility activity described in the annexed Erasmus+ learning agreement, and have attained the specified learning outcomes.]_
  ]

  #v(6pt)
  L’activité de mobilité s’est déroulée du *#date_debut* au *#date_fin*. \
  #text(8pt, en[The mobility activity took place from #date_debut_en to #date_fin_en.])
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
  #signatures((
    (titre: "Organisme d’envoi", organisme: organisation_envoi_nom, adresse: organisation_envoi_adresse,
     nom: envoi_direction_nom, prenom: envoi_direction_prenom,
     fonction: [Personne responsable · #en("Responsible person")], date_label: "Date"),
    (titre: "Organisme d’accueil", organisme: organisation_accueil_nom, adresse: organisation_accueil_adresse,
     nom: accueil_resp_nom, prenom: accueil_resp_prenom,
     fonction: [Personne responsable · #en("Responsible person")], date_label: "Date",
     date: date_signature_accueil),
  ))
]
]


]
