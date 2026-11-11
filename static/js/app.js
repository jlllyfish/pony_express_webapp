(function () {
  // Session expirée : toute réponse 401 d'une API renvoie vers la page de connexion
  const fetchOrigine = window.fetch.bind(window);
  window.fetch = async (...args) => {
    const res = await fetchOrigine(...args);
    if (res.status === 401) {
      location.href = `/connexion?suivant=${encodeURIComponent(location.pathname + location.hash)}`;
    }
    return res;
  };
  "use strict";

  let allDossiers = [];
  const selected = new Set();
  // Filtre d'envoi du document de l'onglet actif : tous / envoye / a_envoyer
  let filterStatut = "tous";
  // Filtre global (synthèse) : "" / "complets" / "incomplets"
  let filterComplet = "";
  // Affichage : "cartes" ou "liste" (mémorisé par page dans le navigateur)
  let modeAffichage = "cartes";
  // Document traité par les boutons Générer / Envoyer
  let documentActif = "pedagogique";
  // Page affichée : "apprenants" (démarche 128447) ou "groupes" (démarche 156967)
  let vue = "apprenants";
  const VUES = {
    apprenants: {
      api: "/api/dossiers",
      // document par défaut (le sélecteur permet de choisir le financier)
      // choix du sélecteur « Document à traiter » -> document réel
      documents: { pedagogique: "pedagogique", financier: "financier" },
      libellePedagogique: "Kit pédagogique",
      titre: "Mobilités des apprenants",
      recherche: "Nom du participant",
    },
    groupes: {
      api: "/api/groupes",
      documents: { pedagogique: "pedagogique_groupe", financier: "financier_groupe" },
      libellePedagogique: "Contrat pédagogique",
      titre: "Mobilités de groupe",
      recherche: "Centre constitutif",
    },
    personnel: {
      api: "/api/personnel",
      documents: { pedagogique: "pedagogique_personnel", financier: "financier_personnel" },
      libellePedagogique: "Kit pédagogique",
      titre: "Mobilités du personnel",
      recherche: "Nom du participant",
    },
    experts: {
      api: null,
      bientot: "La page des mobilités d'experts invités est en préparation. Elle sera branchée dès que la démarche DN existera.",
      documents: { pedagogique: "pedagogique", financier: "financier" },
      libellePedagogique: "Kit péda + attestation",
      titre: "Experts invités",
      recherche: "",
    },
    dashboard: {
      api: null,
      documents: { pedagogique: "pedagogique", financier: "financier" },
      libellePedagogique: "Kit péda + attestation",
      titre: "Tableau de bord",
      recherche: "",
    }
  };
  const DOCUMENTS = {
    pedagogique: {
      court: "le kit péda + attestation",
      nom: "kit pédagogique et de l'attestation",
      champ: "envoye_pedagogique", // statut d'envoi lu dans la tuile
      // PDF téléchargeables séparément
      pdfs: [
        ["pedagogique", "kit pédagogique"],
        ["attestation", "attestation de présence"],
      ],
    },
    financier: {
      court: "le contrat financier",
      nom: "contrat financier",
      champ: "envoye_financier",
      pdfs: [["financier", "contrat financier"]],
    },
    pedagogique_groupe: {
      court: "le contrat péda + attestation",
      nom: "contrat pédagogique et de l'attestation",
      champ: "envoye_pedagogique",
      pdfs: [
        ["pedagogique_groupe", "contrat pédagogique"],
        ["attestation_groupe", "attestation de présence"],
      ],
    },
    financier_groupe: {
      court: "le contrat financier",
      nom: "contrat financier",
      champ: "envoye_financier",
      pdfs: [["financier_groupe", "contrat financier"]],
    },
    pedagogique_personnel: {
      court: "le kit péda + attestation",
      nom: "kit pédagogique et de l'attestation",
      champ: "envoye_pedagogique",
      pdfs: [
        ["pedagogique_personnel", "kit pédagogique"],
        ["attestation_personnel", "attestation de présence"],
      ],
    },
    financier_personnel: {
      court: "le contrat financier",
      nom: "contrat financier",
      champ: "envoye_financier",
      pdfs: [["financier_personnel", "contrat financier"]],
    },
  };

  // Envoi / synchro DN non configurés pour une démarche (ex : personnel, identifiants DN à venir)
  let envoiConfigure = {};
  const statutsSession = {}; // {vue: {dossier_number: {document: "genere"}}}
  let synchroConfiguree = true;
  const MESSAGE_NON_CONFIGURE = "Envoi vers DN pas encore configuré pour cette démarche (identifiants des annotations à renseigner)";

  function setDocument(value) {
    documentActif = value;
    document
      .querySelectorAll(".doc-label")
      .forEach((span) => (span.textContent = DOCUMENTS[value].court));
  }

  const el = {
    cards: document.getElementById("cards"),
    filterEtab: document.getElementById("filter-etablissement"),
    search: document.getElementById("search-nom"),
    countVisible: document.getElementById("count-visible"),
    countTotal: document.getElementById("count-total"),
    countATraiter: document.getElementById("count-a-traiter"),
    selNombre: document.getElementById("sel-nombre"),
    selCountBis: document.querySelector(".sel-count-bis"),
    barreActions: document.getElementById("barre-actions"),
    btnTout: document.getElementById("btn-tout"),
    btnAucun: document.getElementById("btn-aucun"),
    vueCartes: document.getElementById("vue-cartes"),
    vueListe: document.getElementById("vue-liste"),
    statutLibelle: document.getElementById("filtre-statut-libelle"),
    btnGenerate: document.getElementById("btn-generate"),
    selCount: document.getElementById("sel-count"),
    btnRefresh: document.getElementById("btn-refresh"),
    btnSyncDn: document.getElementById("btn-sync-dn"),
    btnSend: document.getElementById("btn-send"),
    toggleSelectAll: document.getElementById("toggle-select-all"),
    toast: document.getElementById("toast"),
    toastLoader: document.getElementById("toast-loader"),
    toastLoaderFrozen: document.getElementById("toast-loader-frozen"),
    toastTitle: document.getElementById("toast-title"),
    toastProgress: document.getElementById("toast-progress"),
    toastClose: document.getElementById("toast-close"),
    modal: document.getElementById("modal"),
    modalTitle: document.getElementById("modal-title"),
    modalList: document.getElementById("modal-list"),
    modalClose: document.getElementById("modal-close"),
  };

  let toastTimeout = null;

  // --- État de santé de Grist et DN ---
  // true tant que le test n'a pas échoué (on ne bloque pas pendant le test)
  const sante = { grist: true, dn: true };
  const SANTE_NOMS = { grist: "Grist", dn: "Démarches Numériques" };

  async function verifierSante(silencieux) {
    ["grist", "dn"].forEach((k) => {
      const b = document.getElementById(`sante-${k}`);
      b.dataset.etat = "test";
      b.title = "Test de connexion en cours…";
    });
    let data;
    try {
      const res = await fetch("/api/sante");
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      data = await res.json();
    } catch (err) {
      data = {
        heure: "",
        grist: { ok: false, message: `Serveur de l'application injoignable (${err.message})` },
        dn: { ok: false, message: "Non testé : serveur de l'application injoignable" },
      };
    }
    const echecs = [];
    ["grist", "dn"].forEach((k) => {
      const r = data[k];
      sante[k] = r.ok;
      const b = document.getElementById(`sante-${k}`);
      b.dataset.etat = r.ok ? "ok" : "ko";
      b.title = `${SANTE_NOMS[k]} ${r.ok ? "OK" : "en échec"}${r.ms != null ? ` · ${r.ms} ms` : ""}${data.heure ? ` · ${data.heure}` : ""}\n${r.message}\n(cliquer pour retester)`;
      if (!r.ok) echecs.push(`<strong>${SANTE_NOMS[k]}</strong> — ${r.message}`);
    });
    updateSelectionUI();
    if (echecs.length && !silencieux) {
      showInfoModal("Connexion en échec", echecs.concat([
        "Les actions qui dépendent de ce service sont désactivées. Clique sur la pastille pour retester.",
      ]), "error");
    }
  }

  function showToastProgress(label, current, total) {
    clearTimeout(toastTimeout);
    el.toast.hidden = false;
    el.toast.classList.remove("toast--error");
    el.toastLoaderFrozen.hidden = true;
    el.toastLoader.hidden = false;
    el.toastTitle.textContent = label;
    el.toastProgress.textContent = `${current} / ${total}`;
  }

  function updateToastProgress(current, total) {
    el.toastProgress.textContent = `${current} / ${total}`;
  }

  function showToastResult(label, successCount, total, failedCount) {
    const ctx = el.toastLoaderFrozen.getContext("2d");
    ctx.clearRect(
      0,
      0,
      el.toastLoaderFrozen.width,
      el.toastLoaderFrozen.height,
    );
    ctx.drawImage(
      el.toastLoader,
      0,
      0,
      el.toastLoaderFrozen.width,
      el.toastLoaderFrozen.height,
    );
    el.toastLoader.hidden = true;
    el.toastLoaderFrozen.hidden = false;

    el.toastTitle.textContent = label;
    el.toastProgress.textContent = failedCount
      ? `${successCount} / ${total} réussis · ${failedCount} échec(s)`
      : `${successCount} / ${total} réussis`;
    el.toast.classList.toggle("toast--error", failedCount > 0);

    if (!failedCount) {
      toastTimeout = setTimeout(hideToast, 4000);
    }
  }

  function hideToast() {
    clearTimeout(toastTimeout);
    el.toast.hidden = true;
  }

  function showInfoModal(title, lines, variant) {
    el.modalTitle.textContent = title;
    el.modalList.innerHTML = lines.map((line) => `<li>${line}</li>`).join("");
    el.modal.classList.toggle("modal--error", variant === "error");
    el.modal.hidden = false;
  }

  function hideInfoModal() {
    el.modal.hidden = true;
  }

  function initiales(dossier) {
    const p = (dossier.prenom || "").trim()[0] || "";
    const n = (dossier.nom || "").trim()[0] || "";
    return (p + n).toUpperCase() || "—";
  }

  function matches(dossier) {
    const etab = el.filterEtab.value;
    if (etab && dossier.etablissement !== etab) return false;

    const complet = dossier.envoye_pedagogique && dossier.envoye_financier;
    if (filterComplet === "complets" && !complet) return false;
    if (filterComplet === "incomplets" && complet) return false;
    const envoye = Boolean(dossier[DOCUMENTS[documentActif].champ]);
    if (filterStatut === "envoye" && !envoye) return false;
    if (filterStatut === "a_envoyer" && envoye) return false;

    const query = el.search.value.trim().toLowerCase();
    if (!query) return true;
    // groupes : le centre constitutif contient la saisie
    if (vue === "groupes") return (dossier.titre || "").toLowerCase().includes(query);
    // apprenants : recherche "starts with" sur nom ou prénom
    return (
      (dossier.nom || "").toLowerCase().startsWith(query) ||
      (dossier.prenom || "").toLowerCase().startsWith(query)
    );
  }

  // Dates reçues au format jj-mm-aa (ou jj-mm-aaaa) -> objet Date, ou null
  function parseDate(txt) {
    const m = /^(\d{2})[-/](\d{2})[-/](\d{2}|\d{4})$/.exec(String(txt || "").trim());
    if (!m) return null;
    const annee = m[3].length === 2 ? 2000 + Number(m[3]) : Number(m[3]);
    return Date.UTC(annee, Number(m[2]) - 1, Number(m[1]));
  }

  // Nombre de jours, bornes incluses, ex : " (29 j)" ; vide si incalculable
  function duree(debut, fin) {
    const d = parseDate(debut);
    const f = parseDate(fin);
    if (d === null || f === null || f < d) return "";
    return ` <span class="card-duree">(${Math.round((f - d) / 86400000) + 1} j)</span>`;
  }

  // ---------------------------------------------------------------------------
  // Cartes et lignes (affichage cartes / liste)
  // ---------------------------------------------------------------------------
  const svg = (paths, taille = 16) =>
    `<svg width="${taille}" height="${taille}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${paths}</svg>`;
  const ICO = {
    calendrier: '<rect x="3" y="4" width="18" height="18" rx="2"/><path d="M16 2v4M8 2v4M3 10h18"/>',
    avion: '<path d="M17.8 19.2 16 11l3.5-3.5C21 6 21.5 4 21 3c-1-.5-3 0-4.5 1.5L13 8 4.8 6.2c-.5-.1-.9.1-1.1.5l-.3.5c-.2.5-.1 1 .3 1.3L9 12l-2 3H4l-1 1 3 2 2 3 1-1v-3l3-2 3.5 5.3c.3.4.8.5 1.3.3l.5-.2c.4-.3.6-.7.5-1.2z"/>',
    groupe: '<path d="M17 21a5 5 0 00-10 0"/><path d="M22 10.5a3.5 3.5 0 00-5.507-2.868"/><path d="M7.507 7.632A3.5 3.5 0 002 10.5"/><circle cx="12" cy="13" r="3"/><circle cx="18.5" cy="4.5" r="2.5"/><circle cx="5.5" cy="4.5" r="2.5"/>',
    personne: '<circle cx="12" cy="8" r="5"/><path d="M20 21a8 8 0 0 0-16 0"/>',
    maison: '<path d="M3 10.5 12 3l9 7.5V21H3z"/>',
    badge: '<path d="M16 20V4a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/><rect width="20" height="14" x="2" y="6" rx="2"/>',
    lieu: '<path d="M20 10c0 4.99-5.54 10.19-7.4 11.8a1 1 0 0 1-1.2 0C9.54 20.19 4 14.99 4 10a8 8 0 0 1 16 0"/><circle cx="12" cy="10" r="3"/>',
    telecharger: '<path d="M12 15V3"/><path d="m7 10 5 5 5-5"/><path d="M5 21h14"/>',
    coche: '<path d="M5 12l4 4 10-10"/>',
  };
  const MOIS = ["janv.", "févr.", "mars", "avr.", "mai", "juin", "juil.", "août", "sept.", "oct.", "nov.", "déc."];

  // « 19 – 23 oct. 2026 », « 28 oct. – 3 nov. 2026 » ; texte brut si une date manque
  function periode(debut, fin, avecAnnee = true) {
    const d = parseDate(debut);
    const f = parseDate(fin);
    if (d === null || f === null) return [debut, fin].filter(Boolean).join(" → ") || "";
    const D = new Date(d);
    const F = new Date(f);
    const an = avecAnnee ? ` ${F.getUTCFullYear()}` : "";
    if (D.getUTCMonth() === F.getUTCMonth() && D.getUTCFullYear() === F.getUTCFullYear())
      return `${D.getUTCDate()} – ${F.getUTCDate()} ${MOIS[F.getUTCMonth()]}${an}`;
    const anD = D.getUTCFullYear() !== F.getUTCFullYear() && avecAnnee ? ` ${D.getUTCFullYear()}` : "";
    return `${D.getUTCDate()} ${MOIS[D.getUTCMonth()]}${anD} – ${F.getUTCDate()} ${MOIS[F.getUTCMonth()]}${an}`;
  }
  function nbJours(debut, fin) {
    const d = parseDate(debut);
    const f = parseDate(fin);
    if (d === null || f === null || f < d) return "";
    const n = Math.round((f - d) / 86400000) + 1;
    return `${n} jour${n > 1 ? "s" : ""}`;
  }

  // Documents de l'onglet actif : à générer / généré (cliquable) / envoyé (+ cliquable si généré)
  function documentsHtml(d) {
    const doc = DOCUMENTS[documentActif];
    const envoye = Boolean(d[doc.champ]);
    const genere = ((d.statuts || {})[documentActif] || "non_genere") !== "non_genere";
    return doc.pdfs.map(([pdf, nom]) => {
      const libelle = nom.charAt(0).toUpperCase() + nom.slice(1);
      const badge = envoye ? '<em class="doc-envoye">Envoyé</em>' : "";
      if (genere) {
        return `<a class="doc is-genere${envoye ? " is-envoye" : ""}" href="/api/kits/${d.dossier_number}/download?document=${pdf}"
                   title="Télécharger le PDF (${nom})">
                  <span class="doc-ic">${svg(envoye ? ICO.coche : ICO.telecharger, 12)}</span><span class="doc-nom">${libelle}</span>${badge}</a>`;
      }
      return `<span class="doc${envoye ? " is-envoye" : ""}">
                <span class="doc-ic">${envoye ? svg(ICO.coche, 12) : ""}</span><span class="doc-nom">${libelle}</span>${badge}</span>`;
    }).join("");
  }

  function lienDossier(d) {
    return `<a class="lien-dossier" href="https://demarche.numerique.gouv.fr/procedures/${d.demarche || 128447}/a-suivre/dossiers/${d.dossier_number}"
              target="_blank" rel="noopener noreferrer">Dossier ${d.dossier_number}</a>`;
  }

  // Données affichées selon la page : titre, avatar, deux paires d'infos
  function contenu(d) {
    const dates = { ic: ICO.calendrier, haut: periode(d.date_debut_activite, d.date_fin_activite) || "Dates ?", bas: nbJours(d.date_debut_activite, d.date_fin_activite) };
    const trajet = d.date_trajet_aller || d.date_trajet_retour
      ? { ic: ICO.avion, haut: "Trajet", bas: periode(d.date_trajet_aller, d.date_trajet_retour, false) }
      : null;
    if (vue === "groupes") {
      return {
        titre: d.titre || "Centre non renseigné",
        avatar: svg(ICO.groupe, 20),
        infos: [dates, trajet || { ic: ICO.avion, haut: "Trajet", bas: "non renseigné" },
          { ic: ICO.groupe, haut: d.effectif ?? "?", bas: `apprenant${d.effectif > 1 ? "s" : ""}` },
          { ic: ICO.personne, haut: d.accompagnateurs || "?", bas: "accompagnateurs" }],
        resume: `${d.effectif ?? "?"} + ${d.accompagnateurs || "?"}`,
        resumeBas: "apprenants + acc.",
      };
    }
    const nom = d.nom || d.prenom ? `${d.nom || ""} ${d.prenom || ""}`.trim() : "Nom inconnu";
    const infos = [dates];
    if (vue === "personnel") {
      infos.push({ ic: ICO.badge, haut: d.type_mobilite || "Type ?", bas: "type de mobilité" });
      if (d.ville_accueil) infos.push({ ic: ICO.lieu, haut: d.ville_accueil, bas: "ville d'accueil" });
    } else if (trajet) infos.push(trajet);
    return {
      titre: nom,
      avatar: initiales(d),
      infos,
      resume: vue === "personnel" ? d.type_mobilite || "" : trajet ? trajet.bas : "",
      resumeBas: vue === "personnel" ? "type de mobilité" : trajet ? "trajet" : "",
    };
  }

  // Vue globale d'un dossier : les deux documents, quel que soit l'onglet actif
  function etatGlobal(d) {
    const complet = d.envoye_pedagogique && d.envoye_financier;
    if (complet) {
      return `<span class="etat-global is-complet" title="Tous les documents ont été envoyés">${svg(ICO.coche, 12)}Complet</span>`;
    }
    const pastille = (ok, court, long) =>
      `<span class="etat-doc${ok ? " is-ok" : ""}" title="${long} : ${ok ? "envoyé" : "à envoyer"}">${ok ? svg(ICO.coche, 10) : ""}${court}</span>`;
    return `<span class="etat-global">${pastille(d.envoye_pedagogique, "Péda", VUES[vue].libellePedagogique)}${pastille(d.envoye_financier, "Fin.", "Contrat financier")}</span>`;
  }

  // Synthèse de l'en-tête : avancement de chaque document et dossiers complets (cliquable = filtre)
  function renderSynthese() {
    const total = allDossiers.length;
    const el_ = document.getElementById("synthese");
    if (!total) {
      el_.innerHTML = "";
      return;
    }
    const peda = allDossiers.filter((d) => d.envoye_pedagogique).length;
    const fin = allDossiers.filter((d) => d.envoye_financier).length;
    const complets = allDossiers.filter((d) => d.envoye_pedagogique && d.envoye_financier).length;
    const jauge = (n, libelle, cle) => `
      <button type="button" class="synthese-item" data-onglet="${cle}" title="Afficher l'onglet ${libelle}">
        <span class="synthese-libelle">${libelle}</span>
        <span class="synthese-jauge"><span style="width:${(n / total) * 100}%"></span></span>
        <b>${n}/${total}</b>
      </button>`;
    el_.innerHTML =
      jauge(peda, VUES[vue].libellePedagogique, "pedagogique") +
      jauge(fin, "Contrat financier", "financier") +
      `<button type="button" class="synthese-item synthese-complets${filterComplet === "complets" ? " is-active" : ""}"
               data-complet="complets" aria-pressed="${filterComplet === "complets"}"
               title="${filterComplet === "complets" ? "Afficher tous les dossiers" : "N'afficher que les dossiers complets"}">
         ${svg(ICO.coche, 12)}<span class="synthese-libelle">Complets</span><b>${complets}/${total}</b>
       </button>` +
      `<button type="button" class="synthese-item synthese-incomplets${filterComplet === "incomplets" ? " is-active" : ""}"
               data-complet="incomplets" aria-pressed="${filterComplet === "incomplets"}"
               title="${filterComplet === "incomplets" ? "Afficher tous les dossiers" : "N'afficher que les dossiers incomplets"}">
         <span class="synthese-libelle">Incomplets</span><b>${total - complets}</b>
       </button>`;
  }

  function carteHtml(d) {
    const c = contenu(d);
    const sel = selected.has(String(d.dossier_number));
    const infos = c.infos.map((i) => `<div class="info">${svg(i.ic)}<div><b>${i.haut}</b>${i.bas ? `<small>${i.bas}</small>` : ""}</div></div>`).join("");
    return `
      <article class="carte${sel ? " is-selected" : ""}" data-dossier="${d.dossier_number}">
        <input class="carte-coche" type="checkbox" data-dossier="${d.dossier_number}" ${sel ? "checked" : ""}
               aria-label="Sélectionner le dossier ${d.dossier_number}">
        <div class="carte-entete">
          <span class="carte-avatar" aria-hidden="true">${c.avatar}</span>
          <div class="carte-nom">
            <h3>${c.titre}</h3>
            <p class="carte-sous-titre">${lienDossier(d)}<span class="carte-pays" title="${d.pays_accueil || ""}">${d.pays_accueil || "Pays ?"}</span></p>
          </div>
        </div>
        <div class="carte-infos">${infos}</div>
        <div class="carte-docs">${documentsHtml(d)}</div>
        <div class="carte-degrade" aria-hidden="true"></div>
        <div class="carte-pied">
          <p class="carte-etab">${svg(ICO.maison, 14)}${d.etablissement}</p>
          ${etatGlobal(d)}
        </div>
      </article>`;
  }

  function ligneHtml(d) {
    const c = contenu(d);
    const sel = selected.has(String(d.dossier_number));
    return `
      <article class="ligne${sel ? " is-selected" : ""}" data-dossier="${d.dossier_number}">
        <input class="carte-coche" type="checkbox" data-dossier="${d.dossier_number}" ${sel ? "checked" : ""}
               aria-label="Sélectionner le dossier ${d.dossier_number}">
        <span class="carte-avatar carte-avatar--petit" aria-hidden="true">${c.avatar}</span>
        <div class="ligne-nom"><h3>${c.titre}</h3><small>${lienDossier(d)} · ${d.etablissement}</small></div>
        <span class="carte-pays" title="${d.pays_accueil || ""}">${d.pays_accueil || "Pays ?"}</span>
        <div class="ligne-col"><b>${c.infos[0].haut}</b><small>${c.infos[0].bas || ""}</small></div>
        <div class="ligne-col"><b>${c.resume || "—"}</b><small>${c.resumeBas || ""}</small></div>
        <div class="ligne-docs">${documentsHtml(d)}</div>
        ${etatGlobal(d)}
      </article>`;
  }

  function render() {
    const visible = allDossiers.filter(matches);
    el.countVisible.textContent = visible.length;
    el.countTotal.textContent = allDossiers.length;
    const champ = DOCUMENTS[documentActif].champ;
    el.countATraiter.textContent = allDossiers.filter((d) => !d[champ]).length;
    renderSynthese();

    el.cards.innerHTML = visible.length
      ? visible.map(modeAffichage === "liste" ? ligneHtml : carteHtml).join("")
      : '<p class="empty-state">Aucun dossier ne correspond à ces filtres.</p>';

    el.cards.querySelectorAll('input[type="checkbox"]').forEach((box) => {
      box.addEventListener("change", () => {
        const id = box.dataset.dossier;
        if (box.checked) selected.add(id);
        else selected.delete(id);
        box.closest("[data-dossier].carte, [data-dossier].ligne")?.classList.toggle("is-selected", box.checked);
        updateSelectionUI();
      });
    });

    updateSelectionUI();
  }

  function updateSelectionUI() {
    const n = selected.size;
    el.selCount.textContent = `(${n})`;
    el.selCountBis.textContent = `(${n})`;
    el.selNombre.textContent = n;
    // Barre d'actions : visible dès qu'un dossier est sélectionné
    el.barreActions.hidden = n === 0 || vue === "dashboard" || Boolean(VUES[vue].bientot);
    // Boutons grisés si le service nécessaire est en échec
    el.btnGenerate.disabled = n === 0 || !sante.grist;
    const envoiOk = envoiConfigure[documentActif] !== false;
    el.btnSend.disabled = n === 0 || !sante.grist || !sante.dn || !envoiOk;
    el.btnSend.title = envoiOk ? "" : MESSAGE_NON_CONFIGURE;
    el.btnSyncDn.disabled = !sante.dn || !sante.grist || !synchroConfiguree;
    el.btnSyncDn.title = synchroConfiguree ? "" : MESSAGE_NON_CONFIGURE;

    const visibleIds = allDossiers
      .filter(matches)
      .map((d) => String(d.dossier_number));
    const selectedVisible = visibleIds.filter((id) => selected.has(id));
    el.toggleSelectAll.checked =
      visibleIds.length > 0 && selectedVisible.length === visibleIds.length;
    el.toggleSelectAll.indeterminate =
      selectedVisible.length > 0 && selectedVisible.length < visibleIds.length;
  }

  // Libellé du filtre d'envoi = document de l'onglet actif
  function majLibelleStatut() {
    const actif = document.querySelector('[data-filter="document"].is-active');
    const financier = actif && actif.dataset.value === "financier";
    el.statutLibelle.textContent = financier ? "Contrat financier" : VUES[vue].libellePedagogique;
  }

  // Affichage cartes / liste, mémorisé par page (localStorage, facultatif)
  function lireAffichage() {
    try {
      return localStorage.getItem(`pony-affichage-${vue}`) === "liste" ? "liste" : "cartes";
    } catch {
      return "cartes";
    }
  }
  function appliquerAffichage() {
    el.cards.classList.toggle("card-grid", modeAffichage === "cartes");
    el.cards.classList.toggle("liste-dossiers", modeAffichage === "liste");
    el.vueCartes.classList.toggle("is-active", modeAffichage === "cartes");
    el.vueListe.classList.toggle("is-active", modeAffichage === "liste");
    el.vueCartes.setAttribute("aria-pressed", modeAffichage === "cartes");
    el.vueListe.setAttribute("aria-pressed", modeAffichage === "liste");
  }
  function choisirAffichage(mode) {
    modeAffichage = mode;
    try {
      localStorage.setItem(`pony-affichage-${vue}`, mode);
    } catch {
      /* stockage indisponible : le choix vaut pour la session */
    }
    appliquerAffichage();
    render();
  }

  function populateEtablissements(etablissements) {
    etablissements.forEach((nom) => {
      const opt = document.createElement("option");
      opt.value = nom;
      opt.textContent = nom;
      el.filterEtab.appendChild(opt);
    });
  }

  async function loadDossiers(refresh) {
    if (vue === "dashboard") return loadDashboard(refresh);
    if (VUES[vue].bientot) return;
    const vueChargee = vue;
    const api = VUES[vue].api;
    const url = refresh ? `${api}?refresh=1` : api;
    el.btnRefresh.disabled = true;
    if (refresh) el.btnRefresh.classList.add("is-loading");

    const res = await fetch(url);
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      el.cards.innerHTML = `<p class="empty-state">Erreur de chargement des dossiers.${err.error ? `<br>${err.error}` : ""}</p>`;
      el.btnRefresh.disabled = false;
      el.btnRefresh.classList.remove("is-loading");
      return;
    }
    const data = await res.json();
    if (vueChargee !== vue) return; // la page a changé pendant le chargement
    // PDF générés pendant la session : conservés au rechargement et au changement de page
    // (le serveur ne les mémorise pas ; sans ça, les liens de téléchargement disparaissent)
    const generes = statutsSession[vueChargee] || {};
    allDossiers = data.dossiers.map((d) => {
      const avant = generes[String(d.dossier_number)];
      return avant ? { ...d, statuts: { ...(d.statuts || {}), ...avant } } : d;
    });
    envoiConfigure = data.envoi || {};
    synchroConfiguree = data.synchro !== false;
    el.filterEtab.innerHTML =
      '<option value="">Tous les établissements</option>';
    populateEtablissements(data.etablissements);
    render();
    el.btnRefresh.disabled = false;
    el.btnRefresh.classList.remove("is-loading");
  }

  async function generateSelection() {
    const ids = Array.from(selected);
    if (ids.length === 0) return;
    el.btnGenerate.disabled = true;

    const doc = documentActif;
    showToastProgress(`Génération du ${DOCUMENTS[doc].nom}…`, 0, ids.length);
    let successCount = 0;
    const failed = {};

    for (let i = 0; i < ids.length; i++) {
      const id = ids[i];
      try {
        const res = await fetch("/api/kits/generate", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ dossier_numbers: [id], document: doc }),
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.error || "erreur inconnue");
        if (!data.generated || !data.generated.length)
          throw new Error("PDF non généré (filtré par should_be_exported ?)");
        const dossier = allDossiers.find(
          (d) => String(d.dossier_number) === id,
        );
        if (dossier) dossier.statuts = { ...(dossier.statuts || {}), [doc]: "genere" };
        const parVue = (statutsSession[vue] = statutsSession[vue] || {});
        parVue[String(id)] = { ...(parVue[String(id)] || {}), [doc]: "genere" };
        successCount++;
      } catch (err) {
        failed[id] = err.message;
      }
      updateToastProgress(i + 1, ids.length);
      render();
    }

    showToastResult(
      "Génération terminée",
      successCount,
      ids.length,
      Object.keys(failed).length,
    );
    if (Object.keys(failed).length) {
      const lines = Object.entries(failed).map(
        ([n, msg]) => `<strong>#${n}</strong> — ${msg}`,
      );
      showInfoModal("Échec de génération", lines, "error");
    }
    updateSelectionUI();
  }

  function selectAllVisible() {
    allDossiers
      .filter(matches)
      .forEach((d) => selected.add(String(d.dossier_number)));
    render();
    updateSelectionUI();
  }

  function selectNone() {
    selected.clear();
    render();
    updateSelectionUI();
  }

  function wireSegmented(groupSelector, onChange) {
    const buttons = document.querySelectorAll(groupSelector);
    buttons.forEach((btn) => {
      btn.addEventListener("click", () => {
        buttons.forEach((b) => b.classList.remove("is-active"));
        btn.classList.add("is-active");
        onChange(btn.dataset.value);
        render();
      });
    });
  }

  async function sendSelection() {
    const ids = Array.from(selected);
    if (ids.length === 0) return;
    el.btnSend.disabled = true;

    const doc = documentActif;
    showToastProgress(`Envoi du ${DOCUMENTS[doc].nom}…`, 0, ids.length);
    let successCount = 0;
    const failed = {};

    for (let i = 0; i < ids.length; i++) {
      const id = ids[i];
      try {
        const res = await fetch("/api/kits/send", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ dossier_numbers: [id], document: doc }),
        });
        const data = await res.json();
        if (data.failed && data.failed[id]) throw new Error(data.failed[id]);
        if (!res.ok && res.status !== 207)
          throw new Error(data.error || "erreur inconnue");
        const dossier = allDossiers.find(
          (d) => String(d.dossier_number) === id,
        );
        if (dossier) {
          dossier[DOCUMENTS[doc].champ] = true;
        }
        successCount++;
      } catch (err) {
        failed[id] = err.message;
      }
      updateToastProgress(i + 1, ids.length);
      render();
    }

    showToastResult(
      "Envoi terminé",
      successCount,
      ids.length,
      Object.keys(failed).length,
    );
    if (Object.keys(failed).length) {
      const lines = Object.entries(failed).map(
        ([n, msg]) => `<strong>#${n}</strong> — ${msg}`,
      );
      showInfoModal("Échec d'envoi", lines, "error");
    }
    updateSelectionUI();
  }

  async function syncWithDn() {
    el.btnSyncDn.disabled = true;
    showToastProgress("Vérification avec DN en cours…", 0, 1);

    try {
      const res = await fetch("/api/dossiers/sync-dn", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ demarche: vue }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "erreur inconnue");

      showToastResult("Vérification terminée", 1, 1, 0);
      const lines = [];
      if (data.corriges && data.corriges.length) {
        lines.push(
          `Kit pédagogique : ${data.corriges.length} dossier(s) corrigé(s) : #${data.corriges.join(", #")}`,
        );
      }
      if (data.corriges_financier && data.corriges_financier.length) {
        lines.push(
          `Contrat financier : ${data.corriges_financier.length} dossier(s) corrigé(s) : #${data.corriges_financier.join(", #")}`,
        );
      }
      if (data.erreurs && Object.keys(data.erreurs).length) {
        Object.entries(data.erreurs).forEach(([n, msg]) => {
          lines.push(`<strong>${n}</strong> — ${msg}`);
        });
      }
      if (lines.length) {
        const hasErrors = data.erreurs && Object.keys(data.erreurs).length;
        showInfoModal(
          "Résultat de la vérification",
          lines,
          hasErrors ? "error" : null,
        );
      }
      await loadDossiers(true);
    } catch (err) {
      showToastResult("Échec de la vérification", 0, 1, 1);
      showInfoModal("Erreur", [`Vérification : ${err.message}`], "error");
    } finally {
      el.btnSyncDn.disabled = !sante.dn || !sante.grist || !synchroConfiguree;
    }
  }

  el.filterEtab.addEventListener("change", render);
  el.search.addEventListener("input", render);
  el.btnGenerate.addEventListener("click", generateSelection);
  el.btnRefresh.addEventListener("click", () => {
    loadDossiers(true);
    verifierSante(false);
  });
  ["grist", "dn"].forEach((k) =>
    document
      .getElementById(`sante-${k}`)
      .addEventListener("click", () => verifierSante(false)),
  );
  el.btnSyncDn.addEventListener("click", syncWithDn);
  el.btnSend.addEventListener("click", sendSelection);
  el.toastClose.addEventListener("click", hideToast);
  el.modalClose.addEventListener("click", hideInfoModal);
  el.modal.addEventListener("click", (e) => {
    if (e.target === el.modal) hideInfoModal();
  });
  el.toggleSelectAll.addEventListener("change", () => {
    if (el.toggleSelectAll.checked) selectAllVisible();
    else selectNone();
  });
  wireSegmented('[data-filter="statut"]', (value) => (filterStatut = value));
  // Onglets : le document traité change, le filtre d'envoi repart sur « Tous »
  wireSegmented('[data-filter="document"]', (value) => {
    setDocument(VUES[vue].documents[value]);
    majLibelleStatut();
    filterStatut = "tous";
    document.querySelectorAll('[data-filter="statut"]').forEach((b) =>
      b.classList.toggle("is-active", b.dataset.value === "tous"));
  });
  document.getElementById("synthese").addEventListener("click", (e) => {
    const b = e.target.closest(".synthese-item");
    if (!b) return;
    if (b.dataset.complet) {
      filterComplet = filterComplet === b.dataset.complet ? "" : b.dataset.complet;
      render();
      return;
    }
    // jauge d'un document : bascule sur son onglet
    document.querySelector(`[data-filter="document"][data-value="${b.dataset.onglet}"]`)?.click();
  });
  el.btnTout.addEventListener("click", selectAllVisible);
  el.btnAucun.addEventListener("click", selectNone);
  el.vueCartes.addEventListener("click", () => choisirAffichage("cartes"));
  el.vueListe.addEventListener("click", () => choisirAffichage("liste"));
  // Clic sur une carte / ligne : (dé)sélection, sauf sur un lien (document, dossier DN)
  el.cards.addEventListener("click", (e) => {
    if (e.target.closest("a, input, button")) return;
    const carte = e.target.closest("[data-dossier]");
    if (!carte) return;
    const id = String(carte.dataset.dossier);
    if (selected.has(id)) selected.delete(id);
    else selected.add(id);
    const coche = carte.querySelector('input[type="checkbox"]');
    if (coche) coche.checked = selected.has(id);
    carte.classList.toggle("is-selected", selected.has(id));
    updateSelectionUI();
  });

  // Navigation entre les pages par le rail (#apprenants, #groupes)
  // --- Tableau de bord du consortium ---

  const COULEURS_TYPES = { apprenants: "#6C38F5", groupes: "#D9772F", personnel: "#1E4FD8" };
  const nf = (n) => Number(n || 0).toLocaleString("fr-FR");
  const euros = (n) => `${nf(Math.round(n || 0))} €`;
  const pct = (a, b) => (b ? Math.round((a / b) * 100) : 0);
  const dash = {
    projet: document.getElementById("filter-projet"),
    annee: document.getElementById("filter-annee-dash"),
    type: document.getElementById("filter-type-dash"),
  };
  const TYPES_DASH = [
    ["apprenants", "Apprenants"],
    ["groupes", "Groupes"],
    ["personnel", "Personnel"],
  ];

  function remplirSelect(sel, libelleTous, valeurs) {
    const courant = sel.value;
    sel.innerHTML = `<option value="">${libelleTous}</option>` +
      valeurs.map((v) => `<option value="${v}">${v}</option>`).join("");
    sel.value = valeurs.includes(courant) ? courant : "";
  }

  const ICONES_KPI = {
    mobilites: '<circle cx="12" cy="12" r="10"/><path d="M12 2a14.5 14.5 0 0 0 0 20 14.5 14.5 0 0 0 0-20"/><path d="M2 12h20"/>',
    apprenants: '<path d="M21.42 10.922a1 1 0 0 0-.019-1.838L12.83 5.18a2 2 0 0 0-1.66 0L2.6 9.08a1 1 0 0 0 0 1.832l8.57 3.908a2 2 0 0 0 1.66 0z"/><path d="M22 10v6"/><path d="M6 12.5V16a6 3 0 0 0 12 0v-3.5"/>',
    personnel: '<path d="M11.5 15H7a4 4 0 0 0-4 4v2"/><path d="M21.4 16.6a1 1 0 0 0-3-3l-4 4a2 2 0 0 0-.5.9l-.8 2.9a.5.5 0 0 0 .6.6l2.9-.8a2 2 0 0 0 .9-.5z"/><circle cx="10" cy="7" r="4"/>',
    groupes: '<path d="M17 21a5 5 0 0 0-10 0"/><path d="M22 10.5a3.5 3.5 0 0 0-5.5-2.9"/><path d="M7.5 7.6A3.5 3.5 0 0 0 2 10.5"/><circle cx="12" cy="13" r="3"/><circle cx="18.5" cy="4.5" r="2.5"/><circle cx="5.5" cy="4.5" r="2.5"/>',
    experts: '<circle cx="15" cy="7" r="4"/><path d="M13 15h5a4 4 0 0 1 4 4v2"/><path d="M2 14h7"/><path d="m6 11 3 3-3 3"/>',
  };

  function kpi(cle, libelle, valeur, detail, teinte) {
    return `<div class="dash-card dash-kpi">
        <div class="dash-kpi-icone dash-kpi-icone--${teinte}">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${ICONES_KPI[cle]}</svg>
        </div>
        <div><div class="dash-kpi-libelle">${libelle}</div><div class="dash-kpi-valeur">${valeur == null ? "—" : nf(valeur)}</div><div class="dash-kpi-detail">${detail}</div></div>
      </div>`;
  }

  // Infobulles façon Metabase : fond foncé, pastille, valeur, %, total
  let infobulles = [];
  function infobulle(titre, lignes, active) {
    infobulles.push({ titre, lignes, active });
    return `data-tip="${infobulles.length - 1}"`;
  }
  const tipEl = document.createElement("div");
  tipEl.className = "dash-tip";
  tipEl.hidden = true;
  document.body.appendChild(tipEl);
  function afficherInfobulle(ev) {
    const cible = ev.target.closest("[data-tip]");
    const tip = cible && infobulles[cible.dataset.tip];
    if (!tip) { tipEl.hidden = true; return; }
    const total = tip.lignes.reduce((t, l) => t + l.valeur, 0);
    tipEl.innerHTML = `<div class="dash-tip-titre">${tip.titre}</div><table>${
      tip.lignes.map((l, i) => `<tr class="${i === tip.active ? "actif" : ""}">
        <td><span class="dash-puce" style="background:${l.couleur}"></span>${l.libelle}</td>
        <td>${nf(l.valeur)}</td><td>${pct(l.valeur, total)} %</td></tr>`).join("")
    }<tr class="total"><td>Total</td><td>${nf(total)}</td><td>100 %</td></tr></table>`;
    tipEl.hidden = false;
    const m = 14, w = tipEl.offsetWidth, h = tipEl.offsetHeight;
    let x = ev.clientX + m, y = ev.clientY + m;
    if (x + w > innerWidth - 8) x = ev.clientX - w - m;
    if (y + h > innerHeight - 8) y = ev.clientY - h - m;
    tipEl.style.left = `${x}px`;
    tipEl.style.top = `${y}px`;
  }
  document.getElementById("view-dashboard").addEventListener("mousemove", afficherInfobulle);
  document.getElementById("view-dashboard").addEventListener("mouseleave", () => { tipEl.hidden = true; });

  // Donut SVG : segments [{libelle, valeur, couleur}] séparés de 2 px
  function donut(segments, centre, sousCentre, aria) {
    const total = segments.reduce((t, s) => t + s.valeur, 0) || 1;
    const r = 54;
    const c = 2 * Math.PI * r;
    let debut = 0;
    const lignes = segments.map(({ libelle, valeur, couleur }) => ({ libelle, valeur, couleur }));
    const arcs = segments.map((s, i) => {
      const longueur = (s.valeur / total) * c;
      const arc = `<circle class="dash-seg" cx="64" cy="64" r="${r}" stroke="${s.couleur}" stroke-dasharray="${Math.max(0, longueur - 2).toFixed(2)} ${c.toFixed(2)}" stroke-dashoffset="${(-debut).toFixed(2)}" ${infobulle(aria, lignes, i)}></circle>`;
      debut += longueur;
      return arc;
    }).join("");
    const legende = segments.map((s) =>
      `<li><span class="dash-puce" style="background:${s.couleur}"></span>${s.libelle}<strong>${s.legende ?? `${pct(s.valeur, total)} %`}</strong></li>`).join("");
    return `<svg width="128" height="128" viewBox="0 0 128 128" role="img" aria-label="${aria}">
        <g transform="rotate(-90 64 64)" fill="none" stroke-width="16">${arcs}</g>
        <text x="64" y="62" text-anchor="middle" class="dash-donut-centre">${centre}</text>
        <text x="64" y="80" text-anchor="middle" class="dash-donut-sous">${sousCentre}</text>
      </svg><ul class="dash-legende">${legende}</ul>`;
  }

  function renderDashboard(d) {
    const t = d.totaux;
    infobulles = [];
    document.getElementById("dash-exemple").hidden = !d.exemple;
    const typeChoisi = dash.type.options[dash.type.selectedIndex];
    const filtres = [
      el.filterEtab.value || "tous établissements",
      dash.projet.value || "tous projets",
      dash.annee.value || "toutes années",
      dash.type.value ? typeChoisi.textContent.toLowerCase() : "tous types",
    ];
    document.getElementById("dash-sous-titre").textContent = `Mobilités Erasmus+ : ${filtres.join(", ")}`;
    // Temps de lecture Grist (test de performance)
    const ch = d.chargement;
    const chronoEl = document.getElementById("dash-chrono");
    if (ch && chronoEl) {
      chronoEl.textContent = ch.memoire
        ? `Données en mémoire (lues dans Grist en ${(ch.ms / 1000).toFixed(1).replace(".", ",")} s)`
        : `Lu dans Grist en ${(ch.ms / 1000).toFixed(1).replace(".", ",")} s (${ch.mode === "sql" ? `${ch.tables.length} requêtes ciblées` : `${ch.tables.length} tables complètes`})`;
      chronoEl.title = ch.tables.map((t) => `${t.table} : ${t.ms} ms, ${t.lignes} lignes`).join("\n") +
        (ch.erreur_sql ? `\n\nSQL indisponible : ${ch.erreur_sql}` : "");
    }

    document.getElementById("dash-kpis").innerHTML =
      kpi("mobilites", "Mobilités", t.mobilites, "tous types confondus", "violet") +
      kpi("apprenants", "Apprenants", t.apprenants, "mobilités individuelles", "violet") +
      kpi("personnel", "Personnel", t.personnel, "mobilités du personnel", "bleu") +
      kpi("groupes", "Groupes", t.groupes, `${nf(t.participants_groupes)} participants`, "violet") +
      // Experts invités : démarche DN pas encore créée
      kpi("experts", "Experts invités", t.experts ?? null, t.experts == null ? "démarche à venir" : "mobilités entrantes", "bleu");

    // Barres empilées par type (violet / orange / bleu), info-bulle par segment
    const max = Math.max(1, ...d.par_etablissement.map((e) => e.mobilites));
    const typesVisibles = TYPES_DASH.filter(([cle]) => !dash.type.value || dash.type.value === cle);
    document.getElementById("dash-etabs-legende").innerHTML = typesVisibles
      .map(([cle, lib]) => `<li><span class="dash-puce" style="background:${COULEURS_TYPES[cle]}"></span>${lib}</li>`)
      .join("");
    document.getElementById("dash-etabs").innerHTML = d.par_etablissement.length
      ? d.par_etablissement.map((e) => {
          const lignes = typesVisibles.map(([cle, lib]) => ({ libelle: lib, valeur: e[cle], couleur: COULEURS_TYPES[cle] }));
          const segments = typesVisibles
            .map(([cle], i) => e[cle] > 0
              ? `<span class="dash-barre-seg" style="flex:${e[cle]} 1 0;background:${COULEURS_TYPES[cle]}" ${infobulle(e.nom, lignes, i)}></span>`
              : "")
            .join("");
          return `
        <div class="dash-barre">
          <span class="dash-barre-nom" title="${e.nom}">${e.nom}</span>
          <div class="dash-barre-piste"><div class="dash-barre-val" style="width:${(e.mobilites / max) * 100}%">${segments}</div></div>
          <span class="dash-barre-nb" ${infobulle(e.nom, lignes, -1)}>${nf(e.mobilites)}</span>
          <span class="dash-barre-montant">${euros(e.montant_engage)}</span>
        </div>`;
        }).join("")
      : '<p class="empty-state">Aucune mobilité pour ces filtres.</p>';

    document.getElementById("dash-donut-type").innerHTML = donut(
      [
        { libelle: "Apprenants", valeur: t.apprenants, couleur: COULEURS_TYPES.apprenants },
        { libelle: "Groupes", valeur: t.groupes, couleur: COULEURS_TYPES.groupes },
        { libelle: "Personnel", valeur: t.personnel, couleur: COULEURS_TYPES.personnel },
      ],
      nf(t.mobilites), "mobilités", "Mobilités par type");
    const st = d.statut;
    const blocStatut = document.getElementById("dash-donut-statut");
    blocStatut.hidden = !st;
    if (st) blocStatut.innerHTML = donut(
      [
        { libelle: "Public", valeur: st.public, couleur: COULEURS_TYPES.apprenants, legende: nf(st.public) },
        { libelle: "Privé", valeur: st.prive, couleur: COULEURS_TYPES.groupes, legende: nf(st.prive) },
      ],
      `${pct(st.public, st.public + st.prive)} %`, "public", "Établissements publics et privés");

    const sub = d.subvention;
    const taux = pct(sub.engagee, sub.accordee);
    const r = 70;
    const c = 2 * Math.PI * r;
    document.getElementById("dash-anneau").innerHTML = `
      <svg width="190" height="190" viewBox="0 0 190 190" role="img" aria-label="Subvention consommée : ${taux} %">
        <circle cx="95" cy="95" r="${r}" fill="none" stroke="#f1eeff" stroke-width="18"></circle>
        <circle cx="95" cy="95" r="${r}" fill="none" stroke="#6c38f5" stroke-width="18" stroke-linecap="round"
          stroke-dasharray="${((Math.min(taux, 100) / 100) * c).toFixed(2)} ${c.toFixed(2)}" transform="rotate(-90 95 95)"></circle>
        <text x="95" y="96" text-anchor="middle" class="dash-anneau-val">${taux} %</text>
        <text x="95" y="118" text-anchor="middle" class="dash-donut-sous">de la subvention</text>
      </svg>`;
    const ligne = (libelle, montant, part, couleur) => `
      <div class="dash-card dash-montant">
        <div class="dash-montant-tete"><span>${libelle}</span>${part != null ? `<strong style="color:${couleur}">${part} %</strong>` : ""}</div>
        <div class="dash-montant-val">${euros(montant)}</div>
        ${part != null ? `<div class="dash-piste"><div style="width:${Math.min(part, 100)}%;background:${couleur}"></div></div>` : ""}
      </div>`;
    const ligneDetail = (libelle, montant, detail) => `
      <div class="dash-card dash-montant">
        <div class="dash-montant-tete"><span>${libelle}</span></div>
        <div class="dash-montant-val">${euros(montant)}</div>
        <div class="dash-montant-detail">${detail}</div>
      </div>`;
    document.getElementById("dash-montants").innerHTML =
      ligne("Subvention accordée", sub.accordee) +
      ligne("Montant engagé", sub.engagee, taux, "#6c38f5") +
      (sub.versee != null ? ligne("Montant versé", sub.versee, pct(sub.versee, sub.accordee), "#1e4fd8") : "") +
      ligne("Reste à engager", Math.max(0, sub.accordee - sub.engagee)) +
      `<h3 class="dash-sous-titre">Autres montants</h3>` +
      ligneDetail("Montant PAMO", sub.pamo, sub.pamo_participants == null
        ? `forfait ${euros(sub.pamo_forfait)} par participant (participants PAMO à brancher)`
        : `${euros(sub.pamo_forfait)} × ${nf(sub.pamo_participants)} participants`) +
      `<h3 class="dash-sous-titre">Soutien organisationnel</h3>` +
      ligneDetail("OS établissement", sub.os_etablissement, "part des établissements") +
      ligneDetail("OS ENSFEA", sub.os_ensfea, "part de l'ENSFEA") +
      ligneDetail("OS total", sub.os_etablissement + sub.os_ensfea,
        `${nf(sub.participants_indiv)} participants individuels, ${nf(sub.participants_groupes)} en groupe`);
  }

  // --- Carte des pays d'accueil --------------------------------------------------
  // Fond de carte Europe pré-projeté (scripts/carte/generer.mjs), chargé une seule fois
  let fondCarte = null;
  const PALETTE_CARTE = ["#ECE8FD", "#C9BCFB", "#A386F8", "#7E54F6", "#5424D6"];
  const GRIS_CARTE = "#E6E4EF";

  async function chargerFondCarte() {
    if (!fondCarte) fondCarte = await (await fetch("/static/data/carte-europe.json")).json();
    return fondCarte;
  }

  function nomPays(code) {
    if (!code) return "Non renseigné";
    return (fondCarte && fondCarte.noms[code]) || code;
  }

  async function renderCarte(parPays) {
    const fond = await chargerFondCarte();
    const index = Object.fromEntries(parPays.map((p) => [p.code, p]));
    const max = Math.max(1, ...parPays.map((p) => p.total));
    // 5 classes de même largeur entre 1 et le maximum
    const couleur = (n) => (n > 0 ? PALETTE_CARTE[Math.min(4, Math.floor((n / max) * 5 - 1e-9))] : GRIS_CARTE);
    const lignesPays = (p) => TYPES_DASH.map(([cle, lib]) => ({ libelle: lib, valeur: p[cle], couleur: COULEURS_TYPES[cle] }));

    const surCarte = new Set();
    const paths = fond.pays.map((f) => {
      const p = index[f.iso2];
      if (p) surCarte.add(f.iso2);
      const tip = p ? infobulle(f.nom, lignesPays(p), -1) : "";
      return `<path class="carte-pays${p ? " carte-pays--actif" : ""}" d="${f.d}" fill="${couleur(p ? p.total : 0)}" ${tip}></path>`;
    }).join("");
    // Petits pays avec des mobilités (Malte, Luxembourg…) : pastille au centre, au-dessus des autres
    const reperes = fond.pays.filter((f) => f.c && index[f.iso2]).map((f) =>
      `<circle class="carte-pays carte-pays--actif carte-repere" cx="${f.c[0]}" cy="${f.c[1]}" r="6" fill="${couleur(index[f.iso2].total)}" ${infobulle(f.nom, lignesPays(index[f.iso2]), -1)}></circle>`).join("");
    document.getElementById("dash-carte").innerHTML =
      `<svg viewBox="0 0 ${fond.largeur} ${fond.hauteur}" role="img" aria-label="Carte des mobilités par pays d'accueil">${paths}${reperes}</svg>`;
    document.getElementById("dash-carte-legende").innerHTML =
      `<span>1</span>${PALETTE_CARTE.map((c) => `<i style="background:${c}"></i>`).join("")}<span>${nf(max)} mobilités</span>` +
      `<i class="carte-legende-aucune" style="background:${GRIS_CARTE}"></i><span>aucune</span>`;

    const ligneListe = (p, barre) => `<li ${infobulle(nomPays(p.code), lignesPays(p), -1)}><span>${nomPays(p.code)}</span><strong>${nf(p.total)}</strong>` +
      (barre ? `<div class="carte-barre"><span style="width:${(p.total / max) * 100}%"></span></div>` : "") + "</li>";
    // le classement ignore les pays non renseignés (listés sous « Hors de la carte »)
    const classes = parPays.filter((p) => p.code);
    document.getElementById("dash-carte-top").innerHTML = classes.length
      ? classes.slice(0, 5).map((p) => ligneListe(p, true)).join("")
      : '<li class="carte-vide">Aucune mobilité</li>';
    const hors = parPays.filter((p) => !surCarte.has(p.code));
    document.getElementById("dash-carte-hors-bloc").hidden = !hors.length;
    document.getElementById("dash-carte-hors").innerHTML = hors.map((p) => ligneListe(p, false)).join("");
  }

  async function loadDashboard(refresh) {
    const params = new URLSearchParams({
      ...(refresh ? { refresh: "1" } : {}),
      etablissement: el.filterEtab.value,
      code_projet: dash.projet.value,
      annee: dash.annee.value,
      type: dash.type.value,
    });
    try {
      const res = await fetch(`/api/dashboard?${params}`);
      const d = await res.json();
      if (!res.ok) throw new Error(d.error || `HTTP ${res.status}`);
      if (vue !== "dashboard") return;
      remplirSelect(el.filterEtab, "Tous les établissements", d.filtres.etablissements);
      remplirSelect(dash.projet, "Tous les projets", d.filtres.codes_projet);
      // Premier affichage : code projet par défaut (l'utilisateur peut choisir « Tous »)
      if (!dash.projetInitialise && d.filtres.code_projet_defaut) {
        dash.projetInitialise = true;
        if (d.filtres.codes_projet.includes(d.filtres.code_projet_defaut)) {
          dash.projet.value = d.filtres.code_projet_defaut;
          return loadDashboard();
        }
      }
      remplirSelect(dash.annee, "Toutes les années", d.filtres.annees);
      const typeCourant = dash.type.value;
      dash.type.innerHTML = '<option value="">Tous les types</option>' +
        d.filtres.types.map((t) => `<option value="${t.valeur}">${t.libelle}</option>`).join("");
      dash.type.value = typeCourant;
      renderDashboard(d);
      renderCarte(d.par_pays || []);
    } catch (err) {
      showInfoModal("Tableau de bord", [`Chargement impossible : ${err.message}`], "error");
    }
  }

  [el.filterEtab, dash.projet, dash.annee, dash.type].forEach((sel) =>
    sel.addEventListener("change", () => {
      if (vue === "dashboard") loadDashboard();
    }),
  );

  function setVue() {
    const h = location.hash.slice(1);
    vue = VUES[h] ? h : "apprenants";
    document.body.classList.toggle("vue-groupes", vue === "groupes");
    document.body.classList.toggle("vue-dashboard", vue === "dashboard");
    // Pages pas encore construites : message « Bientôt disponible »
    document.body.classList.toggle("vue-bientot", Boolean(VUES[vue].bientot));
    if (VUES[vue].bientot) {
      document.getElementById("bientot-titre").textContent = VUES[vue].titre;
      document.getElementById("bientot-texte").textContent = VUES[vue].bientot;
    }
    // Le sélecteur garde son choix (péda / financier) d'une page à l'autre
    const actif = document.querySelector('[data-filter="document"].is-active');
    setDocument(VUES[vue].documents[(actif && actif.dataset.value) || "pedagogique"]);
    document.getElementById("doc-option-pedagogique").innerHTML =
      `${VUES[vue].libellePedagogique} <small>+ attestation</small>`;
    majLibelleStatut();
    filterStatut = "tous";
    document.querySelectorAll('[data-filter="statut"]').forEach((b) =>
      b.classList.toggle("is-active", b.dataset.value === "tous"));
    modeAffichage = lireAffichage();
    appliquerAffichage();
    document.getElementById("page-title").textContent = VUES[vue].titre;
    el.search.placeholder = VUES[vue].recherche;
    document.querySelectorAll(".rail-icon[data-view]").forEach((a) => {
      const on = a.dataset.view === vue;
      a.classList.toggle("rail-icon--active", on);
      if (on) a.setAttribute("aria-current", "page");
      else a.removeAttribute("aria-current");
    });
    selected.clear();
    el.countVisible.textContent = "0";
    el.countTotal.textContent = "0";
    el.countATraiter.textContent = "0";
    filterComplet = "";
    el.search.value = "";
    el.filterEtab.value = "";
    allDossiers = [];
    if (vue === "dashboard") {
      loadDashboard();
      return;
    }
    if (VUES[vue].bientot) return;
    el.cards.innerHTML = '<p class="empty-state">Chargement des dossiers…</p>';
    loadDossiers(false);
  }
  window.addEventListener("hashchange", setVue);

  setVue();
  verifierSante(false);
})();
