#import "../erasmus_plus_utils/erasmus_plus_editorial.typ" : *
#import "../erasmus_plus_utils/legal_template_utils.typ" : *

// Contrat financier Erasmus+ pour les mobilités de groupe (démarche 156967)
// signé par l'établissement d'envoi et par l'ENSFEA, coordonnateur du consortium

#let euros(v) = if v == missing_data { text(7pt, custom_data(v)) } else { [#v €] }

#let contrat_financier_groupe(
  code_projet: missing_data,
  secteur: "Enseignement et formation professionnels",
  type_activite: "Mobilité de groupe pour les apprenants de l’EFP",
  identifiant_mobilite: "N/A",
  titre_activite: missing_data,
  pays_ville: missing_data,
  date_debut: missing_data,
  date_fin: missing_data,
  duree: missing_data,
  organisme_envoi_nom: missing_data,
  organisme_envoi_statut_juridique: missing_data,
  organisme_envoi_adresse: missing_data,
  organisme_envoi_email: missing_data,
  organisme_envoi_code: missing_data,
  organisme_envoi_representant_nom_complet: missing_data,
  organisme_envoi_representant_fonction: missing_data,
  envoi_direction_nom: missing_data,
  envoi_direction_prenom: "",
  coordinateur_nom: "Damien TREMEAU BUSSON",
  coordinateur_fonction: "Directeur",
  coordinateur_adresse: "2 Route de Narbonne – BP 22687 31326 CASTANET-TOLOSAN Cedex",
  duree_voyage: missing_data,
  duree_jours_bourse: missing_data,
  valeur_bourse: missing_data,
  frais_sejour: missing_data,
  frais_voyage: missing_data,
  // une ligne par participant : (nom, statut, frais de séjour, frais de voyage, total)
  participants_frais: ((missing_data, missing_data, missing_data, missing_data, missing_data),),
  limite_prolongation: "0",  // en dur
  accompte_pourcentage: "80",
  option_prise_en_charge: missing_data,
  option_libelle: missing_data,
  assurance_responsable: missing_data,
  compagnie_assurance: missing_data,
  numero_police_assurance: missing_data,
  ..superfluous_arguments
 ) = [

#show: doc => erasmus_plus_layout(
  title: "Contrat financier Erasmus+ pour la mobilité des individus",
  header_note: code_projet,
  activate_translation: false,
  show_title: false,
  doc
)

#let parts = if type(code_projet) == str { code_projet.split("-") } else { () }
#couverture(
  kicker: [ERASMUS+ #if parts.len() >= 5 [#h(3pt)·#h(3pt) #parts.at(3) #parts.at(4)] #h(3pt)·#h(3pt) MOBILITÉ DE GROUPE],
  title: "Contrat financier Erasmus+ pour la mobilité des individus",
  participant_label: "ACTIVITÉ DE GROUPE",
  participant: text(weight: "bold", titre_activite),
  code: code_projet,
  cles: (
    ("Destination", pays_ville),
    ("Début", date_debut),
    ("Fin", date_fin),
    ("Durée", duree),
  ),
  activate_translation: false,
)

#form((
    "Secteur": custom_data(secteur),
    "Type d’activité": custom_data(type_activite),
    "Identifiant de la mobilité Erasmus+": custom_data(identifiant_mobilite),
  ),
  activate_translation: false,
  wide_title: true,
)

= Préambule

