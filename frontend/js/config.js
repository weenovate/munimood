/**
 * MuniMood — Página de Configuración
 */

const modalTopic  = () => bootstrap.Modal.getOrCreateInstance(document.getElementById("modalTopic"));
const modalUser   = () => bootstrap.Modal.getOrCreateInstance(document.getElementById("modalUser"));
const modalDel    = () => bootstrap.Modal.getOrCreateInstance(document.getElementById("modalDelete"));

let pendingDelete = null;  // { type: "topic"|"user", id }

// ================================================================
// SEMÁFORO
// ================================================================

async function loadTrafficLight() {
  try {
    const tl = await Api.getTrafficLight();
    document.getElementById("tlGreenMin").value  = tl.green_min_pct;
    document.getElementById("tlYellowMin").value = tl.yellow_min_pct;
    document.getElementById("tlYellowMax").value = tl.yellow_max_pct;
    document.getElementById("tlRedMax").value    = tl.red_max_pct;
  } catch (err) {
    showAlert("alertTrafficLight", "Error al cargar configuración: " + err.message, "danger");
  }
}

document.getElementById("formTrafficLight")?.addEventListener("submit", async (e) => {
  e.preventDefault();
  const payload = {
    green_min_pct : parseFloat(document.getElementById("tlGreenMin").value),
    yellow_min_pct: parseFloat(document.getElementById("tlYellowMin").value),
    yellow_max_pct: parseFloat(document.getElementById("tlYellowMax").value),
    red_max_pct   : parseFloat(document.getElementById("tlRedMax").value),
  };
  setLoading("formTrafficLight", "btnTLSpinner", false);
  document.getElementById("btnTLSpinner").classList.remove("d-none");
  try {
    await Api.updateTrafficLight(payload);
    showAlert("alertTrafficLight", "Escala del semáforo guardada.", "success");
  } catch (err) {
    showAlert("alertTrafficLight", err.message, "danger");
  } finally {
    document.getElementById("btnTLSpinner").classList.add("d-none");
  }
});

// ================================================================
// MOTOR DE IA
// ================================================================

async function loadAIEngine() {
  try {
    const ai = await Api.getAIEngine();
    document.getElementById("aiEngine").value = ai.engine;
    document.getElementById("aiModel").value  = ai.model || "";
    toggleAIKeyGroup(ai.engine);
    if (ai.has_api_key) {
      document.getElementById("aiKeyStatus").innerHTML =
        '<span class="text-success"><i class="bi bi-check-circle me-1"></i>API Key configurada</span>';
    }
  } catch (err) {
    showAlert("alertAI", "Error al cargar motor: " + err.message, "danger");
  }
}

function toggleAIKeyGroup(engine) {
  const show = !["local", "pysentimiento"].includes(engine);
  document.getElementById("aiKeyGroup").classList.toggle("d-none", !show);

  const hints = {
    openai  : "Obtenela en platform.openai.com → API Keys",
    claude  : "Obtenela en console.anthropic.com",
    gemini  : "Obtenela en aistudio.google.com",
  };
  document.getElementById("aiKeyHint").textContent = hints[engine] || "";
}

document.getElementById("aiEngine")?.addEventListener("change", function () {
  toggleAIKeyGroup(this.value);
});

document.getElementById("btnToggleApiKey")?.addEventListener("click", () => {
  const inp = document.getElementById("aiApiKey");
  const ico = document.querySelector("#btnToggleApiKey i");
  inp.type = inp.type === "password" ? "text" : "password";
  ico.className = inp.type === "password" ? "bi bi-eye" : "bi bi-eye-slash";
});

document.getElementById("formAI")?.addEventListener("submit", async (e) => {
  e.preventDefault();
  const engine = document.getElementById("aiEngine").value;
  const apiKey = document.getElementById("aiApiKey").value.trim();
  const model  = document.getElementById("aiModel").value.trim();
  const needsKey = !["local", "pysentimiento"].includes(engine);

  if (needsKey && !apiKey) {
    showAlert("alertAI", "Ingresá la API Key para el motor seleccionado.", "warning");
    return;
  }

  document.getElementById("btnAISpinner").classList.remove("d-none");
  try {
    await Api.updateAIEngine({ engine, api_key: apiKey, model });
    showAlert("alertAI", "Motor de IA actualizado correctamente.", "success");
    if (apiKey) {
      document.getElementById("aiKeyStatus").innerHTML =
        '<span class="text-success"><i class="bi bi-check-circle me-1"></i>API Key guardada</span>';
    }
  } catch (err) {
    showAlert("alertAI", err.message, "danger");
  } finally {
    document.getElementById("btnAISpinner").classList.add("d-none");
  }
});

// ================================================================
// EJES TEMÁTICOS
// ================================================================

let topicsCache = [];

