// Content Script: Bridge no Sistema Ambiental
// Captura os dados de laudos e sincroniza automaticamente com o chrome.storage

(function() {
  console.log('[Ambiental e-SISLA Extension] Bridge ativado no sistema Ambiental.');

  // Avisa a página web que a extensão está presente
  try {
    window.postMessage({ type: 'AMBIENTAL_EXTENSION_STATUS', installed: true, version: '1.0.0' }, '*');
    document.documentElement.setAttribute('data-ambiental-extension', 'active');
  } catch(_) {}

  function salvarPayload(payload) {
    if (!payload) return;
    try {
      chrome.runtime.sendMessage({ action: 'SALVAR_FICHA', payload: payload }, (res) => {
        mostrarNotificacaoExtensao(payload);
      });
    } catch(err) {
      console.warn('[Ambiental e-SISLA Extension] Erro ao sincronizar:', err);
    }
  }

  function mostrarNotificacaoExtensao(payload) {
    var oldToast = document.getElementById('ambientalExtensionSyncToast');
    if (oldToast) oldToast.remove();

    var toast = document.createElement('div');
    toast.id = 'ambientalExtensionSyncToast';
    var proto = payload.protocolo || 'Atendimento';
    var pac = payload.servidor || payload.paciente || '';
    
    toast.innerHTML = `
      <div style="display:flex;align-items:center;gap:10px;">
        <span style="font-size:20px;line-height:1">⚡</span>
        <div>
          <strong style="display:block;font-size:12.5px;color:#0F172A">Extensão e-SISLA Sincronizada!</strong>
          <span style="display:block;font-size:11px;color:#475569">${proto} ${pac ? '· ' + pac : ''}</span>
        </div>
      </div>
      <div style="font-size:10.5px;color:#047857;font-weight:700;margin-top:6px;display:flex;align-items:center;gap:4px">
        <span>✓ Pronto para preenchimento com 1 clique na aba do e-SISLA</span>
      </div>
    `;

    toast.style.cssText = `
      position: fixed;
      bottom: 24px;
      right: 24px;
      background: #FFFFFF;
      border: 1.5px solid #10B981;
      border-left: 5px solid #10B981;
      border-radius: 12px;
      padding: 12px 16px;
      box-shadow: 0 12px 30px rgba(0,0,0,0.12);
      z-index: 999999;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      animation: ambientalSlideUp 0.3s ease-out;
      transition: opacity 0.3s, transform 0.3s;
    `;

    document.body.appendChild(toast);

    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateY(10px)';
      setTimeout(() => toast.remove(), 350);
    }, 4500);
  }

  // 1. Escuta eventos disparados pela página web (postMessage)
  window.addEventListener('message', (event) => {
    if (event.data && event.data.type === 'AMBIENTAL_ESISLA_PAYLOAD') {
      salvarPayload(event.data.payload);
    }
  });

  // 2. Monitora mudanças no localStorage (contingência)
  function checkLocalStorage() {
    try {
      var raw = localStorage.getItem('ambiental_esisla_current_payload');
      if (raw) {
        var parsed = JSON.parse(raw);
        if (parsed && parsed.timestamp) {
          // Se o timestamp for recente (últimos 3 minutos) e diferente do último salvo
          if (!window._lastSyncTime || window._lastSyncTime !== parsed.timestamp) {
            window._lastSyncTime = parsed.timestamp;
            salvarPayload(parsed);
          }
        }
      }
    } catch(_) {}
  }

  setInterval(checkLocalStorage, 1500);

  // 3. Captura cliques em botões de copiar ou gerar eSisla
  document.addEventListener('click', (e) => {
    var btn = e.target.closest('#copyEsislaBtn, #btnCopyEsislaJson, .btn-copy-hero, #generateEsislaBtn, #btnCopiarLaudoEsisla');
    if (btn) {
      setTimeout(checkLocalStorage, 400);
    }
  }, true);

})();