#chap[

  Ce #strong[contrat] (“le contrat”) engage les parties suivantes :

  *d’une part*,

  *L’Organisme (”l’organisme”)*

  Nom officiel complet de l’organisme d’envoi : #custom_data(organisme_envoi_nom)

  Statut juridique officiel : #custom_data(organisme_envoi_statut_juridique)

  Adresse officielle complète : #custom_data(organisme_envoi_adresse)

  E-mail : #custom_data(organisme_envoi_email)

  Code OID : #custom_data(organisme_envoi_code)

  Représenté aux fins de la signature du présent contrat par :

  Nom(s) et prénom(s) : #custom_data(organisme_envoi_representant_nom_complet)

  Fonction : #custom_data(organisme_envoi_representant_fonction)

  *et d’autre part*,

  *l’ENSFEA*

  Représentée par : #custom_data(coordinateur_nom)

  Adresse : #custom_data(coordinateur_adresse)

  Les parties mentionnées ci-dessus ont accepté de conclure ce contrat.

  Le contrat comprend :
  - les conditions générales
  - l’annexe : Contrat d’apprentissage Erasmus+ pour les mobilités de groupe#footnote[Il n’est pas obligatoire de diffuser des documents avec des signatures originales pour l’Annexe du présent document : des copies numérisées des signatures et des signatures électroniques peuvent être acceptées, selon la législation nationale.]

  Les modalités définies dans les conditions générales prévalent sur celles définies dans les annexes.
]

= CONDITIONS GÉNÉRALES

#article[Objet du contrat]

#mention[
Le présent accord définit les droits, obligations et conditions applicables au soutien financier accordé pour la réalisation d’une activité de mobilité de groupe dans le cadre du programme Erasmus+.
]

#mention[
L’organisation fournira un soutien aux participants pour entreprendre une activité de mobilité de groupe.
]

#mention[
L’organisme accepte le soutien ou la prestation de services tel que spécifié à l’article 3 et s’engage à réaliser l’activité de mobilité décrite à l’annexe.
]

#mention[
Tout avenant au présent contrat financier sera demandé et accepté par les deux parties de manière formelle par courrier postal ou par mail. Un avenant entre en vigueur le jour de la signature (ou accusé de réception) du destinataire. L’avenant prend effet à la date d’entrée en vigueur ou à toute autre date spécifiée dans l’avenant.
]

#article[Entrée en vigueur du contrat et durée de la mobilité]

#mention[
Le contrat financier entre en vigueur à la date de signature de la dernière des deux parties.
]

#mention[
Le contrat financier couvrira la période#footnote[Cette période comprend les composantes physique et virtuelle de la mobilité, comme indiqué dans l’annexe, et les jours de voyage (voir l’annexe pour un calendrier détaillé).] allant du #custom_data(date_debut) au #custom_data(date_fin) dont #custom_data(duree_voyage) jours de voyage par participant.
]

#article[Soutien financier]

#mention[
Le soutien financier est calculé selon les règles de financement indiquées dans le guide du programme Erasmus+ (version 2025).
]

#mention[
L’établissement recevra un soutien financier des fonds européens Erasmus+ pour #custom_data(duree_jours_bourse) jours#footnote[Le nombre de jours sera égal à la durée de la période de mobilité physique en comptant les jours de voyage ; si le participant ne reçoit pas de soutien financier pour une partie ou la totalité de la période de mobilité, ce nombre de jours doit être ajusté en conséquence.].

Le soutien financier total pour la période de mobilité est de #custom_data(valeur_bourse) euros, ce qui correspond à la somme de #custom_data(frais_sejour) euros pour les frais de séjour et #custom_data(frais_voyage) euros pour les frais de voyage.
]

// frais destinés aux participants : une ligne par personne, puis les totaux
// (l'en-tête se répète si le tableau continue sur la page suivante)
#block(above: 10pt, below: 14pt)[
  #let droite(v) = align(right, euros(v))
  #tableau(
    ("Nom et prénom du participant", "Statut du participant", "Frais de séjour", "Frais de voyage", "Total bourse"),
    participants_frais.map(((nom, statut, sejour, voyage, total)) => (nom, statut, droite(sejour), droite(voyage), droite(total)))
      + ((strong[Totaux], [], align(right, strong(euros(frais_sejour))), align(right, strong(euros(frais_voyage))), align(right, strong(euros(valeur_bourse)))),),
    columns: (1fr, 20%, 14%, 14%, 14%),
    activate_translation: false,
  )
]

