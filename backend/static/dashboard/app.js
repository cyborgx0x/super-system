const btns = document.querySelectorAll(".tab-btn");
const panels = document.querySelectorAll(".tab-panel");
btns.forEach((btn) => {
  btn.addEventListener("click", () => {
    btns.forEach((b) => b.classList.remove("active"));
    panels.forEach((p) => p.classList.remove("active"));
    btn.classList.add("active");
    document.getElementById("tab-" + btn.dataset.tab).classList.add("active");
  });
});

document.querySelectorAll(".card").forEach((card) => {
  card.addEventListener("mousemove", (e) => {
    const r = card.getBoundingClientRect();
    card.style.setProperty("--mx", ((e.clientX - r.left) / r.width) * 100 + "%");
    card.style.setProperty("--my", ((e.clientY - r.top) / r.height) * 100 + "%");
  });
});

const ACCESS_STATE_KEY = "super-system-access-state-v1";
const OAUTH_VAULT_KEY = "super-system-oauth-v1";
const OAUTH_PENDING_KEY = "super-system-oauth-pending-v1";
const DEFAULT_X_REDIRECT_URI = window.location.origin + "/x/callback";

function loadJsonStorage(key, fallback) {
  try { return JSON.parse(localStorage.getItem(key) || "null") || fallback; }
  catch { return fallback; }
}
function saveJsonStorage(key, value) { localStorage.setItem(key, JSON.stringify(value)); }
function loadSessionJson(key, fallback) {
  try { return JSON.parse(sessionStorage.getItem(key) || "null") || fallback; }
  catch { return fallback; }
}
function saveSessionJson(key, value) { sessionStorage.setItem(key, JSON.stringify(value)); }
function clearSessionJson(key) { sessionStorage.removeItem(key); }

function loadAccessState() { return loadJsonStorage(ACCESS_STATE_KEY, {}); }
function saveAccessState(state) { saveJsonStorage(ACCESS_STATE_KEY, state); }

function formatAccessTime(iso) {
  if (!iso) return "Not verified";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "Not verified";
  return "Verified: " + d.toLocaleString();
}

function parseRequiredServices(stepEl) {
  return (stepEl.dataset.requires || "").split(",").map((i) => i.trim()).filter(Boolean);
}

function getMissingServices(stepEl, state) {
  return parseRequiredServices(stepEl).filter((id) => !(state[id] && state[id].granted));
}

function refreshAccessUI(state) {
  document.querySelectorAll("[data-access-toggle]").forEach((toggle) => {
    const id = toggle.dataset.accessToggle;
    const entry = state[id] || { granted: false, verifiedAt: null };
    toggle.checked = !!entry.granted;
    const timeEl = document.querySelector("[data-access-time='" + id + "']");
    if (timeEl) timeEl.textContent = formatAccessTime(entry.verifiedAt);
  });
}

function refreshLockedSteps(state) {
  document.querySelectorAll(".mission-step").forEach((stepEl) => {
    const missing = getMissingServices(stepEl, state);
    stepEl.classList.toggle("locked", missing.length > 0);
  });
}

function setAccessGranted(serviceId, granted, verifiedAt) {
  accessState[serviceId] = {
    granted: !!granted,
    verifiedAt: granted ? verifiedAt || new Date().toISOString() : null,
  };
  saveAccessState(accessState);
  refreshAccessUI(accessState);
  refreshLockedSteps(accessState);
}

function maskToken(token) {
  if (!token || token.length < 14) return "-";
  return token.slice(0, 8) + "..." + token.slice(-4);
}

function formatDisplayTime(iso) {
  if (!iso) return "-";
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return "-";
  return date.toLocaleString();
}

async function exchangeXCode(params) {
  const body = new URLSearchParams({
    code: params.code, state: params.state, session_id: params.sessionId,
  });
  const resp = await fetch("/oauth/x/exchange", {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded", Accept: "application/json" },
    body,
  });
  const data = await resp.json().catch(() => ({}));
  if (!resp.ok) {
    throw new Error("Token exchange failed: " + (data.error_description || data.detail || JSON.stringify(data)));
  }
  return data;
}

