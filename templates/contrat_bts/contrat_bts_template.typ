#import "../erasmus_plus_utils/erasmus_plus_editorial.typ" : * 
#import "../erasmus_plus_utils/legal_template_utils.typ" : * 
#import "../erasmus_plus_utils/erasmus_translation.typ" : * 

#let contrat_bts(
  project_code: missing_data,
  annee_academique: missing_data,
  langue: missing_data,
  organisme: missing_data,
  organisme_adresse: missing_data,
  organisme_email: missing_data,
  organisme_contact_nom: missing_data,
  organisme_person_fonction: missing_data,
  participant: missing_data,
  participant_adresse: missing_data,
  participant_telephone: missing_data,
  participant_email: missing_data,
  participant_nom: missing_data,
  participant_prenom: missing_data,
  participant_naissance: missing_data,
  participant_nationalite: missing_data,
  participant_genre: missing_data,
  participant_niveau_CEC: "CEC niveau 5",
  participant_niveau_langue: missing_data,
  participant_domaine_etude: "08 – Agriculture, forestry, fisheries and veterinary",
  participant_banque_titulaire: missing_data,
  participant_nom_banque: missing_data,
  participant_bic_swift: missing_data,
  participant_iban: missing_data,
  is_student: true,
  allocataire_type: missing_data, // fond_europeen / non_fond_europeen / fond_europeen_partiel
  inclut_dans_allocation: (),  // peut contenir :  base_longues, base_courtes, complement_longue, complement_courte, complement_stage, frais_voyage, jours_voyage, couts_exceptionnels, soutien_complementaire
  date_debut: missing_data,
  date_fin: missing_data,
  debut_mobilite_totale: missing_data,
  fin_mobilite_totale: missing_data,
  debut_mobilite_physique: missing_data,
  fin_mobilite_physique: missing_data,
  debut_mobilite_virtuelle: missing_data,
  fin_mobilite_virtuelle: missing_data,
  nb_jours: missing_data,
  nb_jour_prolongation_max: missing_data,
  somme_pour_voyage: missing_data,
  organisme_beneficiaire_nom: missing_data, // same as organisme ?
  organisme_beneficiaire_faculte: missing_data,
  organisme_beneficiaire_code_erasmus: missing_data,
  organisme_beneficiaire_adresse: missing_data,
  organisme_beneficiaire_pays: missing_data,
  organisme_beneficiaire_contact_nom_email : missing_data,
  organisme_envoi_nom: missing_data,
  organisme_envoi_faculte: missing_data,
  organisme_envoi_code_erasmus: missing_data,
  organisme_envoi_adresse: missing_data,
  organisme_envoi_pays: missing_data,
  organisme_envoi_contact_nom : missing_data,
  organisme_envoi_contact_email : missing_data,
  organisme_accueil_nom: missing_data,
  organisme_accueil_faculte: missing_data,
  organisme_accueil_secteur_activite: missing_data,
  organisme_accueil_code_erasmus: missing_data,
  organisme_accueil_adresse: missing_data,
  organisme_accueil_site_web: missing_data,
  organisme_accueil_pays: missing_data,
  organisme_accueil_contact_nom : missing_data,
  organisme_accueil_contact_email : missing_data,
  organism_accueil_more_than_250: true,
  organisme_accueil_tuteur_nom_email: missing_data,
  intitule_stage: missing_data,
  nombre_heures_hebdo: missing_data,
  programme_detaille: missing_data,
  stage_domaine_competences_numeriques: missing_data,
  connaisance_a_acquerir: missing_data,
  plan_suivi: missing_data,
  plan_evaluation: missing_data,
  stage_optionnel: true,
  ects_credit: missing_data,
  support_evaluation: missing_data, // must be one of attestation de stage/rapport final/ entretien
  mention_sur_diplome: true,
  mention_sur_releve: true,
  mention_sur_europass: true,
  organisme_envoi_assurance_accident_travail: true,
  organisme_envoi_assurance_trajet_domicile: true,
  organisme_envoi_assurance_deplacement_professionnel : true,
  organisme_envoi_assurance_responsabilite_civile: true,
  organisme_accueil_assurance_accident_travail: true,
  organisme_accueil_assurance_trajet_domicile: true,
  organisme_accueil_assurance_deplacement_professionnel : true,
  organisme_accueil_assurance_responsabilite_civile: true,
  organisme_accueil_montant_support_financier: missing_data,
  organisme_accueil_avantage_nature: missing_data,
  organisme_accueil_avantage_nature_english: missing_data,
  changement_pendant_mobilite_debut_mobilite_virtuelle: missing_data,
  changement_pendant_mobilite_fin_mobilite_virtuelle: missing_data,
  changement_pendant_mobilite_debut_mobilite_physique: missing_data,
  changement_pendant_mobilite_fin_mobilite_physique: missing_data,
  changement_pendant_mobilite_intitule_stage: missing_data,
  changement_pendant_mobilite_nombre_heures_hebdo: missing_data,
  changement_pendant_mobilite_programme_detaille: missing_data,
  changement_pendant_mobilite_stage_domaine_competences_numeriques: missing_data,
  changement_pendant_mobilite_connaisance_a_acquerir: missing_data,
  changement_pendant_mobilite_plan_suivi: missing_data,
  changement_pendant_mobilite_plan_evaluation: missing_data,
  evaluation_participant: missing_data,
  ..superfluous_arguments
 ) = [

#show: doc => erasmus_plus_layout(
  title:[MOBILITES DE L’ENSEIGNEMENT SUPERIEUR AC 131], 
  activate_translation: false,
  doc
)
   
#erasmus_title("Contrat entre bénéficiaire et participant") #label("b")


#chap[

  #form((
        "Code Projet": custom_data(project_code),
        "Domaine": "enseignement supérieur",
        "Année académique": custom_data(annee_academique),
        "Numéro d'identification de la mobilité Erasmus": custom_data(annee_academique),
      ),
      wide_title: true
  )
]