#mention[
L’établissement peut présenter une demande de prolongation de la période de mobilité physique dans la limite fixée dans le Guide du Programme Erasmus+, soit : #custom_data(limite_prolongation) jours#footnote[À compléter par le bénéficiaire en concordance avec les règles du Guide du Programme Erasmus+.]

Si l’organisation accepte de prolonger la période de mobilité par écrit, le contrat financier sera modifié en conséquence.
]

// option choisie dans DN (libellé affiché en gras), puis le texte correspondant
#mention[
  #let reliquat = [
    L’organisme s’assurera que la contribution en nature répond aux normes de qualité et de sécurité nécessaires.

    En cas de reliquat mineur sur le poste de dépense fourni par l’organisme sous la forme d’une contribution en nature, celui-ci décide de verser le montant de l’intégralité du reliquat correspondant au participant.
  ]

  #if option_prise_en_charge == "Option 1" [
    #custom_data(option_libelle). L’organisme fournira aux participants le soutien requis sous la forme d’un paiement de #custom_data(valeur_bourse) euros.
  ] else if option_prise_en_charge == "Option 2" [
    #custom_data(option_libelle). L’organisme accordera aux participants le soutien requis sous la forme d’une contribution en nature.

    #reliquat
  ] else if option_prise_en_charge == "Option 3 transport" [
    #custom_data(option_libelle). L’organisme fournira aux participants le soutien requis sous la forme d’un paiement du montant suivant : #custom_data(frais_sejour) euros et sous la forme d’une contribution en nature pour les frais de transport.

    #reliquat
  ] else if option_prise_en_charge == "Option 3 sejour" [
    #custom_data(option_libelle). L’organisme fournira aux participants le soutien requis sous la forme d’un paiement du montant suivant : #custom_data(frais_voyage) euros et sous la forme d’une contribution en nature pour les frais de séjour.

    #reliquat
  ] else [
    Modalité de prise en charge : #custom_data(missing_data)
  ]
]

#mention[
Les participants sont en droit de recevoir un remboursement de 100 % des coûts éligibles au titre du soutien pour l’inclusion. Le remboursement des frais encourus liés au soutien pour l’inclusion, le cas échéant, sera effectué sur la base des justificatifs fournis par le participant.
]

#article[Éligibilité des coûts]

#mention[
Pour être éligibles, les coûts doivent être effectivement nécessaires à la mise en œuvre de l’activité visée dans l’annexe. Les coûts doivent être conformes à la législation nationale applicable en matière de fiscalité, de travail et de sécurité sociale.
]

#mention[
En ce qui concerne les coûts réels (par exemple, le soutien pour l’inclusion des participants), ils doivent être fondés sur des documents justificatifs tels que des factures, des reçus, etc.
]

#mention[
Le soutien financier ne peut être utilisé pour couvrir les coûts d’activités déjà financées par des fonds de l’Union européenne. Il est néanmoins compatible avec toute autre source de financement. Dans le cas de la mobilité des apprenants, les revenus, y compris le salaire que le participant pourrait percevoir en travaillant au-delà de ses études/stages, sont compatibles avec les activités d’enseignement, ou pour tout travail en dehors de ses activités de mobilité, pour autant qu’il exerce les activités prévues à l’annexe 1.
]

#mention[
L’organisme ne peut pas demander le remboursement des pertes liées à la monnaie de change ou des frais bancaires facturés par la banque du participant, pour les transferts effectués par l’organisme qui l’envoie.
]

#article[Modalités de paiement]

#mention[
Dans les 30 jours calendaires suivant la signature du contrat par les deux parties ou à la réception de la confirmation d’arrivée, et au plus tard à la date de début de la période de mobilité telle que spécifiée à l’article 2.2, un préfinancement est versé à l’établissement à hauteur de : #custom_data(accompte_pourcentage) % du montant spécifié à l’article 3.

Dans le cas où l’organisme ne fournit pas les pièces justificatives dans les temps impartis fixés par l’organisme d’envoi, un report de paiement du préfinancement peut être exceptionnellement accepté, sur la base de raisons justifiées.
]

