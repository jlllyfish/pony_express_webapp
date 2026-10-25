(function () {
  "use strict";

  let allDossiers = [];
  const selected = new Set();
  let filterKit = "tous";
  let filterFinancier = "tous";
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
      libellePedagogique: "Kit péda + attestation",
      titre: "Mobilités Apprenant",
      recherche: "Nom du participant",
    },
    groupes: {
      api: "/api/groupes",
      documents: { pedagogique: "pedagogique_groupe", financier: "financier_groupe" },
      libellePedagogique: "Contrat péda",
      titre: "Mobilités de groupe",
      recherche: "Centre constitutif",
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
      court: "le contrat péda",
      nom: "contrat pédagogique",
      champ: "envoye_pedagogique",
      pdfs: [["pedagogique_groupe", "contrat pédagogique"]],
    },
    financier_groupe: {
      court: "le contrat financier",
      nom: "contrat financier",
      champ: "envoye_financier",
      pdfs: [["financier_groupe", "contrat financier"]],
    },
  };

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

    if (filterKit === "envoye" && !dossier.envoye_pedagogique) return false;
    if (filterKit === "a_envoyer" && dossier.envoye_pedagogique) return false;
    if (filterFinancier === "envoye" && !dossier.envoye_financier) return false;
    if (filterFinancier === "a_envoyer" && dossier.envoye_financier)
      return false;

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

  // Tuile d'une mobilité de groupe
  function cardGroupe(g) {
    const complet = g.envoye_pedagogique && g.envoye_financier;
    const doc = DOCUMENTS[documentActif];
    const statut = g[doc.champ]
      ? "envoye"
      : (g.statuts || {})[documentActif] || "non_genere";
    const downloadLink =
      statut !== "non_genere"
        ? doc.pdfs
            .map(
              ([pdf, nom]) =>
                `<a class="card-download" href="/api/kits/${g.dossier_number}/download?document=${pdf}">Télécharger le PDF<br>(${nom})</a>`,
            )
            .join("")
        : "";
    const checked = selected.has(String(g.dossier_number)) ? "checked" : "";
    const activite =
      g.date_debut_activite || g.date_fin_activite
        ? `${g.date_debut_activite || "?"} → ${g.date_fin_activite || "?"}${duree(g.date_debut_activite, g.date_fin_activite)}`
        : "";
    const trajet =
      g.date_trajet_aller || g.date_trajet_retour
        ? `Trajet ${g.date_trajet_aller || "?"} → ${g.date_trajet_retour || "?"}`
        : "";
    const svg = (paths, cls = "date-icon") =>
      `<svg width="14" height="14" class="${cls}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">${paths}</svg>`;
    const calendarIcon = svg('<path d="M8 2v3"/><path d="M16 2v3"/><rect x="3" y="3" width="18" height="18" rx="2"/><path d="M3 9h18"/>');
    const etabIcon = svg('<path d="M15 21v-8a1 1 0 0 0-1-1h-4a1 1 0 0 0-1 1v8"/><path d="M3 10a2 2 0 0 1 .709-1.528l7-6a2 2 0 0 1 2.582 0l7 6A2 2 0 0 1 21 10v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>', "etab-icon");
    const usersIcon = '<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>';
    const accompIcon = '<circle cx="12" cy="8" r="5"/><path d="M20 21a8 8 0 0 0-16 0"/>';
    const coche = (ok) =>
      ok
        ? `<svg width="16" height="16" class="check-icon is-done" viewBox="0 0 20 20" fill="none"><circle cx="10" cy="10" r="8" fill="currentColor"/><path d="M6.3 10.3l2.3 2.3 4.7-5" stroke="#fff" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>`
        : `<svg width="16" height="16" class="check-icon" viewBox="0 0 20 20" fill="none"><circle cx="10" cy="10" r="8" stroke="currentColor" stroke-width="1.6"/></svg>`;

    return `
      <article class="card" data-dossier="${g.dossier_number}">
        <div class="card-avatar card-avatar--groupe${complet ? " is-complet" : ""}" aria-hidden="true">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">${usersIcon}</svg>
        </div>
        <div class="card-body">
          <div class="card-header-row">
            <h3 class="card-title">${g.titre || "Centre non renseigné"}</h3>
            <span class="pill-pays-wrap" data-full="${g.pays_accueil || ""}">
              <span class="pill-pays">${g.pays_accueil || "Pays ?"}</span>
            </span>
          </div>
          <hr class="card-divider">

          <a class="card-sub card-dossier-link"
             href="https://demarche.numerique.gouv.fr/procedures/${g.demarche}/a-suivre/dossiers/${g.dossier_number}"
             target="_blank" rel="noopener noreferrer">Dossier ${g.dossier_number}</a>

          ${activite ? `<p class="card-dates">${calendarIcon}${activite}</p>` : ""}
          ${trajet ? `<p class="card-dates card-dates--soft">${calendarIcon}${trajet}</p>` : ""}

          <div class="card-effectifs">
            <p class="card-dates">${svg(usersIcon)}${g.effectif ?? "?"} apprenant${g.effectif > 1 ? "s" : ""}</p>
            <p class="card-dates">${svg(accompIcon)}Accompagnateurs : ${g.accompagnateurs || "?"}</p>
          </div>

          <div class="card-checks">
            <span class="check-item">${coche(g.envoye_pedagogique)} Contrat pédagogique</span>
            <span class="check-item">${coche(g.envoye_financier)} Contrat financier</span>
          </div>
        </div>
        ${downloadLink}
        <div class="card-status-bar ${complet ? "is-envoye" : g.envoye_pedagogique || g.envoye_financier ? "is-genere" : ""}"></div>
        <p class="card-etablissement">${etabIcon}${g.etablissement}</p>
        <label class="card-select">
          <input type="checkbox" data-dossier="${g.dossier_number}" ${checked}
                 aria-label="Sélectionner le dossier ${g.dossier_number}">
        </label>
      </article>
    `;
  }

  function cardTemplate(dossier) {
    if (vue === "groupes") return cardGroupe(dossier);
    // Statut du document actuellement choisi dans le sélecteur
    const statut = dossier[DOCUMENTS[documentActif].champ]
      ? "envoye"
      : (dossier.statuts || {})[documentActif] || "non_genere";
    const statusClass =
      statut === "envoye" ? "is-envoye" : statut === "genere" ? "is-genere" : "";
    const checked = selected.has(String(dossier.dossier_number))
      ? "checked"
      : "";
    const downloadLink =
      statut !== "non_genere"
        ? DOCUMENTS[documentActif].pdfs
            .map(
              ([pdf, nom]) =>
                `<a class="card-download" href="/api/kits/${dossier.dossier_number}/download?document=${pdf}">Télécharger le PDF<br>(${nom})</a>`,
            )
            .join("")
        : "";

    const activite =
      dossier.date_debut_activite || dossier.date_fin_activite
        ? `${dossier.date_debut_activite || "?"} → ${dossier.date_fin_activite || "?"}${duree(dossier.date_debut_activite, dossier.date_fin_activite)}`
        : "";
    const trajet =
      dossier.date_trajet_aller || dossier.date_trajet_retour
        ? `Trajet ${dossier.date_trajet_aller || "?"} → ${dossier.date_trajet_retour || "?"}`
        : "";

    const calendarIcon = `<svg width="14" height="14" class="date-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M8 2v3"/><path d="M16 2v3"/><rect x="3" y="3" width="18" height="18" rx="2"/><path d="M3 9h18"/>
      </svg>`;
    const etabIcon = `<svg width="14" height="14" class="etab-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M15 21v-8a1 1 0 0 0-1-1h-4a1 1 0 0 0-1 1v8"/><path d="M3 10a2 2 0 0 1 .709-1.528l7-6a2 2 0 0 1 2.582 0l7 6A2 2 0 0 1 21 10v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>
      </svg>`;

    const iconNotSent = `<svg width="16" height="16" class="check-icon" viewBox="0 0 20 20" fill="none">
        <circle cx="10" cy="10" r="8" stroke="currentColor" stroke-width="1.6"/>
      </svg>`;
    const iconSent = `<svg width="16" height="16" class="check-icon is-done" viewBox="0 0 20 20" fill="none">
        <circle cx="10" cy="10" r="8" fill="currentColor"/>
        <path d="M6.3 10.3l2.3 2.3 4.7-5" stroke="#fff" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
      </svg>`;

    return `
      <article class="card" data-dossier="${dossier.dossier_number}">
        <div class="card-avatar${dossier.envoye_pedagogique && dossier.envoye_financier ? " is-complet" : ""}"
             ${dossier.envoye_pedagogique && dossier.envoye_financier ? 'title="Les deux contrats ont été envoyés"' : ""}>${initiales(dossier)}</div>
        <div class="card-body">
          <div class="card-header-row">
            <h3 class="card-title">${
              dossier.nom || dossier.prenom
                ? `${dossier.nom || ""}<br>${dossier.prenom || ""}`
                : "Nom inconnu"
            }</h3>
            <span class="pill-pays-wrap" data-full="${dossier.pays_accueil || ""}">
              <span class="pill-pays">${dossier.pays_accueil || "Pays ?"}</span>
            </span>
          </div>
          <hr class="card-divider">

          <a class="card-sub card-dossier-link"
             href="https://demarche.numerique.gouv.fr/procedures/128447/a-suivre/dossiers/${dossier.dossier_number}"
             target="_blank" rel="noopener noreferrer">Dossier ${dossier.dossier_number}</a>

          ${activite ? `<p class="card-dates">${calendarIcon}${activite}</p>` : ""}
          ${trajet ? `<p class="card-dates card-dates--soft">${calendarIcon}${trajet}</p>` : ""}

          <div class="card-checks">
            <span class="check-item">${dossier.envoye_pedagogique ? iconSent : iconNotSent} Kit pédagogique et attestation</span>
            <span class="check-item">${dossier.envoye_financier ? iconSent : iconNotSent} Contrat financier</span>
          </div>
        </div>
        ${downloadLink}
        <div class="card-status-bar ${statusClass}"></div>
        <p class="card-etablissement">${etabIcon}${dossier.etablissement}</p>
        <label class="card-select">
          <input type="checkbox" data-dossier="${dossier.dossier_number}" ${checked}
                 aria-label="Sélectionner le dossier ${dossier.dossier_number}">
        </label>
      </article>
    `;
  }

  function render() {
    const visible = allDossiers.filter(matches);
    el.countVisible.textContent = visible.length;
    el.countTotal.textContent = allDossiers.length;

    el.cards.innerHTML = visible.length
      ? visible.map(cardTemplate).join("")
      : '<p class="empty-state">Aucun dossier ne correspond à ces filtres.</p>';

    el.cards.querySelectorAll('input[type="checkbox"]').forEach((box) => {
      box.addEventListener("change", () => {
        const id = box.dataset.dossier;
        if (box.checked) selected.add(id);
        else selected.delete(id);
        updateSelectionUI();
      });
    });

    updateSelectionUI();
  }

  function updateSelectionUI() {
    el.selCount.textContent = `(${selected.size})`;
    // Boutons grisés si le service nécessaire est en échec
    el.btnGenerate.disabled = selected.size === 0 || !sante.grist;
    el.btnSend.disabled = selected.size === 0 || !sante.grist || !sante.dn;
    el.btnSyncDn.disabled = !sante.dn || !sante.grist;

    const visibleIds = allDossiers
      .filter(matches)
      .map((d) => String(d.dossier_number));
    const selectedVisible = visibleIds.filter((id) => selected.has(id));
    el.toggleSelectAll.checked =
      visibleIds.length > 0 && selectedVisible.length === visibleIds.length;
    el.toggleSelectAll.indeterminate =
      selectedVisible.length > 0 && selectedVisible.length < visibleIds.length;
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
    if (vue === "dashboard") return loadDashboard();
    const vueChargee = vue;
    const api = VUES[vue].api;
    const url = refresh ? `${api}?refresh=1` : api;
    el.btnRefresh.disabled = true;
    const previousLabel = el.btnRefresh.textContent;
    if (refresh) el.btnRefresh.textContent = "Rafraîchissement…";

    const res = await fetch(url);
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      el.cards.innerHTML = `<p class="empty-state">Erreur de chargement des dossiers.${err.error ? `<br>${err.error}` : ""}</p>`;
      el.btnRefresh.disabled = false;
      el.btnRefresh.textContent = previousLabel;
      return;
    }
    const data = await res.json();
    if (vueChargee !== vue) return; // la page a changé pendant le chargement
    allDossiers = data.dossiers;
    el.filterEtab.innerHTML =
      '<option value="">Tous les établissements</option>';
    populateEtablissements(data.etablissements);
    render();
    el.btnRefresh.disabled = false;
    el.btnRefresh.textContent = previousLabel;
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
      el.btnSyncDn.disabled = !sante.dn || !sante.grist;
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
  wireSegmented('[data-filter="kit"]', (value) => (filterKit = value));
  wireSegmented('[data-filter="document"]', (value) =>
    setDocument(VUES[vue].documents[value]),
  );
  wireSegmented(
    '[data-filter="financier"]',
    (value) => (filterFinancier = value),
  );

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
  };

  function kpi(cle, libelle, valeur, detail, teinte) {
    return `<div class="dash-card dash-kpi">
        <div class="dash-kpi-icone dash-kpi-icone--${teinte}">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${ICONES_KPI[cle]}</svg>
        </div>
        <div><div class="dash-kpi-libelle">${libelle}</div><div class="dash-kpi-valeur">${nf(valeur)}</div><div class="dash-kpi-detail">${detail}</div></div>
      </div>`;
  }

  // Donut SVG : segments [{libelle, valeur, couleur}] séparés de 2 px
  function donut(segments, centre, sousCentre, aria) {
    const total = segments.reduce((t, s) => t + s.valeur, 0) || 1;
    const r = 54;
    const c = 2 * Math.PI * r;
    let debut = 0;
    const arcs = segments.map((s) => {
      const longueur = (s.valeur / total) * c;
      const arc = `<circle class="dash-seg" cx="64" cy="64" r="${r}" stroke="${s.couleur}" stroke-dasharray="${Math.max(0, longueur - 2).toFixed(2)} ${c.toFixed(2)}" stroke-dashoffset="${(-debut).toFixed(2)}"><title>${s.libelle} : ${nf(s.valeur)} (${pct(s.valeur, total)} %)</title></circle>`;
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
    document.getElementById("dash-exemple").hidden = !d.exemple;
    const typeChoisi = dash.type.options[dash.type.selectedIndex];
    const filtres = [
      el.filterEtab.value || "tous établissements",
      dash.projet.value || "tous projets",
      dash.annee.value || "toutes années",
      dash.type.value ? typeChoisi.textContent.toLowerCase() : "tous types",
    ];
    document.getElementById("dash-sous-titre").textContent = `Mobilités Erasmus+ : ${filtres.join(", ")}`;

    document.getElementById("dash-kpis").innerHTML =
      kpi("mobilites", "Mobilités", t.mobilites, "tous types confondus", "violet") +
      kpi("apprenants", "Apprenants", t.apprenants, "mobilités individuelles", "violet") +
      kpi("personnel", "Personnel", t.personnel, "mobilités du personnel", "bleu") +
      kpi("groupes", "Groupes", t.groupes, `${nf(t.participants_groupes)} participants`, "orange");

    // Barres empilées par type (violet / orange / bleu), info-bulle par segment
    const max = Math.max(1, ...d.par_etablissement.map((e) => e.mobilites));
    const typesVisibles = TYPES_DASH.filter(([cle]) => !dash.type.value || dash.type.value === cle);
    document.getElementById("dash-etabs-legende").innerHTML = typesVisibles
      .map(([cle, lib]) => `<li><span class="dash-puce" style="background:${COULEURS_TYPES[cle]}"></span>${lib}</li>`)
      .join("");
    document.getElementById("dash-etabs").innerHTML = d.par_etablissement.length
      ? d.par_etablissement.map((e) => {
          const segments = typesVisibles
            .filter(([cle]) => e[cle] > 0)
            .map(([cle, lib]) => `<span class="dash-barre-seg" style="flex:${e[cle]} 1 0;background:${COULEURS_TYPES[cle]}" title="${e.nom} : ${lib} ${nf(e[cle])}"></span>`)
            .join("");
          const detail = typesVisibles.map(([cle, lib]) => `${lib} ${nf(e[cle])}`).join(", ");
          return `
        <div class="dash-barre">
          <span class="dash-barre-nom" title="${e.nom}">${e.nom}</span>
          <div class="dash-barre-piste"><div class="dash-barre-val" style="width:${(e.mobilites / max) * 100}%">${segments}</div></div>
          <span class="dash-barre-nb" title="${detail}">${nf(e.mobilites)}</span>
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
    document.getElementById("dash-donut-statut").innerHTML = donut(
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
      ligne("Montant versé", sub.versee, pct(sub.versee, sub.accordee), "#1e4fd8") +
      ligne("Reste à engager", Math.max(0, sub.accordee - sub.engagee)) +
      `<h3 class="dash-sous-titre">Autres montants</h3>` +
      ligneDetail("Montant PAMO", sub.pamo, "inclusion des participants avec moins d'opportunités") +
      ligneDetail("Soutien organisationnel", sub.soutien_organisationnel, "frais de gestion de la mobilité");
  }

  async function loadDashboard() {
    const params = new URLSearchParams({
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
    // Le sélecteur garde son choix (péda / financier) d'une page à l'autre
    const actif = document.querySelector('[data-filter="document"].is-active');
    setDocument(VUES[vue].documents[(actif && actif.dataset.value) || "pedagogique"]);
    document.getElementById("doc-option-pedagogique").textContent =
      VUES[vue].libellePedagogique;
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
    el.search.value = "";
    el.filterEtab.value = "";
    allDossiers = [];
    if (vue === "dashboard") {
      loadDashboard();
      return;
    }
    el.cards.innerHTML = '<p class="empty-state">Chargement des dossiers…</p>';
    loadDossiers(false);
  }
  window.addEventListener("hashchange", setVue);

  setVue();
  verifierSante(false);
})();
