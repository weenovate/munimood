/**
 * MuniMood — Manejo de autenticación y sesiones
 */

// ----------------------------------------------------------------
// Funciones de sesión
// ----------------------------------------------------------------

function saveSession(token, user) {
  localStorage.setItem("mm_token", token);
  localStorage.setItem("mm_user", JSON.stringify(user));
}

function clearSession() {
  localStorage.removeItem("mm_token");
  localStorage.removeItem("mm_user");
}

function getUser() {
  try { return JSON.parse(localStorage.getItem("mm_user")); }
  catch { return null; }
}

function isLoggedIn() {
  return !!localStorage.getItem("mm_token");
}

function requireAuth() {
  if (!isLoggedIn()) {
    window.location.href = "/frontend/index.html";
    return false;
  }
  return true;
}

// ----------------------------------------------------------------
// Navbar: mostrar username y manejar logout
// ----------------------------------------------------------------

function initNavbar() {
  const user = getUser();
  const el   = document.getElementById("navUsername");
  if (el && user) el.textContent = user.full_name || user.username;

  const btnLogout = document.getElementById("btnLogout");
  if (btnLogout) {
    btnLogout.addEventListener("click", async () => {
      try { await Api.logout(); } catch (_) {}
      clearSession();
      window.location.href = "/frontend/index.html";
    });
  }
}

// ----------------------------------------------------------------
// Utilidades UI
// ----------------------------------------------------------------

function showAlert(elId, msg, type = "danger") {
  const el = document.getElementById(elId);
  if (!el) return;
  el.className = `alert alert-${type}`;
  el.textContent = msg;
  el.classList.remove("d-none");
  setTimeout(() => el.classList.add("d-none"), 6000);
}

function hideAlert(elId) {
  const el = document.getElementById(elId);
  if (el) el.classList.add("d-none");
}

function showToast(msg, type = "success") {
  const toast = document.getElementById("toastMsg");
  const body  = document.getElementById("toastBody");
  if (!toast || !body) return;
  body.textContent = msg;
  toast.className  = `toast align-items-center text-bg-${type} border-0`;
  const bsToast    = bootstrap.Toast.getOrCreateInstance(toast, { delay: 3500 });
  bsToast.show();
}

function setLoading(btnId, spinnerId, loading) {
  const btn     = document.getElementById(btnId);
  const spinner = document.getElementById(spinnerId);
  if (!btn) return;
  btn.disabled = loading;
  if (spinner) spinner.classList.toggle("d-none", !loading);
}

function fmtDate(iso) {
  if (!iso) return "—";
  return new Date(iso).toLocaleDateString("es-AR", {
    day: "2-digit", month: "2-digit", year: "numeric",
  });
}

function fmtDatetime(iso) {
  if (!iso) return "—";
  return new Date(iso).toLocaleString("es-AR", {
    day: "2-digit", month: "2-digit", year: "numeric",
    hour: "2-digit", minute: "2-digit",
  });
}

function snBadge(sn) {
  const map = {
    facebook:  { cls: "mm-badge-fb",  icon: "bi-facebook",  label: "Facebook"  },
    instagram: { cls: "mm-badge-ig",  icon: "bi-instagram", label: "Instagram" },
    twitter:   { cls: "mm-badge-tw",  icon: "bi-twitter-x", label: "X"         },
  };
  const d = map[sn] || { cls: "bg-secondary", icon: "bi-globe", label: sn };
  return `<span class="badge ${d.cls}"><i class="bi ${d.icon} me-1"></i>${d.label}</span>`;
}

// ----------------------------------------------------------------
// Página de Login
// ----------------------------------------------------------------

(function initLogin() {
  const isLoginPage = !!document.getElementById("formLogin");
  if (!isLoginPage) {
    // En todas las páginas protegidas: verificar sesión y montar navbar
    if (requireAuth()) initNavbar();
    return;
  }

  // Si ya está logueado, redirigir al dashboard
  if (isLoggedIn()) {
    window.location.href = "/frontend/dashboard.html";
    return;
  }

  const panelLogin   = document.getElementById("panelLogin");
  const panelReset   = document.getElementById("panelReset");
  const panelNewPass = document.getElementById("panelNewPass");

  function showPanel(name) {
    panelLogin.classList.toggle("d-none",   name !== "login");
    panelReset.classList.toggle("d-none",   name !== "reset");
    panelNewPass.classList.toggle("d-none", name !== "newpass");
  }

  // Detectar token de reset en URL
  const params = new URLSearchParams(window.location.search);
  const resetToken = params.get("reset");
  if (resetToken) {
    showPanel("newpass");
  }

  // Toggle visibilidad contraseña
  document.getElementById("btnTogglePass")?.addEventListener("click", () => {
    const inp = document.getElementById("inputPass");
    const ico = document.querySelector("#btnTogglePass i");
    if (inp.type === "password") {
      inp.type = "text";
      ico.className = "bi bi-eye-slash";
    } else {
      inp.type = "password";
      ico.className = "bi bi-eye";
    }
  });

  document.getElementById("linkForgot")?.addEventListener("click", (e) => {
    e.preventDefault();
    hideAlert("alertLogin");
    showPanel("reset");
  });

  document.getElementById("linkBackLogin")?.addEventListener("click", (e) => {
    e.preventDefault();
    hideAlert("alertReset");
    showPanel("login");
  });

  // Formulario login
  document.getElementById("formLogin")?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const username = document.getElementById("inputUser").value.trim();
    const password = document.getElementById("inputPass").value;
    if (!username || !password) return;

    setLoading("btnLogin", "btnLoginSpinner", true);
    try {
      const data = await Api.login(username, password);
      saveSession(data.access_token, data.user);
      window.location.href = "/frontend/dashboard.html";
    } catch (err) {
      showAlert("alertLogin", err.message, "danger");
      setLoading("btnLogin", "btnLoginSpinner", false);
    }
  });

  // Formulario reset request
  document.getElementById("formReset")?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const email = document.getElementById("inputEmail").value.trim();
    if (!email) return;

    setLoading("btnReset", "btnResetSpinner", true);
    try {
      const data = await Api.resetRequest(email);
      showAlert("alertReset", data.message, "success");
    } catch (err) {
      showAlert("alertReset", err.message, "danger");
    } finally {
      setLoading("btnReset", "btnResetSpinner", false);
    }
  });

  // Formulario nueva contraseña
  document.getElementById("formNewPass")?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const np  = document.getElementById("inputNewPass").value;
    const cnf = document.getElementById("inputConfirmPass").value;

    if (np !== cnf) {
      showAlert("alertNewPass", "Las contraseñas no coinciden.", "danger");
      return;
    }

    setLoading("btnNewPass", "btnNewPassSpinner", true);
    try {
      await Api.resetPassword(resetToken, np);
      showAlert("alertNewPass", "Contraseña actualizada. Redirigiendo...", "success");
      setTimeout(() => {
        window.location.href = "/frontend/index.html";
      }, 2000);
    } catch (err) {
      showAlert("alertNewPass", err.message, "danger");
      setLoading("btnNewPass", "btnNewPassSpinner", false);
    }
  });
})();