#mention[
Si le paiement prévu à l’article 5.1 est inférieur à 100 % du soutien financier, la soumission du questionnaire UE en ligne est considérée comme la demande du participant pour le paiement du solde du soutien financier. L’organisme dispose de 45 jours calendaires pour effectuer le paiement du solde ou pour émettre un ordre de recouvrement en cas de remboursement le cas échéant.
]

#article[Recouvrement]

#mention[
Le soutien financier ou une partie de celui-ci sera récupéré par l’organisation d’envoi si les participants ne respectent pas les termes de la convention. Si les participants mettent fin à la mobilité avant son terme, ces derniers devront restituer le montant de la subvention déjà versé, sauf accord contraire avec l’organisme d’envoi. L’accord sera signalé par l’organisme d’envoi et accepté par l’Agence nationale.
]

#article[Assurance]

#mention[
L’organisme s’assurera que les participants disposent d’une couverture d’assurance adéquate, soit en fournissant lui-même l’assurance, soit en concluant un accord avec l’organisme d’accueil pour que ce dernier fournisse l’assurance#footnote[Dans le cas où l’organisme d’accueil est identifié comme la partie responsable à l’article 7.3, un document spécifique sera joint à ce contrat financier définissant les dispositions en matière d’assurance et incluant le consentement de l’organisme d’accueil.].
]

#mention[
La couverture d’assurance inclura au minimum une assurance maladie, une assurance responsabilité civile et une assurance accident#footnote[En cas de mobilité intracommunautaire, l’assurance maladie nationale du participant inclura une couverture de base pendant son séjour dans un autre pays de l’UE grâce à la carte européenne d’assurance maladie. Toutefois, cette couverture peut ne pas être suffisante pour toutes les situations, par exemple en cas de rapatriement ou d’intervention médicale spéciale ou en cas de mobilité internationale. Dans ce cas, une assurance maladie privée complémentaire peut être nécessaire. Les assurances responsabilité civile et accident couvrent les dommages causés par le participant ou au participant pendant son séjour à l’étranger. La réglementation de ces assurances varie selon les pays et les participants courent le risque de ne pas être couverts par les régimes standards, par exemple s’ils ne sont pas considérés comme des employés ou officiellement inscrits dans l’organisme d’accueil. En plus de ce qui est indiqué précédemment, il est recommandé de souscrire à une assurance contre la perte ou le vol de documents, de titres de voyages et de bagages. L’Agence nationale peut compléter l’article 7.2 s’il est justifié d’adapter les exigences par défaut au contexte national.].
]

#mention[La partie responsable de la souscription de l’assurance (responsabilité civile et accident) est#footnote[En cas d’assurances distinctes, les parties responsables peuvent être différentes et seront énumérées ici en fonction de leurs responsabilités respectives.] : #custom_data(assurance_responsable)
  #form((
      "Compagnie d'assurance": custom_data(compagnie_assurance),
      "Numéro et police d'assurance": custom_data(numero_police_assurance),
    ),
    activate_translation: false,
    wide_title: true
  )
]

#article[Rapport du participant (questionnaire UE)]

#mention[
L’accompagnateur principal devra compléter et soumettre le questionnaire UE en ligne après la mobilité à l’étranger dans les 30 jours calendaires suivant la réception de la notification l’invitant à le faire. Les accompagnateurs principaux qui ne complètent pas et qui ne soumettent pas le questionnaire UE en ligne seront susceptibles de rembourser partiellement ou intégralement le soutien financier reçu sur demande de leur organisme d’envoi.
]

#mention[
Un questionnaire complémentaire en ligne pourra être envoyé aux participants afin de rendre pleinement compte de la reconnaissance de l’expérience de mobilité.
]

#article[Éthique et valeurs]

#mention[
L’activité de mobilité doit être menée en conformité avec les grands principes éthiques et le droit européen, international et national en vigueur.
]

#mention[
Les participants doivent s’engager à respecter les valeurs fondamentales de l’UE (telles que le respect de la dignité humaine, la liberté, la démocratie, l’égalité, l’État de droit et les droits de l’homme, y compris les droits des minorités).
]

