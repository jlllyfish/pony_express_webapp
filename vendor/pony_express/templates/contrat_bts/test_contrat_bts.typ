#import "contrat_bts_template.typ": *
#contrat_bts(
  mode_test: true,
  is_student: true,
  date_debut: "12/07/26",
  date_fin: missing_data,
  allocataire_type: missing_data, // fond_europeen / non_fond_europeen / fond_europeen_partiel
  organisme_envoi_nom: "MOOW ENSFEA",
  ects_credit: "432",
  debut_mobilite_virtuelle: "23/03/22",
  included_in_allocation: ("base_longues", "jours_voyage"), // base_longues, base_courtes, complement_longue, complement_courte, complement_stage, frais_voyage, jours_voyage, couts_exceptionnels, soutien_complementaire
)