async function loadTopics() {
  const wrap = document.getElementById("topicsTableWrap");
  try {
    topicsCache = await Api.getTopics();
    if (!topicsCache.length) {
      wrap.innerHTML = '<div class="text-center py-4 text-muted small">No hay ejes definidos.</div>';
      return;
    }
    wrap.innerHTML = `
      <div class="table-responsive">
        <table class="mm-table">
          <thead>
            <tr>
              <th>Ícono</th><th>Nombre</th><th class="text-center">Orden</th>
              <th class="text-center">Estado</th><th class="text-end">Acciones</th>
            </tr>
          </thead>
          <tbody>
            ${topicsCache.map(t => `
              <tr>
                <td><i class="bi ${t.icon} fs-5"></i></td>
                <td class="fw-semibold">${escHtml(t.name)}</td>
                <td class="text-center">${t.display_order}</td>
                <td class="text-center">
                  ${t.is_active
                    ? '<span class="badge bg-success-subtle text-success">Activo</span>'
                    : '<span class="badge bg-secondary-subtle text-secondary">Inactivo</span>'}
                </td>
                <td class="text-end">
                  <button class="btn btn-outline-secondary btn-sm me-1" onclick="openEditTopic(${t.id})">
                    <i class="bi bi-pencil"></i>
                  </button>
                  <button class="btn btn-outline-danger btn-sm" onclick="confirmDelete('topic',${t.id},'${escHtml(t.name)}')">
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

document.getElementById("btnNewTopic")?.addEventListener("click", () => {
  document.getElementById("modalTopicLabel").textContent = "Nuevo Eje";
  document.getElementById("formTopic").reset();
  document.getElementById("topicId").value = "";
  document.getElementById("topicActive").checked = true;
  document.getElementById("topicIcon").value = "bi-circle";
  document.getElementById("iconPreview").innerHTML = '<i class="bi bi-circle"></i>';
  hideAlert("alertModalTopic");
  modalTopic().show();
});

function openEditTopic(id) {
  const t = topicsCache.find(x => x.id === id);
  if (!t) return;
  document.getElementById("modalTopicLabel").textContent = "Editar Eje";
  document.getElementById("topicId").value       = t.id;
  document.getElementById("topicName").value     = t.name;
  document.getElementById("topicIcon").value     = t.icon;
  document.getElementById("topicOrder").value    = t.display_order;
  document.getElementById("topicActive").checked = t.is_active;
  document.getElementById("iconPreview").innerHTML = `<i class="bi ${t.icon}"></i>`;
  hideAlert("alertModalTopic");
  modalTopic().show();
}

document.getElementById("topicIcon")?.addEventListener("input", function () {
  document.getElementById("iconPreview").innerHTML = `<i class="bi ${this.value}"></i>`;
});

document.getElementById("btnSaveTopic")?.addEventListener("click", async () => {
  const id      = document.getElementById("topicId").value;
  const payload = {
    name         : document.getElementById("topicName").value.trim(),
    icon         : document.getElementById("topicIcon").value.trim() || "bi-circle",
    display_order: parseInt(document.getElementById("topicOrder").value) || 0,
    is_active    : document.getElementById("topicActive").checked,
  };
  if (!payload.name) {
    showAlert("alertModalTopic", "El nombre es obligatorio.", "warning");
    return;
  }
  document.getElementById("btnSaveTopicSpinner").classList.remove("d-none");
  try {
    if (id) {
      await Api.updateTopic(parseInt(id), payload);
      showToast("Eje actualizado.", "success");
    } else {
      await Api.createTopic(payload);
      showToast("Eje creado.", "success");
    }
    modalTopic().hide();
    loadTopics();
  } catch (err) {
    showAlert("alertModalTopic", err.message, "danger");
    document.getElementById("btnSaveTopicSpinner").classList.add("d-none");
  }
});

// ================================================================
// USUARIOS
// ================================================================

const currentUser = getUser();
let usersCache = [];

async function loadUsers() {
  const wrap = document.getElementById("usersTableWrap");
  const section = document.getElementById("usersSection");

  if (!currentUser?.is_admin) {
    section.style.display = "none";
    return;
  }

  try {
    usersCache = await Api.getUsers();
    wrap.innerHTML = `
      <div class="table-responsive">
        <table class="mm-table">
          <thead>
            <tr>
              <th>Usuario</th><th>Email</th><th class="text-center">Admin</th>
              <th class="text-center">Estado</th><th class="text-end">Acciones</th>
            </tr>
          </thead>
          <tbody>
            ${usersCache.map(u => `
              <tr>
                <td>
                  <div class="fw-semibold">${escHtml(u.username)}</div>
                  <div class="small text-muted">${escHtml(u.full_name || "")}</div>
                </td>
                <td class="small">${escHtml(u.email)}</td>
                <td class="text-center">
                  ${u.is_admin ? '<i class="bi bi-shield-check text-primary"></i>' : ''}
                </td>
                <td class="text-center">
                  ${u.is_active
                    ? '<span class="badge bg-success-subtle text-success">Activo</span>'
                    : '<span class="badge bg-secondary-subtle text-secondary">Inactivo</span>'}
                </td>
                <td class="text-end">
                  <button class="btn btn-outline-secondary btn-sm me-1" onclick="openEditUser(${u.id})">
                    <i class="bi bi-pencil"></i>
                  </button>
                  <button class="btn btn-outline-danger btn-sm" onclick="confirmDelete('user',${u.id},'${escHtml(u.username)}')"
                    ${u.id === currentUser?.id ? "disabled title='No podés eliminarte'" : ""}>
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

document.getElementById("btnNewUser")?.addEventListener("click", () => {
  document.getElementById("modalUserLabel").textContent = "Nuevo Usuario";
  document.getElementById("formUser").reset();
  document.getElementById("userId").value = "";
  document.getElementById("userPassGroup").style.display = "block";
  document.getElementById("userActiveGroup").style.display = "none";
  document.getElementById("userPassword").required = true;
  hideAlert("alertModalUser");
  modalUser().show();
});

function openEditUser(id) {
  const u = usersCache.find(x => x.id === id);
  if (!u) return;
  document.getElementById("modalUserLabel").textContent = "Editar Usuario";
  document.getElementById("userId").value        = u.id;
  document.getElementById("userUsername").value  = u.username;
  document.getElementById("userEmail").value     = u.email;
  document.getElementById("userFullName").value  = u.full_name || "";
  document.getElementById("userIsAdmin").checked = u.is_admin;
  document.getElementById("userIsActive").checked= u.is_active;
  document.getElementById("userPassGroup").style.display   = "none";
  document.getElementById("userActiveGroup").style.display = "block";
  document.getElementById("userPassword").required = false;
  hideAlert("alertModalUser");
  modalUser().show();
}

document.getElementById("btnSaveUser")?.addEventListener("click", async () => {
  const id = document.getElementById("userId").value;
  document.getElementById("btnSaveUserSpinner").classList.remove("d-none");

  try {
    if (id) {
      const payload = {
        email    : document.getElementById("userEmail").value.trim(),
        full_name: document.getElementById("userFullName").value.trim(),
        is_active: document.getElementById("userIsActive").checked,
        is_admin : document.getElementById("userIsAdmin").checked,
      };
      await Api.updateUser(parseInt(id), payload);
      showToast("Usuario actualizado.", "success");
    } else {
      const pass = document.getElementById("userPassword").value;
      const payload = {
        username : document.getElementById("userUsername").value.trim(),
        email    : document.getElementById("userEmail").value.trim(),
        full_name: document.getElementById("userFullName").value.trim(),
        password : pass,
        is_admin : document.getElementById("userIsAdmin").checked,
      };
      if (!payload.username || !payload.email || !payload.password) {
        showAlert("alertModalUser", "Completá usuario, email y contraseña.", "warning");
        document.getElementById("btnSaveUserSpinner").classList.add("d-none");
        return;
      }
      await Api.createUser(payload);
      showToast("Usuario creado.", "success");
    }
    modalUser().hide();
    loadUsers();
  } catch (err) {
    showAlert("alertModalUser", err.message, "danger");
    document.getElementById("btnSaveUserSpinner").classList.add("d-none");
  }
});

// ================================================================
// ELIMINAR GENÉRICO
// ================================================================

function confirmDelete(type, id, name) {
  pendingDelete = { type, id };
  const titles = { topic: "Eliminar Eje", user: "Eliminar Usuario" };
  document.getElementById("modalDeleteTitle").textContent = titles[type] || "Eliminar";
  document.getElementById("modalDeleteMsg").innerHTML =
    `¿Estás seguro de que querés eliminar <strong>${escHtml(name)}</strong>?`;
  modalDel().show();
}

document.getElementById("btnConfirmDelete")?.addEventListener("click", async () => {
  if (!pendingDelete) return;
  document.getElementById("btnDeleteSpinner").classList.remove("d-none");
  try {
    if (pendingDelete.type === "topic") {
      await Api.deleteTopic(pendingDelete.id);
      showToast("Eje eliminado.", "success");
      loadTopics();
    } else if (pendingDelete.type === "user") {
      await Api.deleteUser(pendingDelete.id);
      showToast("Usuario eliminado.", "success");
      loadUsers();
    }
    modalDel().hide();
  } catch (err) {
    showToast("Error: " + err.message, "danger");
    document.getElementById("btnDeleteSpinner").classList.add("d-none");
  }
});

// ================================================================
// Utilidades
// ================================================================

function showAlert(elId, msg, type = "danger") {
  const el = document.getElementById(elId);
  if (!el) return;
  el.className = `alert alert-${type}`;
  el.textContent = msg;
  el.classList.remove("d-none");
}

function hideAlert(elId) {
  const el = document.getElementById(elId);
  if (el) el.classList.add("d-none");
}

function escHtml(str) {
  if (!str) return "";
  return String(str).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;");
}

// ---- Init ----
loadTrafficLight();
loadAIEngine();
loadTopics();
loadUsers();
