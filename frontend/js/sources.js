/**
 * MuniMood — Fuentes de Información (CRUD)
 */

let sourcesToDelete = null;
const modalSource = () => bootstrap.Modal.getOrCreateInstance(document.getElementById("modalSource"));
const modalDelete = () => bootstrap.Modal.getOrCreateInstance(document.getElementById("modalDeleteSource"));

async function loadSources() {
  const wrap = document.getElementById("sourcesTableWrap");
  wrap.innerHTML = '<div class="text-center py-5 text-muted"><div class="spinner-border spinner-border-sm me-2"></div>Cargando...</div>';

  try {
    const sources = await Api.getSources();
    if (!sources.length) {
      wrap.innerHTML = `
        <div class="text-center py-5 text-muted">
          <i class="bi bi-rss fs-2 d-block mb-2"></i>
          <p>No hay fuentes registradas.</p>
          <button class="btn btn-primary btn-sm" onclick="openNewSource()">
            <i class="bi bi-plus-lg me-1"></i>Agregar primera fuente
          </button>
        </div>`;
      return;
    }

    wrap.innerHTML = `
      <div class="table-responsive">
        <table class="mm-table">
          <thead>
            <tr>
              <th>Nombre</th>
              <th>Red Social</th>
              <th>Inicio Análisis</th>
              <th>Refresco</th>
              <th>Último Scrap.</th>
              <th>Estado</th>
              <th class="text-end">Acciones</th>
            </tr>
          </thead>
          <tbody>
            ${sources.map(s => `
              <tr>
                <td>
                  <div class="fw-semibold">${escHtml(s.name)}</div>
                  <div class="small text-muted text-truncate" style="max-width:240px">
                    <a href="${escHtml(s.url)}" target="_blank" class="text-decoration-none">
                      <i class="bi bi-link-45deg"></i> ${escHtml(s.profile_handle || s.url)}
                    </a>
                  </div>
                </td>
                <td>${snBadge(s.social_network)}</td>
                <td class="small">${s.start_date}</td>
                <td class="small">${refreshLabel(s.refresh_rate, s.refresh_window)}</td>
                <td class="small text-muted">${fmtDatetime(s.last_scraped_at) || 'Nunca'}</td>
                <td>
                  ${s.is_active
                    ? '<span class="badge bg-success-subtle text-success border border-success-subtle">Activa</span>'
                    : '<span class="badge bg-secondary-subtle text-secondary border border-secondary-subtle">Inactiva</span>'}
                </td>
                <td class="text-end">
                  <button class="btn btn-outline-primary btn-sm me-1" onclick="scrapeOne(${s.id})" title="Scrapear ahora">
                    <i class="bi bi-cloud-download"></i>
                  </button>
                  <button class="btn btn-outline-secondary btn-sm me-1" onclick="openEditSource(${s.id})" title="Editar">
                    <i class="bi bi-pencil"></i>
                  </button>
                  <button class="btn btn-outline-danger btn-sm" onclick="confirmDeleteSource(${s.id}, '${escHtml(s.name)}')" title="Eliminar">
                    <i class="bi bi-trash"></i>
                  </button>
                </td>
              </tr>
            `).join("")}
          </tbody>
        </table>
      </div>`;
  } catch (err) {
    wrap.innerHTML = `<div class="alert alert-danger m-3">${err.message}</div>`;
  }
}

function refreshLabel(rate, window) {
  const rateMap = { never: "Nunca", "30min": "30 min", "1h": "1 hora", "4h": "4 hs", "12h": "12 hs", "24h": "24 hs" };
  if (rate === "never") return "Nunca";
  const wMap = { "24h": "24h", "48h": "48h", "72h": "72h", "1week": "1 semana" };
  return `${rateMap[rate] || rate} / ${wMap[window] || window}`;
}

function openNewSource() {
  document.getElementById("modalSourceLabel").textContent = "Nueva Fuente";
  document.getElementById("formSource").reset();
  document.getElementById("sourceId").value = "";
  document.getElementById("sourceIsActive").checked = true;
  document.getElementById("activeToggleGroup").style.display = "none";
  document.getElementById("refreshWindowGroup").style.display = "none";
  hideAlert("alertModalSource");
  modalSource().show();
}