= Préambule
#chap[
  
  Ce *contrat* (“le contrat”) est conclu entre les parties suivantes :  

  *d'une part*, L’Organisme (”l’organisme”)

  Nom officiel complet de l’organisme d’envoi : #custom_data(organisme)

  Adresse officielle complète : #custom_data(organisme_adresse)

  E-mail : #custom_data(organisme_email)

  Représenté aux fins de la signature du présent contrat par :

  Nom(s) et prénom(s) : #custom_data(organisme_contact_nom)
  
  Fonction :#custom_data(organisme_person_fonction)

  *et d'autre part*, Le “participant”

  Nom(s) et prénom(s) : #custom_data(participant)
      
  Adresse officielle complète : #custom_data(participant_adresse)
    
  Téléphone : #custom_data(participant_telephone)	
    
  E-mail : #custom_data(participant_email)

  Numéro de compte bancaire sur lequel l’aide financière sera versée :

  Titulaire du compte : #custom_data(participant_banque_titulaire)

  Nom de la banque : #custom_data(participant_nom_banque)

  Clearing/BIC/SWIFT : #custom_data(participant_bic_swift)

  IBAN : #custom_data(participant_iban)

  Les parties mentionnées ci-dessus sont convenues de conclure le présent accord.

  Le contrat est composé de :

  - Annexe 1 :   #text(red, "TODO Que GARDER ICI ?")
 #custom_data[Contrat pédagogique Erasmus+ pour la mobilité d’études des étudiants / 
            contrat pédagogique Erasmus+ pour la mobilité de stage des étudiants / 
            contrat de mobilité Erasmus+ pour la mobilité d’enseignement / 
            contrat de mobilité Erasmus+ pour la mobilité de formation des personnels#footnote("L’annexe I ne devra pas obligatoirement comporter les signatures originales, les signatures scannées et électroniques sont acceptées, selon la législation nationale ou la réglementation institutionnelle en vigueur. [Option pour les mobilités d’études de l’AC131 : les contrats pédagogiques devront être échangés et signés digitalement via le reseau Erasmus Without Paper].")]

  #if (is_student) [
    - Annexe 2: Charte de l’étudiant Erasmus
  ]

  Les conditions générales prévalent sur les annexes.

  Le participant est
  #if (allocataire_type == "fond_europeen") [
    #custom_data[allocataire de fonds européens Erasmus +]
  ] else if (allocataire_type == "non_fond_europeen") [
    #custom_data[non-allocataire de fonds européens Erasmus +]
  ] else [
    #custom_data[partiellement allocataire de fonds européens Erasmus +]
  ]

  L’allocation totale comprend  :

 
  #let allocation_options = (
    base_longues: "Allocation de base pour la contribution aux frais de séjour des mobilités physiques longues",
    base_courtes: "Allocation de base pour la contribution aux frais de séjour des mobilités physiques courtes",
    complement_longue: "Complément pour étudiant avec moins d’opportunités mobilité longue",
    complement_courte: "Complément pour étudiant avec moins d’opportunités mobilité courte",
    complement_stage: "Complément applicable aux mobilités de stage",
    frais_voyage: "Frais de voyage (écoresponsable ou standard)",
    jours_voyage: "Jours de voyage (jours supplémentaires à la contribution aux frais de séjour)",
    couts_exceptionnels: "Coûts exceptionnels pour frais de voyage élevés (basés sur les frais réels) [non applicable pour l’AC171]",
    soutien_complementaire: "Soutien complémentaire pour l’inclusion (basé sur frais réels)"
  )

  #for option in inclut_dans_allocation [
    - #custom_data(allocation_options.at(option))
  ]

]

= Conditions générales

  #article[objet du contrat]

  #mention[
  Le présent accord définit les droits, obligations et conditions applicables au soutien financier accordé pour la réalisation d’une activité de mobilité dans le cadre du programme Erasmus+.
  ]

  #mention[L’organisme apportera son soutien au participant dans la mise en œuvre d’une activité de mobilité.]

  #mention[Le participant accepte l’aide financière ou les prestations de services indiquées à l’article 3 et s’engage à réaliser le programme de mobilité tel que défini dans l’annexe I.]

  #mention[Tout avenant à ce contrat devra être demandé et accepté par les deux parties de manière formelle, par voie postale ou électronique.]

  #article[Durée de la mobilité]

  #mention[La période de mobilité commencera le #custom_data(date_debut) et prendra fin le #custom_data(date_fin)]

  #mention[La période couverte par le contrat comprend :]

  text(red, [   
    • a physical mobility period from [date] to [date], equal to [number of mobility days] days 
        une période de mobilité physique du [date] au [date], correspondant à [nombre de jours de mobilité] jours
      • [Option […] funded travel days]
        [Option […] jours de voyage financés]
      • [Option for blended mobility: a virtual component from [date] to [date]]
        [Option pour les mobilités hybrides : une composante virtuelle du [date] au [date]]])

  #mention[L’attestation de présence (ou tout justificatif annexé à ce document) devra comporter les dates effectives de début et de fin de mobilité, y compris celles de la composante virtuelle.]
  }

  #article[Soutien financier et autre]

  #mention[L’aide financière est calculée sur la base des règles financières du guide du programme Erasmus+ [version 2025].]
  #mention[Le participant recevra une aide financière des fonds Erasmus+ de l'UE pour #custom_data(nb_jours) jours]
  #mention[Le participant peut soumettre une demande de prolongation de la période de mobilité physique dans la limite de la durée maximum fixée dans le guide du programme Erasmus+ 2025 de #custom_data(nb_jour_prolongation_max) jours . Si l'organisme accepte de prolonger la durée de la période de mobilité, le contrat sera modifié en conséquence.]
  #mention[L’organisme versera au participant une aide financière totale pour la période de mobilité #text(red, [Option si applicable]): et jours de voyage d’un montant de #custom_data(somme_pour_voyage) euros #text(red, [Option pour les participants non allocataires  0])]
  #mention[L’aide financière accordée pour #text(red, [au choix si applicable : soutien complémentaire à l’inclusion au frais réels, frais exceptionnels pour frais de voyage élevés, frais de voyage, complément inclusion participants avec moins d’opportunité)]) sera basée sur les documents justificatifs fournis par le participant.]
  #article[Droit au soutien financier]
  #mention[Le participant a droit à un soutien financier sur la base de l'article 3 ci-dessus s'il a effectivement entrepris l'activité au cours de la période visée à l'article 2. Lorsque le soutien financier est basé sur des coûts réels, ceux-ci doivent être fondés sur des pièces justificatives telles que des factures, des reçus, etc.]
  #mention[Le participant a droit à un soutien financier sur la base de l'article 3 ci-dessus s'il a effectivement entrepris l'activité au cours de la période visée à l'article 2. Lorsque le soutien financier est basé sur des coûts réels, ceux-ci doivent être fondés sur des pièces justificatives telles que des factures, des reçus, etc.]
  #mention[Le participant ne peut pas demander le remboursement des frais de change ou des frais bancaires facturés par sa banque pour les virements effectués par l'organisme.]

  #article[Modalités de paiement]
  #mention[Le paiement devra être fait au plus tard (selon l’option qui interviendra en premier) :
	- 30 jours calendaires après la signature du contrat par les 2 parties
  
