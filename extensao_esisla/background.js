// Background Service Worker - Ambiental e-SISLA AutoFill (Manifest V3)
// Gerenciador de Fila Inteligente de Atendimentos Multi-Laudos e Sincronização

chrome.runtime.onInstalled.addListener(() => {
  console.log('[Ambiental e-SISLA] Extensão instalada e pronta para uso com fila de laudos.');
  chrome.storage.local.get(['ambiental_esisla_queue'], (res) => {
    updateBadge(res.ambiental_esisla_queue || []);
  });
});

function updateBadge(queue) {
  const pendingCount = (queue || []).filter(item => item.status !== 'preenchido').length;
  if (pendingCount > 0) {
    chrome.action.setBadgeText({ text: String(pendingCount) });
    chrome.action.setBadgeBackgroundColor({ color: '#00C95A' });
    chrome.action.setTitle({
      title: `Ambiental e-SISLA: ${pendingCount} laudo(s) pendente(s) na fila do dia`
    });
  } else if ((queue || []).length > 0) {
    chrome.action.setBadgeText({ text: '✓' });
    chrome.action.setBadgeBackgroundColor({ color: '#10B981' });
    chrome.action.setTitle({ title: 'Ambiental e-SISLA: Todos os laudos da fila foram preenchidos' });
  } else {
    chrome.action.setBadgeText({ text: '' });
    chrome.action.setTitle({ title: 'Ambiental ⚡ e-SISLA AutoFill' });
  }
}

// Atualiza o badge do ícone quando houver alterações na fila
chrome.storage.onChanged.addListener((changes, areaName) => {
  if (areaName === 'local') {
    if (changes.ambiental_esisla_queue) {
      updateBadge(changes.ambiental_esisla_queue.newValue || []);
    } else if (changes.ambiental_latest_esisla && !changes.ambiental_esisla_queue) {
      const val = changes.ambiental_latest_esisla.newValue;
      if (val && val.protocolo) {
        chrome.action.setBadgeText({ text: '1' });
        chrome.action.setBadgeBackgroundColor({ color: '#00C95A' });
      }
    }
  }
});

// Receptor de mensagens
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  // 1. Salvar ou Adicionar laudo na Fila Inteligente do Dia
  if (request.action === 'ADICIONAR_FICHA_FILA' || request.action === 'SALVAR_FICHA') {
    chrome.storage.local.get(['ambiental_esisla_queue'], (res) => {
      let queue = Array.isArray(res.ambiental_esisla_queue) ? res.ambiental_esisla_queue : [];
      const novo = {
        ...request.payload,
        status: 'pendente',
        timestamp: request.payload?.timestamp || new Date().toISOString()
      };
      const proto = String(novo.protocolo || '').trim();
      const idx = queue.findIndex(item => String(item.protocolo || '').trim() === proto && proto);
      if (idx !== -1) {
        queue[idx] = novo; // Atualiza laudo existente
      } else {
        queue.unshift(novo); // Insere no início da fila
      }
      if (queue.length > 50) queue = queue.slice(0, 50);

      chrome.storage.local.set({
        ambiental_esisla_queue: queue,
        ambiental_latest_esisla: novo
      }, () => {
        updateBadge(queue);
        sendResponse({ status: 'ok', count: queue.length });
      });
    });
    return true;
  }

  // 2. Obter toda a Fila do Dia
  if (request.action === 'OBTER_FILA') {
    chrome.storage.local.get(['ambiental_esisla_queue'], (result) => {
      sendResponse({ fila: Array.isArray(result.ambiental_esisla_queue) ? result.ambiental_esisla_queue : [] });
    });
    return true;
  }

  // 3. Obter Ficha Única (compatibilidade)
  if (request.action === 'OBTER_FICHA') {
    chrome.storage.local.get(['ambiental_latest_esisla', 'ambiental_esisla_queue'], (result) => {
      sendResponse({ 
        payload: result.ambiental_latest_esisla || (result.ambiental_esisla_queue?.[0] || null),
        fila: result.ambiental_esisla_queue || []
      });
    });
    return true;
  }

  // 4. Marcar Ficha como Preenchida no e-SISLA
  if (request.action === 'MARCAR_FICHA_PREENCHIDA') {
    chrome.storage.local.get(['ambiental_esisla_queue'], (res) => {
      let queue = Array.isArray(res.ambiental_esisla_queue) ? res.ambiental_esisla_queue : [];
      const proto = String(request.protocolo || '').trim();
      const nome = String(request.servidor || request.paciente || '').trim().toLowerCase();
      
      queue.forEach(item => {
        const itemProto = String(item.protocolo || '').trim();
        const itemNome = String(item.servidor || item.paciente || '').trim().toLowerCase();
        if ((proto && itemProto === proto) || (nome && itemNome === nome)) {
          item.status = 'preenchido';
          item.preenchido_em = new Date().toISOString();
        }
      });

      chrome.storage.local.set({ ambiental_esisla_queue: queue }, () => {
        updateBadge(queue);
        sendResponse({ status: 'ok' });
      });
    });
    return true;
  }

  // 5. Remover Laudo Específico da Fila
  if (request.action === 'REMOVER_FICHA_FILA') {
    chrome.storage.local.get(['ambiental_esisla_queue'], (res) => {
      let queue = Array.isArray(res.ambiental_esisla_queue) ? res.ambiental_esisla_queue : [];
      queue = queue.filter(item => String(item.protocolo || '').trim() !== String(request.protocolo || '').trim());
      chrome.storage.local.set({ ambiental_esisla_queue: queue }, () => {
        updateBadge(queue);
        sendResponse({ status: 'ok' });
      });
    });
    return true;
  }

  // 6. Limpar Toda a Fila
  if (request.action === 'LIMPAR_FILA' || request.action === 'LIMPAR_FICHA') {
    chrome.storage.local.remove(['ambiental_latest_esisla', 'ambiental_esisla_queue'], () => {
      updateBadge([]);
      sendResponse({ status: 'ok' });
    });
    return true;
  }

  // 7. Executar Preenchimento na Aba Ativa
  if (request.action === 'PREENCHER_TAB_ATIVA') {
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      if (!tabs || !tabs.length) {
        sendResponse({ status: 'error', message: 'Nenhuma aba ativa encontrada.' });
        return;
      }
      const activeTab = tabs[0];
      
      chrome.tabs.sendMessage(activeTab.id, { 
        action: 'EXEC_PREENCHIMENTO', 
        payload: request.payload 
      }, (resp) => {
        if (chrome.runtime.lastError) {
          chrome.scripting.executeScript({
            target: { tabId: activeTab.id, allFrames: true },
            files: ['content_esisla.js']
          }).then(() => {
            setTimeout(() => {
              chrome.tabs.sendMessage(activeTab.id, { 
                action: 'EXEC_PREENCHIMENTO', 
                payload: request.payload 
              }, (resp2) => {
                sendResponse(resp2 || { status: 'ok' });
              });
            }, 300);
          }).catch(err => {
            sendResponse({ 
              status: 'error', 
              message: 'Não foi possível injetar o script na aba ativa: ' + err.message 
            });
          });
        } else {
          sendResponse(resp || { status: 'ok' });
        }
      });
    });
    return true;
  }
});
