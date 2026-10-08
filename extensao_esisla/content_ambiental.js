// Content Script: Bridge no Sistema Ambiental
// Captura os dados de laudos e oferece opção explícita de adicionar à Fila da Extensão e-SISLA

(function() {
  console.log('[Ambiental e-SISLA Extension] Bridge ativado com suporte à Fila Inteligente.');

  // Avisa a página web que a extensão está presente e equipada com fila
  try {
    window.postMessage({ 
      type: 'AMBIENTAL_EXTENSION_STATUS', 
      installed: true, 
      version: '1.3.0',
      hasQueueSupport: true 
    }, '*');
    document.documentElement.setAttribute('data-ambiental-extension', 'active');
  } catch(_) {}

  let pendingPayload = null;
  let lastPromptedProto = null;
  let lastPromptedTime = 0;

  function salvarNaFila(payload) {
    if (!payload) return;
    try {
      chrome.runtime.sendMessage({ 
        action: 'ADICIONAR_FICHA_FILA', 
        payload: payload 
      }, (res) => {
        removerPrompt();
        mostrarFeedbackAdicionado(payload, res?.count || 1);
      });
    } catch(err) {
      console.warn('[Ambiental e-SISLA Extension] Erro ao sincronizar com a fila:', err);
    }
  }

  function removerPrompt() {
    const existing = document.querySelectorAll('#ambientalExtensionQueuePrompt, .ambiental-ext-queue-prompt');
    existing.forEach(el => el.remove());
  }

  // Exibe o card interativo dando ao médico a ESCOLHA de adicionar ou não aquela ficha à fila
  function exibirOpcaoCopiarParaFila(payload) {
    if (!payload) return;
    pendingPayload = payload;

    const proto = String(payload.protocolo || 'Sem Protocolo');
    const now = Date.now();

    // Se já está exibindo o prompt para este protocolo recentemente, apenas atualiza payload
    const existing = document.getElementById('ambientalExtensionQueuePrompt');
    if (existing && lastPromptedProto === proto && (now - lastPromptedTime < 3500)) {
      return;
    }

    lastPromptedProto = proto;
    lastPromptedTime = now;
    removerPrompt();

    const pac = payload.servidor || payload.paciente || 'Servidor';
    const cid = payload.cdCidPm || payload['voResult.voParecerFinal.cdCidPm'] || '';
    const dias = payload['voResult.voParecerFinal.qtDiasPm'] || payload.dias || '';

    const prompt = document.createElement('div');
    prompt.id = 'ambientalExtensionQueuePrompt';
    prompt.className = 'ambiental-ext-queue-prompt';
    prompt.innerHTML = `
      <div style="display:flex;align-items:flex-start;justify-content:space-between;gap:12px;margin-bottom:8px">
        <div style="display:flex;align-items:center;gap:8px">
          <span style="font-size:22px;line-height:1">⚡</span>
          <div>
            <strong style="font-size:13.5px;color:#0F172A;display:block;font-weight:800">Ficha e-SISLA Pronta</strong>
            <span style="font-size:11.5px;color:#334155;font-weight:600;display:block">${pac}</span>
          </div>
        </div>
        <button type="button" class="btn-ext-prompt-close" style="background:transparent;border:none;color:#94A3B8;cursor:pointer;font-size:16px;padding:2px 6px;border-radius:4px" title="Fechar sem adicionar">✕</button>
      </div>

      <div style="background:#F8FAFC;border:1px solid #E2E8F0;border-radius:8px;padding:8px 10px;margin-bottom:12px;font-size:11.5px;color:#475569">
        <div><strong>Protocolo:</strong> <code style="font-family:monospace;font-weight:700;color:#0369A1">${proto}</code></div>
        ${cid ? `<div style="margin-top:2px"><strong>CID:</strong> ${cid} ${dias ? `· <strong>${dias} dias</strong>` : ''}</div>` : ''}
      </div>

      <div style="font-size:11.5px;color:#475569;margin-bottom:12px;line-height:1.35">
        Deseja copiar e adicionar esta ficha à <strong>Fila da Extensão</strong> para preencher automaticamente no e-SISLA?
      </div>

      <div style="display:flex;align-items:center;justify-content:flex-end;gap:8px">
        <button type="button" class="btn-ext-prompt-ignore" style="background:#FFFFFF;border:1px solid #CBD5E1;color:#64748B;font-size:11.5px;font-weight:700;padding:6px 12px;border-radius:7px;cursor:pointer">
          Não Adicionar
        </button>
        <button type="button" class="btn-ext-prompt-add" style="background:linear-gradient(135deg, #0284C7 0%, #0369A1 100%);color:#FFFFFF;border:none;font-size:11.5px;font-weight:800;padding:6.5px 14px;border-radius:7px;cursor:pointer;box-shadow:0 2px 6px rgba(2,132,199,0.3)">
          ⚡ Adicionar à Fila e-SISLA
        </button>
      </div>
    `;

    prompt.style.cssText = `
      position: fixed;
      bottom: 24px;
      right: 24px;
      width: min(380px, 92vw);
      background: #FFFFFF;
      border: 1.5px solid #0284C7;
      border-left: 5px solid #0284C7;
      border-radius: 14px;
      padding: 14px 16px;
      box-shadow: 0 16px 36px rgba(15, 23, 42, 0.16);
      z-index: 2147483647;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      animation: ambientalPromptSlideUp 0.3s cubic-bezier(0.16, 1, 0.3, 1);
      transition: opacity 0.25s, transform 0.25s;
    `;

    document.body.appendChild(prompt);

    // Eventos dos botões atrelados DIRETAMENTE ao elemento 'prompt' recém-criado
    const btnAdd = prompt.querySelector('.btn-ext-prompt-add');
    const btnIgnore = prompt.querySelector('.btn-ext-prompt-ignore');
    const btnClose = prompt.querySelector('.btn-ext-prompt-close');

    if (btnAdd) {
      btnAdd.addEventListener('click', (e) => {
        e.preventDefault();
        e.stopPropagation();
        salvarNaFila(payload);
      });
    }

    if (btnIgnore) {
      btnIgnore.addEventListener('click', (e) => {
        e.preventDefault();
        e.stopPropagation();
        removerPrompt();
      });
    }

    if (btnClose) {
      btnClose.addEventListener('click', (e) => {
        e.preventDefault();
        e.stopPropagation();
        removerPrompt();
      });
    }

    // Auto-dismiss após 45 segundos se não for clicado
    setTimeout(() => {
      if (document.body.contains(prompt)) {
        prompt.remove();
      }
    }, 45000);
  }

  function mostrarFeedbackAdicionado(payload, totalFila) {
    const toast = document.createElement('div');
    const pac = payload.servidor || payload.paciente || 'Servidor';
    const proto = payload.protocolo || '';

    toast.innerHTML = `
      <div style="display:flex;align-items:center;gap:10px;">
        <span style="font-size:20px;line-height:1">✅</span>
        <div>
          <strong style="display:block;font-size:12.5px;color:#0F172A">Adicionado à Fila e-SISLA!</strong>
          <span style="display:block;font-size:11px;color:#475569">${pac} ${proto ? `(Prot. ${proto})` : ''}</span>
        </div>
      </div>
      <div style="font-size:10.5px;color:#047857;font-weight:700;margin-top:6px">
        ✓ ${totalFila} laudo(s) na fila do dia · O e-SISLA identificará este periciado automaticamente!
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
      z-index: 2147483647;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      transition: opacity 0.3s, transform 0.3s;
    `;

    document.body.appendChild(toast);

    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateY(10px)';
      setTimeout(() => toast.remove(), 350);
    }, 4000);
  }

  // 1. Escuta eventos disparados pela página web (postMessage)
  window.addEventListener('message', (event) => {
    if (event.data && event.data.type === 'AMBIENTAL_ESISLA_PAYLOAD') {
      const p = event.data.payload;
      if (event.data.forceQueue || event.data.autoAdd) {
        salvarNaFila(p);
      } else {
        exibirOpcaoCopiarParaFila(p);
      }
    }
  });

  // 2. Monitora mudanças no localStorage (contingência quando gerada)
  function checkLocalStorage() {
    try {
      const raw = localStorage.getItem('ambiental_esisla_current_payload');
      if (raw) {
        const parsed = JSON.parse(raw);
        if (parsed && (parsed.timestamp || parsed.protocolo)) {
          const syncKey = String(parsed.timestamp || parsed.protocolo);
          if (!window._lastSyncTime || window._lastSyncTime !== syncKey) {
            window._lastSyncTime = syncKey;
            exibirOpcaoCopiarParaFila(parsed);
          }
        }
      }
    } catch(_) {}
  }

  setInterval(checkLocalStorage, 1500);

  // 3. Clique em botões de copiar explícito no sistema Ambiental: adiciona diretamente à fila
  document.addEventListener('click', (e) => {
    const btn = e.target.closest(
      '#copyEsislaBtn, #btnCopyEsislaJson, #btnCopiarLaudoEsisla, #esislaCopyHeaderBtn, ' +
      '.btn-copy-card-block, .btn-copy-mini, .top-btn-esisla, ' +
      '[onclick*="copiarLaudoEsisla"], [onclick*="copyEsisla"], [onclick*="copyEsislaJson"]'
    );
    if (btn) {
      setTimeout(() => {
        try {
          const raw = localStorage.getItem('ambiental_esisla_current_payload');
          if (raw) {
            const parsed = JSON.parse(raw);
            if (parsed && (parsed.campos_esisla || parsed.protocolo)) {
              salvarNaFila(parsed);
            }
          }
        } catch(_) {}
      }, 150);
    }
  }, true);

  // 4. Se o usuário copiar JSON do e-SISLA para a área de transferência
  window.addEventListener('copy', () => {
    setTimeout(() => {
      try {
        const raw = localStorage.getItem('ambiental_esisla_current_payload');
        if (raw) {
          const parsed = JSON.parse(raw);
          if (parsed && (parsed.campos_esisla || parsed.protocolo)) {
            salvarNaFila(parsed);
          }
        }
      } catch(_) {}
    }, 200);
  });

})();