Le paiement fait au participant devra représente80% du montant spécifié à l’article 3. Dans le cas où le participant ne fournit pas les documents requis dans les délais impartis fixés par l’organisme financeur, un report du délai de paiement du préfinancement pourra être exceptionnellement accepté s’il est justifié.]
  
  #mention[La soumission en ligne du rapport du participant via l’outil EU survey sera considérée comme demande de paiement du solde par le participant. L’organisme disposera de 45 jours calendaires pour effectuer le versement du solde ou émettre un ordre de reversement en cas de remboursement.]

  #article[Remboursement du soutien financier par le participant]

  #mention[Si le participant ne respecte pas les termes de l'accord ou met fin à l'accord avant son terme pour des raisons autres que celles mentionnées à l'article 13.1, le participant devra restituer le montant du soutien financier déjà versé, sauf accord contraire avec l’organisme. Ce dernier doit être signalé par l’organisme et accepté par l'Agence nationale.]

  #article[Assurance] 
  #mention[L’organisme devra s’assurer que le participant bénéficie d’une couverture adéquate en matière d’assurances avant le début de la mobilité, soit en lui fournissant les assurances nécessaires, soit en ayant un accord avec l’organisme d’accueil afin que ce dernier couvre le participant, ou en apportant au participant l’information et l’aide afin qu’il puisse contracter une assurance par ses propres moyens]

  #mention[
La couverture devra inclure au minimum une assurance santé, [obligatoire pour les mobilités de stage et optionnel pour les autres types de mobilité] : une assurance responsabilité civile et assurance accident du travail.
	#text(green, [Explications : dans le cas d’une mobilité intra européenne, l’étudiant est couvert par son régime de sécurité sociale étudiant pour la prise en charge de base des soins médicaux lors de son séjour à l’étranger, par le biais de la Carte Européenne d’Assurance Maladie (CEAM). Cependant, cette couverture peut s’avérer insuffisante dans certaines situations, notamment pour un rapatriement ou une intervention médicale spécifique ou dans le cadre d’une mobilité internationale hors Europe. Dans ce cas, une assurance santé complémentaire peut s’avérer nécessaire. Les assurances responsabilité civile et accident du travail couvrent les dommages causés par le participant ou au participant pendant son séjour. La réglementation de ces assurances varie d'un pays à l'autre et les participants courent le risque de ne pas être couverts par les régimes standards, par exemple s'ils ne sont pas considérés comme des employés ou officiellement inscrits dans l’organisme d'accueil. De plus, il est recommandé de souscrire une assurance contre la perte ou le vol de documents, de billets de voyage et de bagages. L'Agence nationale peut modifier l'article 7.2 s'il est justifié d'adapter les exigences par défaut au contexte national.])
	Il est recommandé d’indiquer les informations suivantes : #text(red,"compagnie d’assurance type et numéro de police.")]

#mention[La partie responsable de la souscription de l’assurance pour la durée de la mobilité est le participant OU l’établissement d’accueil. 
En cas d'assurances distinctes, les parties responsables peuvent être différentes et seront énumérées ici en fonction de leurs responsabilités respectives.]

#article[Niveau linguistique et aide linguistique en ligne]
#mention[Le participant peut effectuer l'évaluation linguistique OLS dans la langue de mobilité (si elle est disponible) avant la période de mobilité et utiliser les cours de langue disponibles sur la plateforme OLS (EU ACADEMY).]

#mention[Le niveau de compétence linguistique en #custom_data(langue) que le participant possède ou s’engage à acquérir avant le début de la mobilité est : #custom_data(participant_niveau_langue)]

#article[Rapport du participant]
#mention[Le participant devra compléter et soumettre le rapport du participant (via l’outil en ligne EU Survey), dans un délai de 10 /: 30 jours calendaires suivant la réception de l’invitation à le faire. Les participants qui ne complètent pas et qui ne soumettent pas leur rapport seront susceptibles de rembourser partiellement ou intégralement l’aide financière reçue à l’organisme financeur.]
#mention[Un rapport en ligne complémentaire portant sur les questions de reconnaissance pourra être envoyé au participant.]

#article[Éthique et valeurs]
#mention[L'activité de mobilité doit être menée dans le respect des normes éthiques les plus élevées et des législations européenne, internationale et nationale applicables.]
#mention[Les parties doivent s'engager à respecter les valeurs fondamentales de l'UE (telles que le respect de la dignité humaine, de la liberté, de la démocratie, de l'égalité, de l'État de droit et des droits de l'homme, y compris les droits des minorités) et veiller à ce qu'elles soient respectées.]
#mention[Si un participant manque à l'une des obligations qui lui incombent en vertu du présent article, l'allocation peut être réduite ou non payée.]

