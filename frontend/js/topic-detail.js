/**
 * MuniMood — Detalle de Eje Temático
 */

const params    = new URLSearchParams(window.location.search);
const topicId   = parseInt(params.get("topic")) || 0;
const topicName = decodeURIComponent(params.get("name") || "Eje");

let currentPage   = 1;
let totalPosts    = 0;
const PER_PAGE    = 20;
let sentChart     = null;

// ---- Setup inicial ----
document.getElementById("topicTitle").textContent = topicName;
document.getElementById("bcTopic").textContent    = topicName;
document.title = `MuniMood — ${topicName}`;

async function loadPosts(page = 1) {
  currentPage = page;
  const wrap  = document.getElementById("postsTableWrap");
  wrap.innerHTML = '<div class="text-center py-5 text-muted"><div class="spinner-border spinner-border-sm me-2"></div>Cargando notas...</div>';

  try {
    const data = await Api.getPostsByTopic(topicId, page, PER_PAGE);
    totalPosts  = data.total;

    // Header
    document.getElementById("topicStats").textContent =
      `${data.total.toLocaleString("es-AR")} nota${data.total !== 1 ? "s" : ""} relevada${data.total !== 1 ? "s" : ""}`;

    if (!data.posts.length) {
      wrap.innerHTML = `
        <div class="text-center py-5 text-muted">
          <i class="bi bi-inbox fs-2 d-block mb-2"></i>
          No hay posteos para este eje todavía.
        </div>`;
      renderPagination(0, 0);
      return;
    }

    wrap.innerHTML = `
      <div class="table-responsive">
        <table class="mm-table">
          <thead>
            <tr>
              <th>Título / Nota</th>
              <th>Medio</th>
              <th>Fecha</th>
              <th class="text-center">Pos</th>
              <th class="text-center">Neg</th>
              <th class="text-end">Total</th>
            </tr>
          </thead>
          <tbody>
            ${data.posts.map(p => `
              <tr class="cursor-pointer" onclick="openPost(${p.id})">
                <td>
                  <div class="text-truncate-2 fw-semibold" style="max-width:340px">${escHtml(p.title || "Sin título")}</div>
                </td>
                <td>
                  <div class="small fw-semibold">${escHtml(p.source_name)}</div>
                  ${snBadge(p.social_network)}
                </td>
                <td class="small text-muted">${fmtDate(p.post_date)}</td>
                <td class="text-center">
                  <span class="fw-semibold text-success">${p.positive_comments}</span>
                </td>
                <td class="text-center">
                  <span class="fw-semibold text-danger">${p.negative_comments}</span>
                </td>
                <td class="text-end small text-muted">${p.total_comments}</td>
              </tr>
            `).join("")}
          </tbody>
        </table>
      </div>`;

    renderPagination(data.total, page);
  } catch (err) {
    wrap.innerHTML = `<div class="alert alert-danger m-3">${err.message}</div>`;
  }
}

function renderPagination(total, page) {
  const pag     = document.getElementById("postsPagination");
  const pages   = Math.ceil(total / PER_PAGE);

  if (pages <= 1) { pag.innerHTML = ""; return; }

  let html = `<small class="text-muted">${total} notas</small>`;
  html += `<button class="btn btn-outline-secondary btn-sm" ${page <= 1 ? "disabled" : ""} onclick="loadPosts(${page - 1})">
    <i class="bi bi-chevron-left"></i>
  </button>`;
  html += `<span class="small">${page} / ${pages}</span>`;
  html += `<button class="btn btn-outline-secondary btn-sm" ${page >= pages ? "disabled" : ""} onclick="loadPosts(${page + 1})">
    <i class="bi bi-chevron-right"></i>
  </button>`;
  pag.innerHTML = html;
}

