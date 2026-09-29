/* Ambiental — Auth Manager
 * Centraliza autenticação Supabase, sessão, perfil e autorização do frontend.
 * Nunca persiste senha e nunca usa perfil enviado pelo navegador como prova de autorização.
 */
(() => {
  "use strict";

  const STATE = {
    client: null,
    config: null,
    remember: true,
    ready: null,
    profile: null,
    signingOut: false,
    localSignOutInProgress: false,
    syncedTokenHash: null,
    syncPromise: null,
  };

  const text = (v) => String(v ?? "").trim();

  async function loadConfig() {
    const res = await fetch("/api/auth/config", {
      method: "GET",
      headers: { "Accept": "application/json" },
      cache: "no-store",
    });
    const data = await res.json().catch(() => null);
    if (!res.ok || !data?.success) {
      throw new Error("Não foi possível carregar a configuração de acesso.");
    }
    STATE.config = data.data;
    return STATE.config;
  }

  const storage = {
    getItem(key) {
      return localStorage.getItem(key) ?? sessionStorage.getItem(key);
    },
    setItem(key, value) {
      const target = STATE.remember ? localStorage : sessionStorage;
      const other = STATE.remember ? sessionStorage : localStorage;
      target.setItem(key, value);
      other.removeItem(key);
    },
    removeItem(key) {
      localStorage.removeItem(key);
      sessionStorage.removeItem(key);
    },
  };

  async function init(options = {}) {
    if (typeof options.remember === "boolean") STATE.remember = options.remember;
    if (STATE.ready) return STATE.ready;

    STATE.ready = (async () => {
      const config = STATE.config || await loadConfig();
      if (!window.supabase?.createClient) {
        throw new Error("Biblioteca de autenticação indisponível.");
      }
      STATE.client = window.supabase.createClient(config.supabase_url, config.supabase_publishable_key, {
        auth: {
          persistSession: true,
          autoRefreshToken: true,
          detectSessionInUrl: true,
          storage,
          storageKey: "ambiental.auth.session",
        },
      });

      STATE.client.auth.onAuthStateChange((event, session) => {
        if (event === "SIGNED_IN" || event === "TOKEN_REFRESHED") {
          window.setTimeout(() => syncServerSession(session?.access_token), 0);
        }
        if (event === "SIGNED_OUT" && !STATE.localSignOutInProgress && !STATE.signingOut) {
          window.setTimeout(() => {
            fetch("/api/auth/logout", { method: "POST", credentials: "same-origin", keepalive: true }).catch(() => {});
          }, 0);
        }
      });

      return STATE.client;
    })();

    return STATE.ready;
  }

  async function setRemember(value) {
    STATE.remember = !!value;
    // Reinstancia o cliente para que o storage escolhido seja respeitado no próximo login.
    if (STATE.client) {
      STATE.localSignOutInProgress = true;
      await STATE.client.auth.signOut({ scope: "local" }).catch(() => {});
      STATE.localSignOutInProgress = false;
      STATE.client = null;
      STATE.ready = null;
    }
    return init({ remember: STATE.remember });
  }

  async function getClient() {
    return init();
  }

  async function getAccessToken() {
    const client = await getClient();
    // getSession é usado apenas para obter o access token mantido pelo SDK oficial.
    const { data } = await client.auth.getSession();
    return data?.session?.access_token || null;
  }

  async function getUser() {
    const client = await getClient();
    // getUser faz validação/autenticação junto ao Auth e não deve ser tratado como "dados confiáveis do localStorage".
    const { data, error } = await client.auth.getUser();
    if (error || !data?.user) return null;
    return data.user;
  }

  async function syncServerSession(token) {
    if (!token) return { ok: false, code: "NO_TOKEN" };
    const tokenHash = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(token))
      .then(buf => Array.from(new Uint8Array(buf)).map(b => b.toString(16).padStart(2, "0")).join(""))
      .catch(() => "");
    const storedHash = STATE.syncedTokenHash || sessionStorage.getItem("ambiental.auth.syncedHash");
    if (tokenHash && tokenHash === storedHash) return { ok: true };
    if (STATE.syncPromise) return STATE.syncPromise;
    STATE.syncPromise = (async () => {
      try {
        let res = await fetch("/api/auth/session", {
          method: "POST",
          credentials: "same-origin",
          headers: { "Authorization": `Bearer ${token}`, "Accept": "application/json" },
          cache: "no-store",
        });
        // Se deu erro de servidor (5xx) por cold start ou indisponibilidade temporária, tenta 1 retry rápido
        if (!res.ok && res.status >= 500) {
          await new Promise(r => setTimeout(r, 600));
          res = await fetch("/api/auth/session", {
            method: "POST",
            credentials: "same-origin",
            headers: { "Authorization": `Bearer ${token}`, "Accept": "application/json" },
            cache: "no-store",
          });
        }
        const data = await res.json().catch(() => null);
        if (res.ok) {
          if (tokenHash) {
            STATE.syncedTokenHash = tokenHash;
            try { sessionStorage.setItem("ambiental.auth.syncedHash", tokenHash); } catch(_) {}
          }
          if (data?.data) {
            STATE.profile = data.data;
            try { sessionStorage.setItem("ambiental.auth.profile", JSON.stringify({ profile: data.data, tokenHash, ts: Date.now() })); } catch(_) {}
          }
          return { ok: true, profile: data?.data };
        }
        return {
          ok: false,
          status: res.status,
          code: data?.error?.code || (res.status === 403 ? "NO_PROFILE" : "AUTH_SERVER_UNAVAILABLE"),
          message: data?.error?.message,
        };
      } catch (err) {
        return { ok: false, code: "NETWORK_ERROR", message: "Falha de conexão com o servidor.", error: err };
      } finally {
        STATE.syncPromise = null;
      }
    })();
    return STATE.syncPromise;
  }

  async function me() {
    const token = await getAccessToken();
    const tokenHash = token ? await crypto.subtle.digest("SHA-256", new TextEncoder().encode(token))
      .then(buf => Array.from(new Uint8Array(buf)).map(b => b.toString(16).padStart(2, "0")).join(""))
      .catch(() => "") : "";

    // 1. Cache ultrarrápido em sessionStorage para transições instantâneas entre telas (ex: abrir novo atendimento)
    if (tokenHash) {
      try {
        const cached = sessionStorage.getItem("ambiental.auth.profile");
        if (cached) {
          const parsed = JSON.parse(cached);
          if (parsed && parsed.ts && (Date.now() - parsed.ts < 300000) && (!parsed.tokenHash || parsed.tokenHash === tokenHash)) {
            STATE.profile = parsed.profile;
            STATE.syncedTokenHash = tokenHash;
            return STATE.profile;
          }
        }
      } catch (_) {}
    }

    const headers = { "Accept": "application/json" };
    if (token) headers.Authorization = `Bearer ${token}`;
    const res = await fetch("/api/auth/me", {
      credentials: "same-origin",
      headers,
      cache: "no-store",
    });
    const data = await res.json().catch(() => null);
    if (!res.ok || !data?.success) {
      if (res.status === 401) {
        try { sessionStorage.removeItem("ambiental.auth.profile"); } catch(_) {}
        return null;
      }
      throw new Error(data?.error?.message || "Não foi possível validar o usuário.");
    }
    STATE.profile = data.data;
    if (tokenHash) {
      try {
        sessionStorage.setItem("ambiental.auth.profile", JSON.stringify({ profile: STATE.profile, tokenHash, ts: Date.now() }));
        sessionStorage.setItem("ambiental.auth.syncedHash", tokenHash);
      } catch(_) {}
    }
    return STATE.profile;
  }

  function areaAllowed(profile, area) {
    if (!profile) return false;
    const role = profile.perfil;
    if (area === "gestao") return ["Administrador", "Coordenador", "Revisor", "Gestor", "Consulta"].includes(role);
    if (area === "atendimento") return ["Administrador", "Médico", "Coordenador", "Revisor"].includes(role);
    if (area === "portal-medico") return ["Administrador", "Médico"].includes(role);
    return true;
  }

  function roleHome(profile) {
    const permissions = new Set(profile?.permissoes || []);
    const role = profile?.perfil;
    if (["Administrador", "Gestor", "Coordenador", "Revisor", "Consulta"].includes(role)) return "/gestao";
    if (role === "Médico" && permissions.has("view")) return "/gestao-medicos.html";
    return "/acesso-negado.html";
  }

  async function requireAuth({ area } = {}) {
    await init();
    const profile = await me();
    if (!profile) {
      const target = encodeURIComponent(location.pathname + location.search);
      location.replace(`/login.html?next=${target}&reason=expired`);
      throw new Error("AUTH_REQUIRED");
    }
    if (area && !areaAllowed(profile, area)) {
      location.replace(`/acesso-negado.html?area=${encodeURIComponent(area)}`);
      throw new Error("PERMISSION_DENIED");
    }
    // Sincroniza o cookie HttpOnly de sessão apenas se ainda não estiver sincronizado
    const token = await getAccessToken();
    const storedHash = STATE.syncedTokenHash || sessionStorage.getItem("ambiental.auth.syncedHash");
    if (!storedHash) {
      await syncServerSession(token);
    }
    return profile;
  }

  async function login(email, password, remember) {
    const client = await init({ remember });
    const result = await client.auth.signInWithPassword({
      email: text(email).toLowerCase(),
      password,
    });
    if (result.error || !result.data?.session?.access_token) {
      return { ok: false, error: result.error || new Error("LOGIN_FAILED") };
    }
    STATE.remember = !!remember;
    const serverSynced = await syncServerSession(result.data.session.access_token);
    const syncOk = serverSynced === true || serverSynced?.ok === true;
    if (!syncOk) {
      await client.auth.signOut({ scope: "local" }).catch(() => {});
      const code = serverSynced?.code || "AUTH_SERVER_UNAVAILABLE";
      const message = serverSynced?.message;
      return { ok: false, code, message };
    }
    const profile = (typeof serverSynced === "object" && serverSynced?.profile) ? serverSynced.profile : await me();
    if (!profile) {
      await client.auth.signOut({ scope: "local" }).catch(() => {});
      await fetch("/api/auth/logout", { method: "POST", credentials: "same-origin" }).catch(() => {});
      return { ok: false, code: "NO_PROFILE" };
    }
    return { ok: true, profile };
  }

  async function recover(email) {
    const client = await init();
    const redirectTo = `${location.origin}/reset-password.html`;
    const { error } = await client.auth.resetPasswordForEmail(text(email).toLowerCase(), {
      redirectTo,
    });
    if (error) return { ok: false, error };
    return { ok: true };
  }

  async function updatePassword(password) {
    const client = await init();
    const { data, error } = await client.auth.updateUser({ password });
    if (error || !data?.user) return { ok: false, error };
    await syncServerSession(await getAccessToken());
    return { ok: true };
  }

  async function logout({ redirect = "/login.html" } = {}) {
    if (STATE.signingOut) return;
    STATE.signingOut = true;
    STATE.syncedTokenHash = null;
    STATE.syncPromise = null;
    STATE.profile = null;
    try {
      try {
        sessionStorage.removeItem("ambiental.auth.profile");
        sessionStorage.removeItem("ambiental.auth.syncedHash");
        storage.removeItem("ambiental.auth.session");
      } catch (_) {}
      await fetch("/api/auth/logout", { method: "POST", credentials: "same-origin", keepalive: true }).catch(() => {});
      if (STATE.client) await STATE.client.auth.signOut({ scope: "local" }).catch(() => {});
      localStorage.removeItem("ambiental_access_token");
      localStorage.removeItem("ambiental_user_email");
      sessionStorage.removeItem("ambiental_access_token");
      sessionStorage.removeItem("ambiental_user_email");
    } finally {
      if (redirect) location.replace(redirect);
    }
  }

  async function authFetch(input, initOptions = {}) {
    const token = await getAccessToken();
    const headers = new Headers(initOptions.headers || {});
    if (token) headers.set("Authorization", `Bearer ${token}`);
    headers.set("Accept", headers.get("Accept") || "application/json");
    let response = await fetch(input, {
      ...initOptions,
      credentials: initOptions.credentials || "same-origin",
      headers,
      cache: initOptions.cache || "no-store",
    });
    if (response.status === 401) {
      try {
        const client = await getClient();
        const { data: refData, error: refErr } = await client.auth.refreshSession().catch(e => ({ error: e }));
        if (!refErr && refData?.session?.access_token) {
          await syncServerSession(refData.session.access_token);
          const retryHeaders = new Headers(initOptions.headers || {});
          retryHeaders.set("Authorization", `Bearer ${refData.session.access_token}`);
          retryHeaders.set("Accept", retryHeaders.get("Accept") || "application/json");
          response = await fetch(input, {
            ...initOptions,
            credentials: initOptions.credentials || "same-origin",
            headers: retryHeaders,
            cache: initOptions.cache || "no-store",
          });
          if (response.status !== 401) {
            return response;
          }
        }
      } catch (_) {}
      await logout({ redirect: `/login.html?reason=expired&next=${encodeURIComponent(location.pathname + location.search)}` });
    }
    return response;
  }

  window.AmbientalAuth = {
    init, setRemember, getClient, getAccessToken, getUser, me, login, recover,
    updatePassword, logout, requireAuth, authFetch, syncServerSession, roleHome, areaAllowed,
    get profile() { return STATE.profile; },
  };
})();