#article[Protection des données]
#mention[Toute donnée personnelle dans le cadre de l'accord sera traitée sous la responsabilité du responsable du traitement des données identifié dans la déclaration de confidentialité, conformément à la législation applicable en matière de protection des données, en particulier le règlement 2018/1725 et les lois nationales relatives à la protection des données, et aux fins énoncées dans la déclaration de confidentialité disponible à l'adresse suivante : https://webgate.ec.europa.eu/erasmus-esc/index/privacy-statement]

#mention[Ces données seront traitées uniquement dans le cadre de la mise en œuvre et du suivi de la convention par l'organisme, l'agence nationale et la Commission européenne, sans préjudice quant à la possibilité de transmission de ces données aux organes chargés du contrôle et de l'audit conformément à la législation de l'UE (Cour des comptes ou Office européen de lutte antifraude (OLAF)).]

#mention[Le participant peut, sur demande écrite, avoir le droit d’accéder à ses données personnelles pour les modifier en cas d’erreur et pour les compléter. Il adressera toute question concernant l’utilisation de ses données personnelles à l’organisme et/ou à l’Agence nationale. Le participant peut porter plainte contre l’utilisation de ses données personnelles auprès du Contrôleur européen de protection des données (CEPD) en ce qui concerne l’utilisation de celles-ci par la Commission européenne.]

#article[Suspension du contrat]

#mention[L'accord peut être suspendu à l'initiative du participant ou de l'organisme si des circonstances exceptionnelles - notamment de force majeure (voir article 16) - en rendent l'exécution impossible ou excessivement difficile. La suspension prend effet le jour convenu par notification écrite des parties. L'accord peut être repris par la suite.
]

#mention[Chacune des parties peut, à tout moment, suspendre l'accord si l’autre partie a commis ou est soupçonnée d'avoir commis :
#set enum(numbering: "a)")

+ des erreurs substantielles, des irrégularités ou des fraudes, ou 
+ un manquement grave aux obligations découlant de la présente convention ou au cours de son attribution (y compris la mise en œuvre incorrecte de l'action, la présentation de fausses informations, le manquement à l'obligation de fournir les informations requises, le manquement aux règles d'éthique (le cas échéant), etc.).]

#mention[Lorsque les circonstances permettent la reprise de la mise en œuvre, les parties doivent immédiatement convenir de la date de reprise (un jour après la date de fin de la suspension). La suspension sera levée à compter de la date de fin de la suspension]

#mention[Pendant la suspension, aucune aide financière ne sera versée au participant.]

#mention[Le participant ne peut prétendre à des dommages et intérêts du fait de la suspension par l'organisme.]

#mention[La suspension n'affecte pas le droit de l'organisation de mettre fin à l'accord (voir article 13).]

#article[Résiliation du contrat]

#mention[L'accord peut être résilié par l'une ou l'autre des parties si des circonstances qui surviennent rendent l'exécution de l'accord irréalisable, impossible ou excessivement difficile.]

#mention[En cas de résiliation, le participant aura le droit de recevoir au moins le montant du soutien financier correspondant à la durée réelle de la période d'activité. Le participant devra restituer les fonds restants.]

#mention[En cas de manquement grave aux obligations ou si l'une des parties a commis des irrégularités, une fraude, une corruption ou est impliquée dans une organisation criminelle, un blanchiment d'argent, des crimes liés au terrorisme (y compris le financement du terrorisme), le travail des enfants ou la traite des êtres humains, l'autre partie peut mettre fin à l'accord par le biais d'une notification formelle.]

#mention[L'organisme se réserve le droit d'intenter une action en justice si le remboursement demandé n'est pas effectué volontairement dans le délai notifié au participant par lettre recommandée.]

#mention[La résiliation prendra effet à la date indiquée dans la notification comme étant la « date de résiliation ».]

#mention[Le participant ne peut prétendre à des dommages et intérêts du fait de la résiliation par l'organisme.]

#article[Vérifications et audits]

#mention[Les contractants s’engagent à fournir toute information détaillée demandée par la Commission européenne, l’Agence nationale #strong[française] ou tout autre organisme extérieur accrédité par la Commission européenne et l’Agence nationale #strong[française] pour vérifier que la période de mobilité et les dispositions prévues au contrat sont ou ont été mises en œuvre de manière conforme.]

#mention[Toute constatation relative à l'accord peut donner lieu aux mesures prévues à l'article 6 ou à d'autres actions en justice dans les conditions prévues par le droit national applicable.]

#article[Dommages]
#mention[Chaque partie contractante décharge l’autre partie contractante de toute responsabilité civile pour les dommages subis par elle-même ou son personnel résultant de l’exécution du présent contrat, pour autant que ces dommages ne résultent pas d’une faute grave et intentionnelle de l’autre partie contractante ou de son personnel.]

#mention[La responsabilité de l'Agence nationale #strong[française], de la Commission européenne ou de leurs personnels ne sera pas engagée en cas d’action en réparation des dommages pendant la réalisation de la période de mobilité. En conséquence, l’Agence nationale #strong[française] ou la Commission européenne ne donneront suite à aucune demande d’indemnité de remboursement en cas de réclamation.]

#article[Force majeure]

#mention[Une partie empêchée par une force majeure de remplir ses obligations en vertu de l'accord ne peut être considérée comme les ayant enfreintes.]

#mention[On entend par « force majeure » toute situation ou tout événement qui :
- empêche l'une ou l'autre des parties de remplir ses obligations au titre de l'accord
- était imprévisible, exceptionnel et indépendant de la volonté des parties
- n'est pas dû à une erreur ou à une négligence de leur part (ou de la part d'autres entités participant à l'action), et
- s'avère inévitable malgré l'exercice de toute la diligence requise.]

