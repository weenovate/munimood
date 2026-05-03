/**
 * MuniMood — Cliente API centralizado
 * Todas las llamadas al backend pasan por este módulo.
 */

const API_BASE = "/api";

const Api = (() => {

  function _token() {
    return localStorage.getItem("mm_token") || "";
  }

  function _headers(extra = {}) {
    const h = { "Content-Type": "application/json", ...extra };
    const t = _token();
    if (t) h["Authorization"] = `Bearer ${t}`;
    return h;
  }

  async function _fetch(path, options = {}) {
    const url = `${API_BASE}${path}`;
    const res = await fetch(url, {
      ...options,
      headers: _headers(options.headers || {}),
    });

    if (res.status === 401) {
      localStorage.removeItem("mm_token");
      localStorage.removeItem("mm_user");
      window.location.href = "/frontend/index.html";
      return;
    }

    let body;
    const ct = res.headers.get("content-type") || "";
    if (ct.includes("application/json")) {
      body = await res.json();
    } else {
      body = await res.text();
    }

    if (!res.ok) {
      const msg = body?.detail || body?.message || body || "Error desconocido";
      throw new Error(Array.isArray(msg) ? msg.map(e => e.msg).join(", ") : String(msg));
    }
    return body;
  }

  return {
    // --- Auth ---
    login: (username, password) =>
      _fetch("/auth/login", { method: "POST", body: JSON.stringify({ username, password }) }),

    logout: () =>
      _fetch("/auth/logout", { method: "POST" }),

    resetRequest: (email) =>
      _fetch("/auth/reset-password-request", { method: "POST", body: JSON.stringify({ email }) }),

    resetPassword: (token, new_password) =>
      _fetch("/auth/reset-password", { method: "POST", body: JSON.stringify({ token, new_password }) }),

    me: () => _fetch("/auth/me"),

    // --- Fuentes ---
    getSources: () => _fetch("/sources"),
    createSource: (data) => _fetch("/sources", { method: "POST", body: JSON.stringify(data) }),
    updateSource: (id, data) => _fetch(`/sources/${id}`, { method: "PUT", body: JSON.stringify(data) }),
    deleteSource: (id) => _fetch(`/sources/${id}`, { method: "DELETE" }),

    // --- Dashboard ---
    getDashboard: () => _fetch("/dashboard"),

    // --- Temas ---
    getTopics: () => _fetch("/topics"),
    createTopic: (data) => _fetch("/topics", { method: "POST", body: JSON.stringify(data) }),
    updateTopic: (id, data) => _fetch(`/topics/${id}`, { method: "PUT", body: JSON.stringify(data) }),
    deleteTopic: (id) => _fetch(`/topics/${id}`, { method: "DELETE" }),

    // --- Posts ---
    getPostsByTopic: (topicId, page = 1, perPage = 20) =>
      _fetch(`/topics/${topicId}/posts?page=${page}&per_page=${perPage}`),
    getPostDetail: (postId) => _fetch(`/posts/${postId}`),

    // --- Config ---
    getTrafficLight: () => _fetch("/config/traffic-light"),
    updateTrafficLight: (data) =>
      _fetch("/config/traffic-light", { method: "PUT", body: JSON.stringify(data) }),

    getAIEngine: () => _fetch("/config/ai-engine"),
    updateAIEngine: (data) =>
      _fetch("/config/ai-engine", { method: "PUT", body: JSON.stringify(data) }),

    getUsers: () => _fetch("/config/users"),
    createUser: (data) => _fetch("/config/users", { method: "POST", body: JSON.stringify(data) }),
    updateUser: (id, data) => _fetch(`/config/users/${id}`, { method: "PUT", body: JSON.stringify(data) }),
    changePassword: (id, data) =>
      _fetch(`/config/users/${id}/password`, { method: "PUT", body: JSON.stringify(data) }),
    deleteUser: (id) => _fetch(`/config/users/${id}`, { method: "DELETE" }),

    // --- Scraping ---
    triggerScraping: (sourceId = null) =>
      _fetch("/scraping/trigger", {
        method: "POST",
        body: JSON.stringify({ source_id: sourceId }),
      }),
    getScrapingLogs: (limit = 30) => _fetch(`/scraping/logs?limit=${limit}`),
  };
})();