async function openPost(postId) {
  const viewPosts  = document.getElementById("viewPosts");
  const viewDetail = document.getElementById("viewPostDetail");

  viewPosts.classList.add("d-none");
  viewDetail.classList.remove("d-none");

  // Limpiar
  document.getElementById("detailTitle").textContent   = "Cargando...";
  document.getElementById("detailSource").textContent  = "";
  document.getElementById("detailDate").textContent    = "";
  document.getElementById("detailContent").textContent = "";
  document.getElementById("negPhrasesList").innerHTML  =
    '<div class="text-center py-3 text-muted small"><div class="spinner-border spinner-border-sm me-2"></div>Analizando...</div>';

  try {
    const p = await Api.getPostDetail(postId);

    document.getElementById("detailTitle").textContent = p.title || "Sin título";
    document.getElementById("detailSource").textContent =
      (p.source?.name || "") + " · " + (p.source?.social_network || "");
    document.getElementById("detailDate").textContent  = fmtDatetime(p.post_date);
    document.getElementById("detailContent").textContent = p.content || "(Sin contenido)";

    const detailUrl = document.getElementById("detailUrl");
    if (p.post_url) {
      detailUrl.href = p.post_url;
      detailUrl.style.display = "";
    } else {
      detailUrl.style.display = "none";
    }

    document.getElementById("detailPosCnt").textContent = p.positive_comments.toLocaleString("es-AR");
    document.getElementById("detailNegCnt").textContent = p.negative_comments.toLocaleString("es-AR");
    document.getElementById("detailPosPct").textContent = `(${p.pos_pct}%)`;
    document.getElementById("detailNegPct").textContent = `(${p.neg_pct}%)`;

    // Gráfico de sentimiento
    renderPostChart(p.positive_comments, p.negative_comments, p.neutral_comments);

    // Frases negativas
    renderNegPhrases(p.negative_phrases);

  } catch (err) {
    document.getElementById("detailTitle").textContent = "Error al cargar: " + err.message;
  }
}

function renderPostChart(pos, neg, neu) {
  const ctx = document.getElementById("chartPostSentiment").getContext("2d");
  if (sentChart) sentChart.destroy();
  const total = pos + neg + neu;

  sentChart = new Chart(ctx, {
    type: "doughnut",
    data: {
      labels: ["Positivos", "Negativos", "Neutrales"],
      datasets: [{
        data: [pos, neg, neu],
        backgroundColor: ["#16a34a", "#dc2626", "#94a3b8"],
        borderWidth: 2,
        borderColor: "#fff",
      }],
    },
    options: {
      responsive: true,
      cutout: "60%",
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: (ctx) => {
              const v   = ctx.parsed;
              const pct = total ? ((v / total) * 100).toFixed(1) : 0;
              return ` ${ctx.label}: ${v} (${pct}%)`;
            },
          },
        },
      },
    },
  });
}

function renderNegPhrases(phrases) {
  const list = document.getElementById("negPhrasesList");
  if (!phrases || !phrases.length) {
    list.innerHTML = '<div class="list-group-item text-muted small text-center py-3">Sin frases destacadas</div>';
    return;
  }
  const max = phrases[0]?.count || 1;
  list.innerHTML = phrases.map((p, i) => `
    <div class="list-group-item px-3 py-2">
      <div class="d-flex justify-content-between align-items-center mb-1">
        <span class="small fw-semibold">${escHtml(p.phrase)}</span>
        <span class="badge bg-danger-subtle text-danger">${p.count}x</span>
      </div>
      <div class="progress" style="height:4px">
        <div class="progress-bar bg-danger" style="width:${Math.round(p.count/max*100)}%"></div>
      </div>
    </div>
  `).join("");
}

document.getElementById("btnBackToPosts")?.addEventListener("click", () => {
  document.getElementById("viewPostDetail").classList.add("d-none");
  document.getElementById("viewPosts").classList.remove("d-none");
});

function escHtml(str) {
  if (!str) return "";
  return String(str).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;");
}

// ---- Init ----
if (!topicId) {
  document.getElementById("postsTableWrap").innerHTML =
    '<div class="alert alert-warning m-3">No se especificó un eje. <a href="dashboard.html">Volver al tablero.</a></div>';
} else {
  loadPosts(1);
}
