/**
 * MuniMood — Tablero de Comando
 */

let globalChart = null;

async function loadDashboard() {
  try {
    const data = await Api.getDashboard();
    renderKPIs(data.kpis);
    renderGlobalChart(data.kpis);
    renderSemaphore(data.semaphore, data.traffic_light_config);

    document.getElementById("lastUpdated").textContent =
      "Última actualización: " + fmtDatetime(new Date().toISOString());
  } catch (err) {
    showToast("Error al cargar el tablero: " + err.message, "danger");
  }
}

function renderKPIs(kpis) {
  document.getElementById("kpiFuentes").textContent  = kpis.total_sources.toLocaleString("es-AR");
  document.getElementById("kpiPosts").textContent    = kpis.total_posts.toLocaleString("es-AR");
  document.getElementById("kpiComments").textContent = kpis.total_comments.toLocaleString("es-AR");
  document.getElementById("kpiPositive").textContent = kpis.positive.toLocaleString("es-AR");
  document.getElementById("kpiNegative").textContent = kpis.negative.toLocaleString("es-AR");
  document.getElementById("kpiNeutral").textContent  = kpis.neutral.toLocaleString("es-AR");
  document.getElementById("kpiPosPct").textContent   = kpis.pos_pct + "%";
  document.getElementById("kpiNegPct").textContent   = kpis.neg_pct + "%";
}

function renderGlobalChart(kpis) {
  const ctx = document.getElementById("chartGlobal").getContext("2d");
  if (globalChart) globalChart.destroy();

  const total = kpis.positive + kpis.negative + kpis.neutral;
  if (total === 0) {
    document.getElementById("chartGlobal").parentElement.innerHTML =
      '<div class="text-center text-muted py-5"><i class="bi bi-bar-chart-line fs-2 d-block mb-2"></i>Sin datos aún</div>';
    return;
  }

  globalChart = new Chart(ctx, {
    type: "doughnut",
    data: {
      labels: ["Positivos", "Negativos", "Neutrales"],
      datasets: [{
        data: [kpis.positive, kpis.negative, kpis.neutral],
        backgroundColor: ["#16a34a", "#dc2626", "#94a3b8"],
        borderWidth: 2,
        borderColor: "#fff",
      }],
    },
    options: {
      responsive: true,
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: (ctx) => {
              const v   = ctx.parsed;
              const pct = total ? ((v / total) * 100).toFixed(1) : 0;
              return ` ${ctx.label}: ${v.toLocaleString("es-AR")} (${pct}%)`;
            },
          },
        },
      },
      cutout: "65%",
    },
  });

  // Leyenda manual
  const legend = document.getElementById("chartLegend");
  const items = [
    { color: "#16a34a", label: "Positivos", val: kpis.positive, pct: kpis.pos_pct },
    { color: "#dc2626", label: "Negativos", val: kpis.negative, pct: kpis.neg_pct },
    { color: "#94a3b8", label: "Neutrales", val: kpis.neutral,
      pct: total ? (100 - kpis.pos_pct - kpis.neg_pct).toFixed(1) : 0 },
  ];
  legend.innerHTML = items.map(i => `
    <div class="d-flex align-items-center justify-content-between mb-1">
      <div class="d-flex align-items-center gap-2">
        <span style="width:12px;height:12px;border-radius:50%;background:${i.color};display:inline-block"></span>
        <span class="small">${i.label}</span>
      </div>
      <span class="small fw-semibold">${i.val.toLocaleString("es-AR")} (${i.pct}%)</span>
    </div>
  `).join("");
}

function renderSemaphore(items, tlConfig) {
  const container = document.getElementById("semaphoreContainer");
  const scaleBadge = document.getElementById("semaphoreScaleBadge");

  scaleBadge.textContent =
    `🟢 ≥${tlConfig.green_min}%  🟡 ${tlConfig.yellow_min}–${tlConfig.yellow_max}%  🔴 ≤${tlConfig.red_max}%`;

  if (!items || items.length === 0) {
    container.innerHTML =
      '<div class="text-center py-5 text-muted"><i class="bi bi-inbox fs-2 d-block mb-2"></i>No hay ejes activos.</div>';
    return;
  }

  container.innerHTML = items.map(item => {
    const lightClass = `light-${item.color}`;
    const cardClass  = `color-${item.color}`;
    const posW = item.total ? Math.round(item.pos_pct) : 0;
    const negW = item.total ? Math.round(item.neg_pct) : 0;

    return `
      <div class="mm-semaphore-item ${cardClass}" onclick="goToTopic(${item.topic_id}, '${encodeURIComponent(item.topic_name)}')">
        <div class="d-flex align-items-center gap-2 mb-2">
          <span class="mm-semaphore-light ${lightClass}"></span>
          <i class="bi ${item.icon} ms-1"></i>
          <span class="mm-semaphore-name">${item.topic_name}</span>
        </div>
        <div class="mm-semaphore-stats mb-2">
          <span class="text-success fw-semibold">${item.positive.toLocaleString("es-AR")} pos (${item.pos_pct}%)</span>
          &nbsp;·&nbsp;
          <span class="text-danger fw-semibold">${item.negative.toLocaleString("es-AR")} neg (${item.neg_pct}%)</span>
        </div>
        <div class="d-flex gap-1">
          <div class="mm-progress-bar-pos" style="width:${posW}%;flex-grow:${posW || 1}"></div>
          <div class="mm-progress-bar-neg" style="width:${negW}%;flex-grow:${negW || 1}"></div>
        </div>
        <div class="text-end mt-1 small text-muted">${item.total.toLocaleString("es-AR")} comentarios</div>
      </div>
    `;
  }).join("");
}

function goToTopic(topicId, topicName) {
  window.location.href = `/frontend/topic-detail.html?topic=${topicId}&name=${topicName}`;
}

// ---- Init ----
document.getElementById("btnRefreshData")?.addEventListener("click", loadDashboard);
loadDashboard();
