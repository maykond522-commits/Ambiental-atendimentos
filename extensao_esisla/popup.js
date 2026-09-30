// Script de controle do Popup da Extensão

document.addEventListener('DOMContentLoaded', () => {
  const cardComFicha = document.getElementById('cardComFicha');
  const cardSemFicha = document.getElementById('cardSemFicha');
  const badgeProtocol = document.getElementById('badgeProtocol');
  const badgeParecer = document.getElementById('badgeParecer');
  const cardPatient = document.getElementById('cardPatient');
  const detailCid1 = document.getElementById('detailCid1');
  const detailDias = document.getElementById('detailDias');
  const detailCid2 = document.getElementById('detailCid2');
  const btnPreencherAbaAtiva = document.getElementById('btnPreencherAbaAtiva');
  const btnColarClipboard = document.getElementById('btnColarClipboard');
  const btnLimparMemoria = document.getElementById('btnLimparMemoria');

  let currentPayload = null;

  function render(payload) {
    currentPayload = payload;
    if (payload && payload.protocolo) {
      cardComFicha.style.display = 'block';
      cardSemFicha.style.display = 'none';

      badgeProtocol.textContent = payload.protocolo;
      
      const isFav = (payload['voResult.voParecerFinal.flPfinal'] === 'F' || payload.parecer === 'FAVORÁVEL');
      badgeParecer.textContent = isFav ? 'Favorável' : 'Contrário';
      badgeParecer.className = 'badge-parecer ' + (isFav ? 'favoravel' : 'contrario');

      cardPatient.textContent = payload.servidor || payload.paciente || 'Servidor';
      
      const c1 = payload.cdCidPm || payload['voResult.voParecerFinal.cdCidPm'] || '—';
      const c2 = payload.cdCid2Pm || payload['voResult.voParecerFinal.cdCid2Pm'] || 'Não informado';
      const d = payload['voResult.voParecerFinal.qtDiasPm'] || payload.dias || '0';

      detailCid1.textContent = c1;
      detailCid2.textContent = c2;
      detailDias.textContent = d + ' dias';
    } else {
      cardComFicha.style.display = 'none';
      cardSemFicha.style.display = 'block';
    }
  }

  function carregarDoStorage() {
    chrome.storage.local.get(['ambiental_latest_esisla'], (result) => {
      render(result.ambiental_latest_esisla || null);
    });
  }

  // Preencher aba ativa
  btnPreencherAbaAtiva.addEventListener('click', () => {
    if (!currentPayload) return;
    btnPreencherAbaAtiva.disabled = true;
    btnPreencherAbaAtiva.textContent = '⏳ Preenchendo...';

    chrome.runtime.sendMessage({ 
      action: 'PREENCHER_TAB_ATIVA', 
      payload: currentPayload 
    }, (resp) => {
      if (resp && resp.success) {
        btnPreencherAbaAtiva.textContent = '✅ Sucesso!';
        setTimeout(() => window.close(), 1200);
      } else {
        btnPreencherAbaAtiva.disabled = false;
        btnPreencherAbaAtiva.textContent = '⚡ Preencher Aba do e-SISLA';
        alert((resp && resp.error) ? resp.error : 'Abra a aba do laudo no e-SISLA e tente novamente.');
      }
    });
  });

  // Colar do clipboard
  btnColarClipboard.addEventListener('click', async () => {
    try {
      const text = await navigator.clipboard.readText();
      if (!text) { alert('A área de transferência está vazia.'); return; }
      const obj = JSON.parse(text);
      if (obj && (obj.protocolo || obj.campos_esisla || obj['voMedico.parRlCat'])) {
        chrome.storage.local.set({ ambiental_latest_esisla: obj }, () => {
          render(obj);
        });
      } else {
        alert('O texto copiado não possui o formato de laudo do e-SISLA.');
      }
    } catch(err) {
      alert('Não foi possível ler a área de transferência ou o JSON é inválido: ' + err.message);
    }
  });

  // Limpar memória
  btnLimparMemoria.addEventListener('click', () => {
    if (confirm('Deseja limpar os dados do laudo ativo da extensão?')) {
      chrome.storage.local.remove(['ambiental_latest_esisla'], () => {
        render(null);
      });
    }
  });

  carregarDoStorage();
});