#mention[Toute situation constituant un cas de force majeure doit être notifiée formellement et sans délai à l'autre partie, en précisant sa nature, sa durée probable et ses effets prévisibles.]

#mention[Les parties doivent immédiatement prendre toutes les mesures nécessaires pour limiter les dommages dus à la force majeure et faire de leur mieux pour reprendre la mise en œuvre de l'action dès que possible.]

#article[Loi applicable et tribunal compétent]
#mention[Ce contrat est régi par le droit #strong[français].]
#mention[Le tribunal compétent déterminé conformément à la législation nationale applicable sera seul compétent pour entendre tout litige entre l’établissement et le participant concernant l’interprétation, l’application ou la validité de ce contrat, si ce litige ne peut pas être réglé à l’amiable.]

#article[Entrée en vigueur]
#mention[L'accord entrera en vigueur le jour de la signature par l'organisation ou le participant, selon la date la plus tardive.]

= Signatures

#signatures((
  "Participant": custom_data(participant),
  "Organisme" : custom_data(organisme)
))

#pagebreak()
#erasmus_title("Annexe I: Contrat pédagogique - mobilité étudiante de stage")

= Contrat pédagogique - mobilité étudiante de stages

Année académique/#englishStyling[Academic year] #custom_data(annee_academique)

=== Stagiaire
#form((
    "Nom":custom_data(participant_nom),
    "Prénom":custom_data(participant_prenom),
    "Date de naissance":custom_data(participant_naissance),
    "Nationalité":custom_data(participant_nationalite),
    "Genre (M/F/Non défini)":custom_data(participant_genre),
    "Niveau d'études (niveau CEC)": custom_data(participant_niveau_CEC), 
    "Domaine d'étude": custom_data(participant_domaine_etude),
  ),
  wide_title: true
)

Niveau d'études (niveau CEC)#footnote[
  Cycle court (CEC niveau 5) / Licence ou équivalent 1er cycle (CEC niveau 6) / Master ou équivalent 2ème cycle (CEC niveau 7) / Doctorat ou équivalent 3ème cycle (CEC niveau 8). 
  #linebreak()
  #englishStyling[Short cycle (EQF level 5) / Bachelor or equivalent first cycle (EQF level 6) / Master or equivalent second cycle (EQF level 7) / Doctorate or equivalent third cycle (EQF level 8). EQF level codes 5 to 8 are equivalent to the ISCED levels 5 to 8.]]

Domaine d'étude #footnote[
  l’outil de recherche CITE-F 2013 disponible sur http://ec.europa.eu/education/tools/isced-f_en.htm détaille les domaines de l'enseignement et de la formation qui se rapprochent le plus du diplôme qui sera délivré au stagiaire par l’organisme d’envoi.
  #linebreak()
  #englishStyling[The ISCED-F 2013 search tool available at http://ec.europa.eu/education/tools/isced-f_en.htm detailed field of education and training that is closest to the subject of the degree to be awarded to the trainee by the sending institution.]]

=== Organisme bénéficiaire
#form((
    "Nom":custom_data(organisme_beneficiaire_nom),
    "Faculté/Département":custom_data(organisme_beneficiaire_faculte),
    "Code Erasmus (si applicable)" :custom_data(organisme_beneficiaire_code_erasmus),
    "Adresse":custom_data(organisme_beneficiaire_adresse),
    "Pays":custom_data(organisme_beneficiaire_pays),
    "Nom et email de la personne contact":custom_data(organisme_beneficiaire_contact_nom_email)
  ),
  wide_title: true
  )

Code Erasmus #footnote[
  identifiant unique pour tout établissement d’enseignement supérieur titulaire de la charte Erasmus pour l’enseignement supérieur (ECHE). Concerne uniquement les établissements situés dans les pays membres de l’Union européenne et les pays tiers associés au programme.
  #linebreak()
  #englishStyling[
  a unique identifier that every higher education institution that has been awarded with the Erasmus Charter for Higher Education (ECHE) receives. It is only applicable to higher education institutions located in EU Member States and third countries associated to the programme.
  ]
]

#if (organisme_envoi_nom != missing_data){

[=== Organisme d’envoi]
form((
    "Nom":custom_data(organisme_envoi_nom),
    "Faculté/Département":custom_data(organisme_envoi_faculte),
    "Code Erasmus (si applicable)": custom_data(organisme_envoi_code_erasmus),
    "Adresse":custom_data(organisme_envoi_adresse),
    "Pays":custom_data(organisme_envoi_pays),
    "Nom et email de la personne contact":custom_data([#organisme_envoi_contact_nom, #organisme_envoi_contact_email])
  ),
  wide_title: true
)

[Code Erasmus #footnote[
  identifiant unique pour tout établissement d’enseignement supérieur titulaire de la charte Erasmus pour l’enseignement supérieur (ECHE). Concerne uniquement les établissements situés dans les pays membres de l’Union européenne et les pays tiers associés au programme.
  #linebreak()
  #englishStyling[
  a unique identifier that every higher education institution that has been awarded with the Erasmus Charter for Higher Education (ECHE) receives. It is only applicable to higher education institutions located in EU Member States and third countries associated to the programme.
  ]
]]
}



=== Organisme d'accueil

Tuteur #footnote[son rôle est d’apporter aide, encouragement et information au stagiaire sur la vie et l’expérience de l’entreprise (culture d’entreprise, codes informels et comportements, etc..). Normalement, le tuteur et le superviseur doivent être deux personnes différentes.
#linebreak()
#englishStyling[the role of the mentor is to provide support, encouragement and information to the trainee on the life and experience relative to the organisation (culture of the organisation, informal codes and conducts, etc.). Normally, the mentor should be a different person than the supervisor.]
]

#let taille = if (organism_accueil_more_than_250) {"Plus de 250 employés"} else {"Moins de 250 employés"}