async function createXOAuthSession(params) {
  const body = new URLSearchParams({
    client_id: params.clientId, client_secret: params.clientSecret || "",
    redirect_uri: params.redirectUri, scope: params.scope,
  });
  const resp = await fetch("/oauth/x/session", {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded", Accept: "application/json" },
    body,
  });
  const data = await resp.json().catch(() => ({}));
  if (!resp.ok) {
    throw new Error("Create OAuth session failed: " + (data.error_description || data.detail || JSON.stringify(data)));
  }
  return data;
}

function openTab(tabName) {
  btns.forEach((b) => b.classList.remove("active"));
  panels.forEach((p) => p.classList.remove("active"));
  const nextBtn = document.querySelector(".tab-btn[data-tab='" + tabName + "']");
  const nextPanel = document.getElementById("tab-" + tabName);
  if (nextBtn) nextBtn.classList.add("active");
  if (nextPanel) nextPanel.classList.add("active");
}

const oauthVault = loadJsonStorage(OAUTH_VAULT_KEY, {});
let pendingOAuth = loadSessionJson(OAUTH_PENDING_KEY, null);

function saveOAuthVault() { saveJsonStorage(OAUTH_VAULT_KEY, oauthVault); }

function setXAlert(message, isError) {
  const alertEl = document.getElementById("x-alert");
  if (!alertEl) return;
  alertEl.textContent = message;
  alertEl.style.color = isError ? "#ffb8b3" : "var(--muted)";
}

function refreshXSettingsUI() {
  const xVault = oauthVault.x || null;
  const pill = document.getElementById("x-status-pill");
  const verifiedEl = document.getElementById("x-verified-at");
  const scopesEl = document.getElementById("x-vault-scopes");
  const tokenEl = document.getElementById("x-token-preview");
  const clientIdInput = document.getElementById("x-client-id");
  const redirectInput = document.getElementById("x-redirect-uri");

  if (clientIdInput && xVault && xVault.clientId && !clientIdInput.value) {
    clientIdInput.value = xVault.clientId;
  }
  if (redirectInput && !redirectInput.value) {
    redirectInput.value = (xVault && xVault.redirectUri) || DEFAULT_X_REDIRECT_URI;
  }

  if (xVault && xVault.accessToken) {
    pill.textContent = "Connected";
    pill.classList.add("connected");
    verifiedEl.textContent = formatDisplayTime(xVault.verifiedAt);
    scopesEl.textContent = xVault.scope || "-";
    tokenEl.textContent = maskToken(xVault.accessToken);
    setAccessGranted("x", true, xVault.verifiedAt);
  } else {
    pill.textContent = "Not connected";
    pill.classList.remove("connected");
    verifiedEl.textContent = "-";
    scopesEl.textContent = "-";
    tokenEl.textContent = "-";
    setAccessGranted("x", false, null);
  }
}

let accessState = loadAccessState();
refreshAccessUI(accessState);
refreshLockedSteps(accessState);
refreshXSettingsUI();

document.querySelectorAll("[data-open-tab]").forEach((link) => {
  link.addEventListener("click", (event) => {
    event.preventDefault();
    openTab(link.dataset.openTab);
  });
});

document.querySelectorAll("[data-access-toggle]").forEach((toggle) => {
  toggle.addEventListener("change", () => {
    const serviceId = toggle.dataset.accessToggle;
    if (serviceId === "x" && oauthVault.x && oauthVault.x.accessToken) {
      refreshAccessUI(accessState);
      return;
    }
    accessState[serviceId] = {
      granted: toggle.checked,
      verifiedAt: toggle.checked ? new Date().toISOString() : null,
    };
    saveAccessState(accessState);
    refreshAccessUI(accessState);
    refreshLockedSteps(accessState);
  });
});

function updateMissionProgress(mission) {
  const steps = mission.querySelectorAll("[data-step]");
  const done = Array.from(steps).filter((s) => s.checked).length;
  const total = steps.length;
  const pct = total ? (done / total) * 100 : 0;
  const text = mission.querySelector("[data-progress-text]");
  const fill = mission.querySelector("[data-progress-fill]");
  if (text) text.textContent = done + "/" + total;
  if (fill) fill.style.width = pct + "%";
}