async function openEditSource(id) {
  try {
    const s = await Api.getSources().then(list => list.find(x => x.id === id));
    if (!s) return;
    document.getElementById("modalSourceLabel").textContent = "Editar Fuente";
    document.getElementById("sourceId").value            = s.id;
    document.getElementById("sourceName").value          = s.name;
    document.getElementById("sourceUrl").value           = s.url;
    document.getElementById("sourceSocialNetwork").value = s.social_network;
    document.getElementById("sourceStartDate").value     = s.start_date;
    document.getElementById("sourceRefreshRate").value   = s.refresh_rate;
    document.getElementById("sourceRefreshWindow").value = s.refresh_window || "24h";
    document.getElementById("sourceIsActive").checked   = s.is_active;
    document.getElementById("activeToggleGroup").style.display = "block";
    document.getElementById("refreshWindowGroup").style.display =
      s.refresh_rate !== "never" ? "block" : "none";
    hideAlert("alertModalSource");
    modalSource().show();
  } catch (err) {
    showToast("Error: " + err.message, "danger");
  }
}

document.getElementById("sourceRefreshRate")?.addEventListener("change", function () {
  document.getElementById("refreshWindowGroup").style.display =
    this.value !== "never" ? "block" : "none";
});

document.getElementById("btnNewSource")?.addEventListener("click", openNewSource);

document.getElementById("btnSaveSource")?.addEventListener("click", async () => {
  const id      = document.getElementById("sourceId").value;
  const rate    = document.getElementById("sourceRefreshRate").value;
  const payload = {
    name          : document.getElementById("sourceName").value.trim(),
    url           : document.getElementById("sourceUrl").value.trim(),
    social_network: document.getElementById("sourceSocialNetwork").value,
    start_date    : document.getElementById("sourceStartDate").value,
    refresh_rate  : rate,
    refresh_window: rate !== "never" ? document.getElementById("sourceRefreshWindow").value : null,
    is_active     : document.getElementById("sourceIsActive").checked,
  };

  if (!payload.name || !payload.url || !payload.social_network || !payload.start_date) {
    showAlert("alertModalSource", "Completá todos los campos obligatorios.", "warning");
    return;
  }

  setLoading("btnSaveSource", "btnSaveSourceSpinner", true);
  try {
    if (id) {
      await Api.updateSource(parseInt(id), payload);
      showToast("Fuente actualizada.", "success");
    } else {
      await Api.createSource(payload);
      showToast("Fuente creada.", "success");
    }
    modalSource().hide();
    loadSources();
  } catch (err) {
    showAlert("alertModalSource", err.message, "danger");
    setLoading("btnSaveSource", "btnSaveSourceSpinner", false);
  }
});

function confirmDeleteSource(id, name) {
  sourcesToDelete = id;
  document.getElementById("deleteSourceName").textContent = name;
  modalDelete().show();
}

document.getElementById("btnConfirmDeleteSource")?.addEventListener("click", async () => {
  if (!sourcesToDelete) return;
  setLoading("btnConfirmDeleteSource", "btnDeleteSpinner", true);
  try {
    await Api.deleteSource(sourcesToDelete);
    showToast("Fuente eliminada.", "success");
    modalDelete().hide();
    loadSources();
  } catch (err) {
    showToast("Error: " + err.message, "danger");
    setLoading("btnConfirmDeleteSource", "btnDeleteSpinner", false);
  }
});

async function scrapeOne(id) {
  try {
    await Api.triggerScraping(id);
    showToast("Scraping iniciado para esta fuente.", "success");
  } catch (err) {
    showToast("Error al iniciar scraping: " + err.message, "danger");
  }
}

document.getElementById("btnScrapeAll")?.addEventListener("click", async () => {
  try {
    const res = await Api.triggerScraping(null);
    showToast(res.message, "success");
  } catch (err) {
    showToast("Error: " + err.message, "danger");
  }
});

function escHtml(str) {
  if (!str) return "";
  return String(str).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;");
}

// ---- Init ----
loadSources();