#form((
    "Nom":custom_data(organisme_accueil_nom),
    "Département":custom_data(organisme_accueil_faculte),
    "Site web":custom_data(organisme_accueil_code_erasmus),
    "Adresse":custom_data(organisme_accueil_adresse),
    "Pays":custom_data(organisme_accueil_pays),
    "Taille":custom_data(taille),
    "Nom et email de la personne contact":custom_data([#organisme_accueil_contact_nom, #organisme_accueil_contact_email]),
    "Nom, email, position du tuteur":custom_data(organisme_accueil_tuteur_nom_email)
  ),
  wide_title: true
)

#pagebreak()

== Avant la mobilité

=== Programme de stage dans l'organisme d'accueil

#let virtual_mobility_field



Stage dans le domaine des compétences numériques #footnote[
  tout stage au cours duquel le stagiaire se forme et met en pratique une ou plusieurs des activités suivantes : marketing numérique (exemples : gestion de médias sociaux, analyse Web) ; conception numérique graphique, mécanique ou architecturale; développement d’applications, de logiciels, de scripts ou de sites ; installation, maintenance et gestion de systèmes et de réseaux informatiques ; sécurité des systèmes d’informations ; analyse de données ; extraction et visualisation ; programmation et tests d’applications pour robots et intelligence artificielle. Assistance clients, réalisation de commandes, saisies de données et tâches administratives ne sont pas concernées.
  #linebreak()
  #englishStyling[any traineeship where trainees receive training and practice in at least one or more of the following activities: digital marketing (e.g. social media management, web analytics); digital graphical, mechanical or architectural design; development of apps, software, scripts, or websites; installation, maintenance and management of IT systems and networks; cybersecurity; data analytics, mining and visualisation; programming and training of robots and artificial intelligence applications. Generic customer support, order fulfilment, data entry or office tasks are not considered in this category.]
]

#let form_dict = (
  "Période de mobilité physique":[#custom_data(debut_mobilite_physique) à #custom_data(fin_mobilite_physique)],
  "Intitulé du stage": custom_data(intitule_stage),
  "Nombre d'heures travaillées par semaine":custom_data(nombre_heures_hebdo),
  "Programme détaillé du stage (y compris la composante virtuelle si applicable)":custom_data(programme_detaille),
  "Stage dans le domaine des compétences numériques" : custom_data(stage_domaine_competences_numeriques),
  "Connaissances, aptitudes et compétences à acquérir par le stagiaire au cours du stage (résultats d’apprentissage attendus)": custom_data(connaisance_a_acquerir),
)

#if (debut_mobilite_virtuelle != missing_data){
  form_dict.insert("Période de mobilité virtuelle", [#custom_data(debut_mobilite_virtuelle) à #custom_data(fin_mobilite_virtuelle)])
}

#form(
  form_dict,
  wide_title: true
)

compétence linguistique #footnote[une information sur le Cadre Européen Commun de Référence pour les langues (CECR) est disponible sur :
https://europass.cedefop.europa.eu/en/resources/european-language-levels-cefr
#linebreak()
#englishStyling[a description of the European Language Levels (CEFR) is available at: https://europass.cedefop.europa.eu/en/resources/european-language-levels-cefr]
]

#form((
  "Plan de suivi": custom_data(plan_suivi),
  "Plan d'évaluation":custom_data(plan_evaluation),
  "Langue": custom_data(langue),
  "Niveau de compétence linguistique que le stagiaire possède ou s’engage à acquérir avant le début de la période de stage": custom_data(participant_niveau_langue)
  ), 
  wide_title: true
)

=== Organisme d'envoi

#if stage_optionnel [
  Le stage est optionnel (facultatif) et, sous réserve d’une réalisation satisfaisante, l’établissement s’engage à :

  _#englishStyling[The traineeship is voluntary and, upon satisfactory completion of the traineeship, the institution undertakes to:]_

  #if ects_credit != missing_data [
    - Attribuer #custom_data(ects_credit) crédits ECTS (ou équivalent#footnote[dans les pays où le système ECTS n’est pas utilisé, le système « ECTS » devra être remplacé dans tous les tableaux par le système équivalent, et un lien internet vers une explication du système devra être ajouté.]
     
      _#englishStyling[Award #custom_data(ects_credit) ECTS credits (or equivalent)#footnote[#englishStyling[in countries where the "ECTS" system it is not in place, "ECTS" needs to be replaced in all tables by the name of the equivalent system that is used and a web link to an explanation to the system should be added.]]]_
  ]

  #if support_evaluation != missing_data [
    - Attribuer une note sur la base de #custom_data(support_evaluation)

      _#englishStyling[Give a grade based on #custom_data(custom_data(translate(support_evaluation)))]_
  ]

] else /*Stage Obligatoire*/ [

  La période de stage fait partie intégrante du programme d’études et, sous réserve d’une réalisation satisfaisante, l’établissement s’engage à : \
  #englishStyling[The traineeship is embedded in the curriculum and upon satisfactory completion of the traineeship, the institution undertakes to:]

  - Attribuer #custom_data(ects_credit) crédits ECTS (ou équivalent)#footnote[dans les pays où le système ECTS n’est pas utilisé, le système « ECTS » devra  être remplacé dans tous les tableaux par le système équivalent, et un lien internet vers une explication du système devra être ajouté.]\
    #englishStyling[Award #custom_data(ects_credit) ECTS credits (or equivalent)#footnote[in countries where the "ECTS" system it is not in place, "ECTS" needs to be replaced in all tables by the name of the equivalent system that is used and a web link to an explanation to the system should be added.]]

  - Attribuer une note sur la base de #custom_data(support_evaluation) \
    #englishStyling[Give a grade based on #custom_data(custom_data(translate(support_evaluation)))]
]

  #if mention_sur_releve [
    - Indiquer la période de stage dans le relevé de notes du stagiaire \
      #englishStyling[Record the traineeship in the trainee's Transcript of Records]
  ]

  #if mention_sur_diplome [
    - Indiquer la période de stage dans le supplément au diplôme (ou équivalent) du stagiaire \
      #englishStyling[Record the traineeship in the trainee's Diploma Supplement (or equivalent)]
  ]

  #if mention_sur_europass [
    - Indiquer la période de stage dans l’Europass Mobilité du stagiaire \
      #englishStyling[Record the traineeship in the trainee's Europass Mobility Document]
  ]

  #if organisme_envoi_assurance_accident_travail or organisme_envoi_assurance_responsabilite_civile [
  \
  Assurance accident du travail pour le stagiaire\
  #englishStyling[Accident insurance for the trainee]\
  \
  ]
  #if organisme_envoi_assurance_accident_travail [
    L’organisme bénéficiaire fournira au stagiaire une assurance accident du travail (s’il n’est pas assuré par l’organisme d’accueil)\
    #englishStyling[The beneficiary organisation will provide an accident insurance to the trainee (if not provided by the Receiving Organisation)]
  ]

  #if organisme_envoi_assurance_deplacement_professionnel [
    - L’assurance accident couvre les accidents survenus pendant les déplacements professionnels.\
      #englishStyling[The accident insurance covers accidents during travels made for work purposes]
  ]

  #if organisme_envoi_assurance_trajet_domicile [
    - L’assurance accident couvre les accidents survenus sur les trajets domicile-travail.\
      #englishStyling[The accident insurance covers accidents on the way to work and back from work]
  ]

  #if organisme_envoi_assurance_responsabilite_civile [
    L’organisme bénéficiaire fournira au stagiaire une assurance accident du travail (s’il n’est pas assuré par l’organisme d’accueil).\
    #englishStyling[The beneficiary organisation will provide a liability insurance to the trainee (if not provided by the Receiving Organisation)]
  ]