document.querySelectorAll("[data-mission]").forEach((mission) => {
  mission.querySelectorAll("[data-step]").forEach((step) => {
    step.addEventListener("change", () => {
      const stepEl = step.closest(".mission-step");
      const missing = getMissingServices(stepEl, accessState);
      if (step.checked && missing.length > 0) {
        step.checked = false;
        alert("Cần xác thực quyền truy cập trước: " +
          missing.join(", ") + ". Vào tab System > Service Access Validation.");
      }
      updateMissionProgress(mission);
    });
  });
  updateMissionProgress(mission);
});

document.getElementById("x-connect-btn").addEventListener("click", async () => {
  try {
    const clientId = document.getElementById("x-client-id").value.trim();
    const clientSecret = document.getElementById("x-client-secret").value.trim();
    const redirectUri = document.getElementById("x-redirect-uri").value.trim() || DEFAULT_X_REDIRECT_URI;
    const scope = (document.getElementById("x-scopes").value || "tweet.read tweet.write users.read")
      .replace(/,/g, " ").replace(/\s+/g, " ").trim();

    if (!clientId) { setXAlert("Please provide X Client ID.", true); return; }

    setXAlert("Creating secure OAuth session on backend...", false);
    const sessionData = await createXOAuthSession({ clientId, redirectUri, clientSecret, scope });

    pendingOAuth = {
      sessionId: sessionData.session_id, authorizeUrl: sessionData.authorize_url,
      expiresIn: sessionData.expires_in, clientId, redirectUri, scope,
      createdAt: new Date().toISOString(),
    };
    saveSessionJson(OAUTH_PENDING_KEY, pendingOAuth);

    const popup = window.open(sessionData.authorize_url, "x-oauth", "popup=yes,width=560,height=760");
    if (!popup) { setXAlert("Popup blocked. Allow popups then retry.", true); return; }
    setXAlert("Waiting for X authorization callback...", false);
  } catch (err) { setXAlert(String(err.message || err), true); }
});

document.getElementById("x-disconnect-btn").addEventListener("click", () => {
  delete oauthVault.x;
  saveOAuthVault();
  refreshXSettingsUI();
  setXAlert("Disconnected and removed token from local vault.", false);
});

document.getElementById("x-test-btn").addEventListener("click", async () => {
  try {
    const xVault = oauthVault.x;
    if (!xVault || !xVault.accessToken) { setXAlert("No token in vault. Connect first.", true); return; }

    const resp = await fetch("/oauth/x/users-me", {
      headers: { Authorization: "Bearer " + xVault.accessToken, Accept: "application/json" },
    });
    const data = await resp.json().catch(() => ({}));
    if (!resp.ok) throw new Error(data.detail || data.error_description || "X users/me failed");

    oauthVault.x.verifiedAt = new Date().toISOString();
    oauthVault.x.userId = data && data.data ? data.data.id : undefined;
    saveOAuthVault();
    refreshXSettingsUI();
    setXAlert("Token works. users/me verified.", false);
  } catch (err) { setXAlert(String(err.message || err), true); }
});

window.addEventListener("message", async (event) => {
  if (event.origin !== window.location.origin) return;
  const payload = event.data || {};
  if (payload.type !== "x-oauth-callback") return;

  try {
    if (payload.error) {
      throw new Error("OAuth error: " + payload.error + (payload.errorDescription ? " - " + payload.errorDescription : ""));
    }

    pendingOAuth = pendingOAuth || loadSessionJson(OAUTH_PENDING_KEY, null);
    if (!pendingOAuth) throw new Error("Missing OAuth session. Click Connect again.");
    if (!payload.code) throw new Error("Missing authorization code from callback.");

    setXAlert("Exchanging code for access token...", false);
    const tokenData = await exchangeXCode({
      code: payload.code, state: payload.state || "", sessionId: pendingOAuth.sessionId,
    });

    oauthVault.x = {
      clientId: pendingOAuth.clientId, accessToken: tokenData.access_token || "",
      refreshToken: tokenData.refresh_token || "", tokenType: tokenData.token_type || "bearer",
      scope: tokenData.scope || pendingOAuth.scope, redirectUri: pendingOAuth.redirectUri,
      verifiedAt: new Date().toISOString(),
    };
    saveOAuthVault();
    clearSessionJson(OAUTH_PENDING_KEY);
    pendingOAuth = null;

    refreshXSettingsUI();
    setXAlert("Connected successfully. Token saved in browser vault.", false);
  } catch (err) { setXAlert(String(err.message || err), true); }
});
