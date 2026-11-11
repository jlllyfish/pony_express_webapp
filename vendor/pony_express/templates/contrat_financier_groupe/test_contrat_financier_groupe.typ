#import "contrat_financier_groupe_template.typ": *
#let app(nom) = (nom, "Apprenant", "650", "309", "959")
#let acc(nom) = (nom, "Accompagnateur", "1 500", "309", "1 809")
#contrat_financier_groupe(
  code_projet: "2026-1-FR01-KA121-VET-000435983",
  titre_activite: "Mobilité de groupe – Catane (Italie)",
  pays_ville: "Italie (IT), Catane", date_debut: "14.05.2026", date_fin: "23.05.2026", duree: "10 jours",
  organisme_envoi_nom: "EPLEFPA Perpignan-Roussillon", organisme_envoi_statut_juridique: "Établissement public local d’enseignement",
  organisme_envoi_adresse: "Route de Pia, 66000 Perpignan", organisme_envoi_email: "direction.perpignan@educagri.fr",
  organisme_envoi_code: "E10012345", organisme_envoi_representant_nom_complet: "Hélène MARTINEZ", organisme_envoi_representant_fonction: "Directrice",
  envoi_direction_nom: "Martinez", envoi_direction_prenom: "Hélène",
  duree_voyage: "2", duree_jours_bourse: "12", valeur_bourse: "8 349", frais_sejour: "6 100", frais_voyage: "2 249",
  participants_frais: (app("MARTIN Léa"), app("DURAND Hugo"), app("BENALI Inès"), app("ROUX Tom"), app("PETIT Jade"), app("FAURE Noah"), acc("HERRAIZ Camille"), acc("GENTILS Hélène")) ,
  option_prise_en_charge: "Option 2", option_libelle: "Option 2",
  assurance_responsable: "L’organisme d’envoi", compagnie_assurance: "Groupama d’Oc", numero_police_assurance: "12345678N/2001",
)