=== Organisme d'accueil

#if organisme_accueil_montant_support_financier != missing_data [
  L’organisme d’accueil accordera au stagiaire une aide financière pendant son stage.
  Le montant est de #organisme_accueil_montant_support_financier euros
  #englishStyling[The Receiving Organisation will provide financial support to the trainee for the traineeship. The amount is #organisme_accueil_montant_support_financier euros]
]

#if organisme_accueil_avantage_nature != missing_data [
  L’organisme d’accueil accordera au stagiaire des avantages en nature : #organisme_accueil_avantage_nature \
  #englishStyling[The Receiving Organisation will provide a contribution in kind to the trainee for the traineeship : #organisme_accueil_avantage_nature_english]
]

#if organisme_accueil_assurance_accident_travail or organisme_accueil_assurance_responsabilite_civile [
  Assurance pour le stagiaire\
  #englishStyling[Insurance for the trainee]\
  \
  ]
  #if organisme_accueil_assurance_accident_travail [
    L’organisme d’accueil fournira au stagiaire une assurance accident du travail (s’il n’est pas couvert par l’organisme bénéficiaire)\
    #englishStyling[The Receiving Organisation will provide an accident insurance to the trainee (if not provided by the beneficiary organisation)]
  ]

  #if organisme_accueil_assurance_deplacement_professionnel [
    - L’assurance accident couvre les accidents survenus pendant les déplacements professionnels.\
      #englishStyling[The accident insurance covers accidents during travels made for work purposes]
  ]

  #if organisme_accueil_assurance_trajet_domicile [
    - L’assurance accident couvre les accidents survenus sur les trajets domicile-travail.\
      #englishStyling[The accident insurance covers accidents on the way to work and back from work]
  ]

  #if organisme_accueil_assurance_responsabilite_civile [
    L’organisme d’accueil fournira au stagiaire une assurance accident du travail (s’il n’est pas assuré par l’organisme d’accueil).\
    #englishStyling[The receiving organisation will provide a liability insurance to the trainee (if not provided by the beneficiary organisation)]\
  ]

  [\
    L’organisme fournira au stagiaire les équipements adaptés et lui apportera un accompagnement pendant son stage.\
  #englishStyling[The Receiving Organisation will provide appropriate support and equipment to the trainee.]\
\
Sous réserve de la réalisation complète de la période de stage, l’organisme d’accueil s’engage à délivrer une attestation de stage dans un délai de 5 semaines à compter de la date de fin du stage.
#englishStyling[Upon completion of the traineeship, the Receiving Organisation undertakes to issue a traineeship certificate within 5 weeks after the end of the traineeship.]
  ]

#pagebreak()

En signant ce document, le stagiaire, l’organisme bénéficiaire et l’organisme d’accueil \[et l’établissement d’envoi, si différent de l’organisme bénéficiaire\] confirment qu’ils approuvent le contrat pédagogique et qu’ils se conforment aux dispositions acceptées par toutes les parties. Le stagiaire et l’organisme d’accueil communiqueront à l’organisme d’envoi \[et à l’organisme bénéficiaire, si différent de l’organisme d’envoi\] tout problème ou toute modification relatifs à la période de stage. L’organisme d’envoi \[et l’organisme bénéficiaire, si différent de l’organisme d’envoi\] et le stagiaire s’engagent également à respecter les termes du contrat de mobilité. L’organisme d’envoi et l’organisme d’accueil \[si l’organisme d’accueil est un établissement d’enseignement supérieur\] sont soumis au respect des principes de la Charte Erasmus pour l’enseignement supérieur en matière de stages. \
#englishStyling[By signing this document, the trainee, the beneficiary organisation, the receiving organisation \[and the sending institution, if different from the beneficiary organisation\] confirm that they approve the learning agreement and that they will comply with all the arrangements agreed by all parties. The trainee and receiving organisation will communicate to the sending institution \[and beneficiary organisation, if different from the sending institution\] any problem or changes regarding the traineeship period. The sending institution \[and the beneficiary organisation, if different from the sending institution\] and the trainee should also commit to what is set out in the Erasmus+ grant agreement. The sending institution \[and the receiving institution \[if the receiving organisation is a higher education institution\] undertake\[s\] to respect all the principles of the Erasmus Charter for Higher Education relating to traineeships.]


