// Background Service Worker - Ambiental e-SISLA AutoFill (Manifest V3)

chrome.runtime.onInstalled.addListener(() => {
  console.log('[Ambiental e-SISLA] Extensão instalada e pronta para uso.');
});

// Atualiza o badge do ícone quando houver uma nova ficha disponível
chrome.storage.onChanged.addListener((changes, areaName) => {
  if (areaName === 'local' && changes.ambiental_latest_esisla) {
    const val = changes.ambiental_latest_esisla.newValue;
    if (val && val.protocolo) {
      chrome.action.setBadgeText({ text: '✓' });
      chrome.action.setBadgeBackgroundColor({ color: '#00C95A' });
      chrome.action.setTitle({
        title: `Ambiental e-SISLA: Laudo pronto para preenchimento (${val.protocolo})`
      });
    } else {
      chrome.action.setBadgeText({ text: '' });
      chrome.action.setTitle({ title: 'Ambiental ⚡ e-SISLA AutoFill' });
    }
  }
});

// Receptor de mensagens
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'SALVAR_FICHA') {
    chrome.storage.local.set({ ambiental_latest_esisla: request.payload }, () => {
      chrome.action.setBadgeText({ text: '✓' });
      chrome.action.setBadgeBackgroundColor({ color: '#00C95A' });
      sendResponse({ status: 'ok' });
    });
    return true;
  }

  if (request.action === 'OBTER_FICHA') {
    chrome.storage.local.get(['ambiental_latest_esisla'], (result) => {
      sendResponse({ payload: result.ambiental_latest_esisla || null });
    });
    return true;
  }

  if (request.action === 'LIMPAR_FICHA') {
    chrome.storage.local.remove(['ambiental_latest_esisla'], () => {
      chrome.action.setBadgeText({ text: '' });
      sendResponse({ status: 'ok' });
    });
    return true;
  }

  if (request.action === 'PREENCHER_TAB_ATIVA') {
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      if (!tabs || !tabs.length) {
        sendResponse({ status: 'error', message: 'Nenhuma aba ativa encontrada.' });
        return;
      }
      const activeTab = tabs[0];
      
      // Envia mensagem direta para o content_script da aba
      chrome.tabs.sendMessage(activeTab.id, { 
        action: 'EXEC_PREENCHIMENTO', 
        payload: request.payload 
      }, (resp) => {
        if (chrome.runtime.lastError) {
          // Se o content script não respondeu, tenta injetar os scripts dinamicamente
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
