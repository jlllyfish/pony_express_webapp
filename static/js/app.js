(function () {
  "use strict";

  let allDossiers = [];
  const selected = new Set();
  let filterKit = "tous";
  let filterFinancier = "tous";

  const el = {
    cards: document.getElementById("cards"),
    filterEtab: document.getElementById("filter-etablissement"),
    search: document.getElementById("search-nom"),
    countVisible: document.getElementById("count-visible"),
    countTotal: document.getElementById("count-total"),
    btnGenerate: document.getElementById("btn-generate"),
    selCount: document.getElementById("sel-count"),
    btnRefresh: document.getElementById("btn-refresh"),
    btnSend: document.getElementById("btn-send"),
    toggleSelectAll: document.getElementById("toggle-select-all"),
    toast: document.getElementById("toast"),
    toastLoader: document.getElementById("toast-loader"),
    toastLoaderFrozen: document.getElementById("toast-loader-frozen"),
    toastTitle: document.getElementById("toast-title"),
    toastProgress: document.getElementById("toast-progress"),
    toastClose: document.getElementById("toast-close"),
  };

  let toastTimeout = null;

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
    // recherche "starts with" sur nom ou prénom
    return (
      dossier.nom.toLowerCase().startsWith(query) ||
      dossier.prenom.toLowerCase().startsWith(query)
    );
  }

  function cardTemplate(dossier) {
    const statusClass =
      dossier.statut === "envoye"
        ? "is-envoye"
        : dossier.statut === "genere"
          ? "is-genere"
          : "";
    const checked = selected.has(String(dossier.dossier_number))
      ? "checked"
      : "";
    const downloadLink =
      dossier.statut !== "non_genere"
        ? `<a class="card-download" href="/api/kits/${dossier.dossier_number}/download">Télécharger le PDF</a>`
        : "";

    const activite =
      dossier.date_debut_activite || dossier.date_fin_activite
        ? `${dossier.date_debut_activite || "?"} → ${dossier.date_fin_activite || "?"}`
        : "";
    const trajet =
      dossier.date_trajet_aller || dossier.date_trajet_retour
        ? `Trajet ${dossier.date_trajet_aller || "?"} → ${dossier.date_trajet_retour || "?"}`
        : "";

    const calendarIcon = `<svg width="14" height="14" class="date-icon" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.6">
        <rect x="2.5" y="4" width="15" height="13" rx="2"/><path d="M6.5 2v4M13.5 2v4M2.5 8h15"/>
      </svg>`;
    const buildingIcon = `<svg width="14" height="14" class="etab-icon" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.6">
        <path d="M4 17V5.5L10 3l6 2.5V17"/><path d="M4 17h12M7.5 8h1M11.5 8h1M7.5 11.5h1M11.5 11.5h1M8.5 17v-3h3v3"/>
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
        <div class="card-avatar">${initiales(dossier)}</div>
        <div class="card-body">
          <div class="card-header-row">
            <h3 class="card-title">${dossier.nom_complet || "Nom inconnu"}</h3>
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
            <span class="check-item">${dossier.envoye_pedagogique ? iconSent : iconNotSent} Kit pédagogique</span>
            <span class="check-item">${dossier.envoye_financier ? iconSent : iconNotSent} Contrat financier</span>
          </div>
        </div>
        ${downloadLink}
        <div class="card-status-bar ${statusClass}"></div>
        <p class="card-etablissement">${buildingIcon}${dossier.etablissement}</p>
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
    el.btnGenerate.disabled = selected.size === 0;
    el.btnSend.disabled = selected.size === 0;

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
    const url = refresh ? "/api/dossiers?refresh=1" : "/api/dossiers";
    el.btnRefresh.disabled = true;
    const previousLabel = el.btnRefresh.textContent;
    if (refresh) el.btnRefresh.textContent = "Rafraîchissement…";

    const res = await fetch(url);
    if (!res.ok) {
      el.cards.innerHTML =
        '<p class="empty-state">Erreur de chargement des dossiers.</p>';
      el.btnRefresh.disabled = false;
      el.btnRefresh.textContent = previousLabel;
      return;
    }
    const data = await res.json();
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

    showToastProgress("Génération en cours…", 0, ids.length);
    let successCount = 0;
    const failed = {};

    for (let i = 0; i < ids.length; i++) {
      const id = ids[i];
      try {
        const res = await fetch("/api/kits/generate", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ dossier_numbers: [id] }),
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.error || "erreur inconnue");
        const dossier = allDossiers.find(
          (d) => String(d.dossier_number) === id,
        );
        if (dossier) dossier.statut = "genere";
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
      const detail = Object.entries(failed)
        .map(([n, msg]) => `#${n} : ${msg}`)
        .join("\n");
      alert(`Échecs de génération :\n${detail}`);
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

    showToastProgress("Envoi en cours…", 0, ids.length);
    let successCount = 0;
    const failed = {};

    for (let i = 0; i < ids.length; i++) {
      const id = ids[i];
      try {
        const res = await fetch("/api/kits/send", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ dossier_numbers: [id] }),
        });
        const data = await res.json();
        if (data.failed && data.failed[id]) throw new Error(data.failed[id]);
        if (!res.ok && res.status !== 207)
          throw new Error(data.error || "erreur inconnue");
        const dossier = allDossiers.find(
          (d) => String(d.dossier_number) === id,
        );
        if (dossier) {
          dossier.envoye_pedagogique = true;
          dossier.statut = "envoye";
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
      const detail = Object.entries(failed)
        .map(([n, msg]) => `#${n} : ${msg}`)
        .join("\n");
      alert(`Échecs d'envoi :\n${detail}`);
    }
    updateSelectionUI();
  }

  el.filterEtab.addEventListener("change", render);
  el.search.addEventListener("input", render);
  el.btnGenerate.addEventListener("click", generateSelection);
  el.btnRefresh.addEventListener("click", () => loadDossiers(true));
  el.btnSend.addEventListener("click", sendSelection);
  el.toastClose.addEventListener("click", hideToast);
  el.toggleSelectAll.addEventListener("change", () => {
    if (el.toggleSelectAll.checked) selectAllVisible();
    else selectNone();
  });
  wireSegmented('[data-filter="kit"]', (value) => (filterKit = value));
  wireSegmented(
    '[data-filter="financier"]',
    (value) => (filterFinancier = value),
  );

  loadDossiers(true);
})();