Superviseur de l’organisme d’accueil#footnote[personne responsable de la signature du contrat pédagogique (et des modifications qui y seront apportées si nécessaire) et de l’attestation de stage, qui supervise le stagiaire pendant son stage. Le nom et l’adresse électronique du superviseur doivent être indiqués uniquement dans le cas où celui-ci diffère de la personne contact indiquée au début du document.#englishStyling[this person is responsible for signing the learning agreement, amending it if needed, supervising the trainee during the traineeship and signing the Traineeship Certificate. The name and email of the supervisor must be filled in only in case it differs from that of the contact person mentioned at the top of the document.]]

Personne responsable de l’organisme bénéficiaire#footnote[personne responsable signataire des contrats pédagogiques, pouvant les modifier si nécessaire et qui, si l’organisme bénéficiaire est l’organisme d’envoi, est responsable de la reconnaissance des crédits et des résultats d’apprentissage associés, au nom de l’entité académique responsable indiquée dans le contrat pédagogique. Le nom et l’adresse électronique de la personne responsable devront être indiqués uniquement s’ils diffèrent de ceux de la personne de contact indiquée au début du document. #englishStyling[this person is responsible for signing the learning agreement, amending it if needed and if the beneficiary organisation is the sending institution, is responsible for recognising the credits and associated learning outcomes on behalf of the responsible academic body as set out in the learning agreement. The name and email of the responsible person must be filled in only in case it differs from that of the contact person mentioned at the top of the document.]]

"Personne responsable dans l’organisme d’envoi" #footnote[personne responsable signataire des contrats pédagogiques, pouvant les modifier si nécessaire et qui, si l’organisme bénéficiaire est différent de l’organisme d’envoi, est responsable de la reconnaissance des crédits et des résultats d’apprentissage associés, au nom de l’entité académique responsable indiquée dans le contrat pédagogique. Le nom et l’adresse électronique de la personne responsable devront être indiqués uniquement s’ils diffèrent de ceux de la personne de contact indiquée au début du document. 
#englishStyling[this person is responsible for signing the learning agreement, amending it if needed and if the beneficiary organisation is not the sending institution, is responsible for recognising the credits and associated learning outcomes on behalf of the responsible academic body as set out in the learning agreement. The name and email of the responsible person must be filled in only in case it differs from that of the responsible person at the beneficiary organisation.]
]

#signatures((
    "Stagiaire": custom_data(participant),
    "Superviseur de l’organisme d’accueil": custom_data(organisme_accueil_contact_nom),
    "Personne responsable de l’organisme bénéficiaire": custom_data(organisme),
    "Personne responsable dans l’organisme d’envoi":custom_data(organisme_envoi_contact_nom)),
))


#pagebreak()

= Pendant la mobilité

=== Modifications exceptionnelles du programme de stage dans l’organisme d’accueil

(à approuver par mail ou à faire signer par l’étudiant et les personnes responsables dans l’organisme d’envoi et l’organisme d’accueil)\
#englishStyling[(to be approved by e-mail or signature by the student, the responsible person in the Sending Institution and the responsible person in the receiving organisation)]

#let form_dict = (
  "Période de mobilité physique":[#custom_data(changement_pendant_mobilite_debut_mobilite_physique) à #custom_data(changement_pendant_mobilite_fin_mobilite_physique)],
  "Intitulé du stage": custom_data(changement_pendant_mobilite_intitule_stage),
  "Nombre d'heures travaillées par semaine":custom_data(changement_pendant_mobilite_nombre_heures_hebdo),
  "Programme détaillé du stage (y compris la composante virtuelle si applicable)":custom_data(changement_pendant_mobilite_programme_detaille),
  "Stage dans le domaine des compétences numériques" : custom_data(changement_pendant_mobilite_stage_domaine_competences_numeriques),
  "Connaissances, aptitudes et compétences à acquérir par le stagiaire au cours du stage (résultats d’apprentissage attendus)": custom_data(changement_pendant_mobilite_connaisance_a_acquerir),
  "Plan de suivi":[#custom_data(changement_pendant_mobilite_plan_suivi)],
  "Plan d'évaluation":[#custom_data(changement_pendant_mobilite_plan_evaluation)]
)

#if (debut_mobilite_virtuelle != missing_data){
  form_dict.insert("Période de mobilité virtuelle", [#custom_data(changement_pendant_mobilite_debut_mobilite_virtuelle) à #custom_data(changement_pendant_mobilite_fin_mobilite_virtuelle)])
}

#form(
  form_dict,
  wide_title: true
)

#pagebreak()

= Après la mobilité

=== Attestation de stage de l’organisme d’accueil

#form((
      "Nom du stagiaire":custom_data(participant),
      "Nom de l’organisme d’accueil":custom_data(organisme_accueil_nom),
      "Secteur d’activité de l’organisme d’accueil":custom_data(organisme_accueil_secteur_activite),
      "Coordonnées de l’organisme d’accueil": [#custom_data(organisme_accueil_adresse), #custom_data(organisme_accueil_site_web)],
      "Période de mobilité complete (période virtuelle incluse)":[#custom_data(debut_mobilite_totale) à #custom_data(fin_mobilite_totale)],
      "Intitulé du stage":custom_data(intitule_stage),
      "Programme détaillé du stage (y compris la composante virtuelle si applicable)": custom_data(programme_detaille),
    ),
    wide_title: true)


#form((
      "Connaissances, aptitudes et compétences à acquérir par le stagiaire au cours du stage (résultats d’apprentissage attendus)": custom_data(connaisance_a_acquerir),
      "Évaluation du stagiaire": custom_data(evaluation_participant)
    ),
    wide_title: true
)
#signatures(("Superviseur de l’organisme d’accueil" : custom_data(organisme_accueil_contact_nom))),


#pagebreak()

= Annexe II: Charte de l'étudiant Erasmus
https://erasmus-plus.ec.europa.eu/fr/charte-de-letudiant-erasmus-0

]