#mention[
Si un participant manque à l’une des obligations citées dans le présent article, le soutien financier peut être réduit ou ne pas être versé.
]

#article[Protection des données]

#mention[
Toute donnée fournie dans ce contrat sera traitée sous la responsabilité du contrôleur de données identifié dans la déclaration de confidentialité, conformément à la législation applicable en matière de récupération des données, en particulier le règlement 2018/1725#footnote[Regulation (EU) 2018/1725 of the European Parliament and of the Council of 23 October 2018 on the protection of natural persons with regard to the processing of personal data by the Union institutions, bodies, offices and agencies and on the free movement of such data, and repealing Regulation (EC) No 45/2001 and Decision No 1247/2002/EC.] et les lois nationales connexes sur la protection des données, et aux fins énoncées dans la déclaration de confidentialité disponible à l’adresse suivante : https://webgate.ec.europa.eu/erasmus-esc/index/privacy-statement
]

#mention[
Ces données seront traitées uniquement dans le cadre de mise en œuvre et du suivi du contrat par l’organisme d’envoi, l’Agence nationale et la Commission européenne, sans préjudice quant à la possibilité de transmission des données aux organes chargés du contrôle et de l’audit conformément à la législation de l’UE (Cour des comptes européenne ou Office européen de lutte antifraude).
]

#mention[
L’organisme peut, sur demande écrite, avoir accès à ses données personnelles et corriger toute information inexacte ou incomplète. Le participant adressera toute question concernant le traitement de ses données personnelles à l’organisme d’envoi et/ou à l’Agence nationale. Le participant peut déposer plainte contre le traitement de ses données personnelles auprès du Contrôleur européen de la protection des données en ce qui concerne l’utilisation des données par la Commission européenne.
]

#article[Suspension du contrat]

#mention[
Le contrat peut être suspendu si des circonstances exceptionnelles – notamment de force majeure (voir article 15) – en rendent l’exécution impossible ou excessivement difficile. La suspension prend effet au jour convenu par notification écrite des parties. Le contrat peut être rétabli par la suite.
]

#mention[
L’organisme peut, à tout moment, suspendre l’accord si le participant a commis ou est soupçonné d’avoir commis :

+ des erreurs substantielles, des irrégularités ou des fraudes, ou
+ un manquement grave aux obligations découlant du présent contrat ou au cours de son attribution (y compris la mise en œuvre incorrecte de l’action, la soumission de fausses informations, le manquement à l’obligation de fournir les informations requises, la violation des règles éthiques (le cas échéant), etc.).
]

#mention[
Lorsque les circonstances permettent la reprise de la mise en œuvre du contrat, les parties doivent immédiatement convenir de la date de reprise (un jour après la date de fin de la suspension). La suspension sera levée à compter de la date de fin de la suspension.
]

#mention[Pendant la suspension, aucun soutien financier ne sera versé.]

#mention[Le participant ne peut prétendre à des dommages et intérêts du fait de la suspension par l’organisme.]

#mention[La suspension n’affecte pas le droit de l’organisme de résilier le contrat (voir article 12).]

#article[Résiliation du contrat]

#mention[
Le contrat peut être résilié par l’une ou l’autre des parties si des circonstances surviennent qui rendent l’exécution de l’accord impraticable, impossible ou excessivement difficile.
]

#mention[
En cas de résiliation pour cause de force majeure (article 15), l’organisme aura le droit de recevoir au moins le montant du soutien financier correspondant à la durée réelle de la période d’activité. Les fonds restants devront être remboursés.
]

#mention[
En cas de manquement grave aux obligations ou si le participant a commis des irrégularités, une fraude, une corruption ou est impliqué dans une organisation criminelle, un blanchiment d’argent, des crimes liés au terrorisme (y compris le financement du terrorisme), le travail des enfants ou la traite des êtres humains, l’organisme peut mettre fin au contrat en le notifiant officiellement à l’autre partie.
]

