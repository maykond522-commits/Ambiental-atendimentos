/* Ambiental — utilitários globais e armazenamento local resiliente. */
(() => {
  "use strict";

  const root = window.AmbientalUtils = window.AmbientalUtils || {};

  root.escapeHtml = root.escapeHtml || ((value) => String(value ?? "").replace(/[&<>"']/g, (m) => ({
    "&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#039;"
  }[m])));

  const toastState = { timer: null };
  root.toast = (message, timeout = 2600) => {
    let el = document.getElementById("toast");
    if (!el) {
      el = document.createElement("div");
      el.id = "toast";
      el.setAttribute("role", "status");
      el.setAttribute("aria-live", "polite");
      document.body.appendChild(el);
    }
    el.textContent = String(message ?? "");
    el.classList.add("show");
    window.clearTimeout(toastState.timer);
    toastState.timer = window.setTimeout(() => el.classList.remove("show"), timeout);
  };
  window.toast = root.toast;

  function ensureDialog() {
    let overlay = document.getElementById("customDialogOverlay");
    if (overlay) return overlay;
    overlay = document.createElement("div");
    overlay.id = "customDialogOverlay";
    overlay.setAttribute("aria-hidden", "true");
    overlay.innerHTML = `
      <div id="customDialogBox" role="dialog" aria-modal="true" aria-labelledby="customDialogTitle" aria-describedby="customDialogMessage">
        <div id="customDialogHeader"><strong id="customDialogTitle">Aviso</strong></div>
        <div id="customDialogMessage"></div>
        <div id="customDialogActions">
          <button id="customDialogCancel" type="button">Cancelar</button>
          <button id="customDialogConfirm" type="button">OK</button>
        </div>
      </div>`;
    document.body.appendChild(overlay);
    return overlay;
  }

  const dialog = {
    resolve: null,
    open(title, message, isConfirm = false) {
      const overlay = ensureDialog();
      const titleEl = document.getElementById("customDialogTitle");
      const msgEl = document.getElementById("customDialogMessage");
      const cancelEl = document.getElementById("customDialogCancel");
      const confirmEl = document.getElementById("customDialogConfirm");
      titleEl.textContent = title || (isConfirm ? "Confirmação" : "Aviso do Sistema");
      msgEl.textContent = String(message ?? "");
      cancelEl.style.display = isConfirm ? "inline-flex" : "none";
      confirmEl.textContent = isConfirm ? "Confirmar" : "OK";
      overlay.classList.add("open");
      overlay.setAttribute("aria-hidden", "false");
      return new Promise((resolve) => {
        dialog.resolve = resolve;
        confirmEl.onclick = () => dialog.confirmAction();
        cancelEl.onclick = () => dialog.cancel();
      });
    },
    close(result = false) {
      const overlay = document.getElementById("customDialogOverlay");
      if (overlay) {
        overlay.classList.remove("open");
        overlay.setAttribute("aria-hidden", "true");
      }
      const resolve = dialog.resolve;
      dialog.resolve = null;
      if (resolve) resolve(!!result);
    },
    cancel() { dialog.close(false); },
    confirmAction() { dialog.close(true); }
  };
  root.CustomDialog = window.CustomDialog = dialog;

  window.alert = (message) => dialog.open("Aviso do Sistema", message, false);
  window.confirm = (message) => dialog.open("Confirmação", message, true);

  // IndexedDB: armazenamento primário para rascunhos/offline.
  const DB_NAME = "ambiental-lts-local";
  const DB_VERSION = 2;
  const STORE = "drafts";
  const QUEUE = "sync_queue";
  let dbPromise = null;

  function openDb() {
    if (dbPromise) return dbPromise;
    dbPromise = new Promise((resolve, reject) => {
      if (!("indexedDB" in window)) return reject(new Error("IndexedDB indisponível."));
      const req = indexedDB.open(DB_NAME, DB_VERSION);
      req.onupgradeneeded = () => {
        const db = req.result;
        if (!db.objectStoreNames.contains(STORE)) {
          db.createObjectStore(STORE, { keyPath: "key" });
        }
        if (!db.objectStoreNames.contains(QUEUE)) {
          const store = db.createObjectStore(QUEUE, { keyPath: "key" });
          store.createIndex("updatedAt", "updatedAt", { unique: false });
        }
      };
      req.onsuccess = () => resolve(req.result);
      req.onerror = () => reject(req.error || new Error("Não foi possível abrir o armazenamento local."));
    });
    return dbPromise;
  }

  root.DraftStore = {
    async put(key, value) {
      const db = await openDb();
      return new Promise((resolve, reject) => {
        const tx = db.transaction(STORE, "readwrite");
        tx.objectStore(STORE).put({ key: String(key), value, updatedAt: new Date().toISOString() });
        tx.oncomplete = () => resolve(true);
        tx.onerror = () => reject(tx.error || new Error("Falha ao salvar rascunho local."));
      });
    },
    async get(key) {
      try {
        const db = await openDb();
        return await new Promise((resolve, reject) => {
          const tx = db.transaction(STORE, "readonly");
          const req = tx.objectStore(STORE).get(String(key));
          req.onsuccess = () => resolve(req.result?.value ?? null);
          req.onerror = () => reject(req.error || new Error("Falha ao ler rascunho local."));
        });
      } catch {
        return null;
      }
    },
    async remove(key) {
      try {
        const db = await openDb();
        return await new Promise((resolve, reject) => {
          const tx = db.transaction(STORE, "readwrite");
          tx.objectStore(STORE).delete(String(key));
          tx.oncomplete = () => resolve(true);
          tx.onerror = () => reject(tx.error || new Error("Falha ao remover rascunho local."));
        });
      } catch {
        return false;
      }
    },
    async clear() {
      try {
        const db = await openDb();
        return await new Promise((resolve, reject) => {
          const tx = db.transaction(STORE, "readwrite");
          tx.objectStore(STORE).clear();
          tx.oncomplete = () => resolve(true);
          tx.onerror = () => reject(tx.error || new Error("Falha ao limpar armazenamento local."));
        });
      } catch {
        return false;
      }
    }
  };

  root.SyncQueue = {
    async put(key, payload, meta = {}) {
      const db = await openDb();
      return new Promise((resolve, reject) => {
        const tx = db.transaction(QUEUE, "readwrite");
        tx.objectStore(QUEUE).put({
          key: String(key),
          payload,
          endpoint: meta.endpoint || null,
          updatedAt: new Date().toISOString(),
          attempts: Number(meta.attempts || 0),
          lastError: meta.lastError || null,
        });
        tx.oncomplete = () => resolve(true);
        tx.onerror = () => reject(tx.error || new Error("Falha ao enfileirar sincronização."));
      });
    },
    async list() {
      try {
        const db = await openDb();
        return await new Promise((resolve, reject) => {
          const tx = db.transaction(QUEUE, "readonly");
          const req = tx.objectStore(QUEUE).getAll();
          req.onsuccess = () => resolve((req.result || []).sort((a,b) => String(a.updatedAt).localeCompare(String(b.updatedAt))));
          req.onerror = () => reject(req.error || new Error("Falha ao ler fila de sincronização."));
        });
      } catch { return []; }
    },
    async remove(key) {
      try {
        const db = await openDb();
        return await new Promise((resolve, reject) => {
          const tx = db.transaction(QUEUE, "readwrite");
          tx.objectStore(QUEUE).delete(String(key));
          tx.oncomplete = () => resolve(true);
          tx.onerror = () => reject(tx.error || new Error("Falha ao remover item da fila."));
        });
      } catch { return false; }
    },
    async count() {
      try {
        const db = await openDb();
        return await new Promise((resolve, reject) => {
          const tx = db.transaction(QUEUE, "readonly");
          const req = tx.objectStore(QUEUE).count();
          req.onsuccess = () => resolve(req.result || 0);
          req.onerror = () => reject(req.error || new Error("Falha ao contar a fila."));
        });
      } catch { return 0; }
    }
  };

  root.legacyStorage = {
    get(key) { try { return localStorage.getItem(key); } catch { return null; } },
    remove(key) { try { localStorage.removeItem(key); } catch {} }
  };
})();