#mention[
L’organisme se réserve le droit d’entamer une action en justice si le remboursement demandé n’est pas effectué volontairement dans le délai notifié au participant par lettre recommandée.
]

#mention[La résiliation prendra effet à la date spécifiée dans la notification (« date de résiliation »).]

#mention[Le participant ne peut prétendre à des dommages et intérêts du fait de la résiliation par l’organisme.]

#article[Contrôles et audits]

#mention[
Les contractants s’engagent à fournir toute information détaillée demandée par la Commission européenne, l’Agence nationale française ou par tout autre organisme extérieur autorisé par la Commission européenne ou l’Agence nationale française à contrôler que la période de mobilité et les dispositions prévues au contrat soient ou aient été correctement mises en œuvre.
]

#mention[
Toute constatation relative au contrat peut donner lieu aux mesures prévues à l’article 6 ou à d’autres actions en justice dans les conditions prévues par le droit national applicable.
]

#article[Dommages et intérêts]

#mention[
L’Agence nationale française, la Commission européenne ou leurs personnels ne seront pas tenus pour responsables en cas d’action de réclamation au titre du contrat relative à tout dommage causé pendant l’exécution de la période de mobilité. En conséquence, l’Agence nationale française ou la Commission européenne n’examinera aucune demande d’indemnisation ou de remboursement accompagnant une telle réclamation.
]

#article[Force majeure]

#mention[
Un participant ne pouvant remplir ses obligations contractuelles en raison d’un cas de force majeure ne peut être tenu responsable de leur infraction.
]

#mention[
La « force majeure » renvoie à toute situation ou évènement qui :
- empêche l’une ou l’autre des parties de s’acquitter de ses obligations au titre du contrat,
- était imprévisible, exceptionnel et indépendant de la volonté des parties,
- n’était pas dû à une erreur ou à une négligence de leur part (ou de la part d’autres entités participantes impliquées dans l’action), et
- s’avère inévitable malgré l’exercice de toute la diligence requise.
]

#mention[
Toute situation constituant un cas de force majeure doit être notifiée formellement et sans délai à l’autre partie, en précisant sa nature, sa durée probable et ses effets prévisibles.
]

#mention[
Toutes les mesures nécessaires doivent être prises immédiatement pour limiter les dommages dus à la force majeure et faire de leur mieux pour reprendre la mise en œuvre de l’action dès que possible.
]

#article[Loi applicable et tribunal compétent]

#mention[Le présent contrat est régi par le droit français.]

#article[Entrée en vigueur]

#mention[Le contrat entrera en vigueur à la dernière date de signature par les parties.]

= Signatures

#signatures((
  (titre: "Pour l’organisme", organisme: organisme_envoi_nom,
   nom: envoi_direction_nom, prenom: envoi_direction_prenom, fonction: organisme_envoi_representant_fonction),
  (titre: "Pour le coordonnateur du consortium", organisme: "ENSFEA",
   nom: coordinateur_nom, fonction: coordinateur_fonction),
), activate_translation: false)

#pagebreak()

= Annexe

== Contrat pédagogique

Le bénéficiaire peut rédiger un contrat d’apprentissage ou utiliser un modèle fourni par la Commission européenne ou l’Agence nationale.

Au minimum, le contrat d’apprentissage comportera les éléments suivants :

- Le contrat d’apprentissage est convenu et signé par les deux parties principales : l’organisme d’envoi et l’organisme d’accueil
- Des informations sur la mobilité à des fins d’apprentissage, notamment : le secteur d’enseignement, le type d’activité, le format (mobilité physique, virtuelle ou hybride), la date de début et de fin
- Des informations sur le programme d’apprentissage auquel est inscrit le participant dans l’organisme d’envoi (dans le cas des apprenants) ou sur son emploi actuel (dans le cas du personnel)
- Une liste et une description des acquis d’apprentissage attendus
- Le programme d’apprentissage et les tâches des participants dans l’organisme d’accueil
- Les personnes responsables dans les organismes d’accueil et d’envoi

]
