// Script de controle do Popup da Extensão (Buffer e Fila Inteligente)

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
  const statusQueueBadge = document.getElementById('statusQueueBadge');
  const sectionQueue = document.getElementById('sectionQueue');
  const queueCount = document.getElementById('queueCount');
  const queueList = document.getElementById('queueList');
  const btnLimparFila = document.getElementById('btnLimparFila');

  let currentPayload = null;
  let currentQueue = [];

  function renderCard(payload) {
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
      cardSemFicha.style.display = currentQueue.length === 0 ? 'block' : 'none';
    }
  }

  function renderFila(fila) {
    currentQueue = Array.isArray(fila) ? fila : [];

    if (currentQueue.length > 0) {
      sectionQueue.style.display = 'block';
      queueCount.textContent = currentQueue.length;
      statusQueueBadge.textContent = `${currentQueue.length} na fila`;
      statusQueueBadge.style.background = 'rgba(0, 230, 118, 0.25)';

      queueList.innerHTML = currentQueue.map((it, idx) => {
        const isSelected = currentPayload && String(currentPayload.protocolo || '') === String(it.protocolo || '');
        const isDone = it.status === 'preenchido';
        const pac = it.servidor || it.paciente || 'Servidor';
        return `
          <div class="popup-queue-item ${isSelected ? 'selected' : ''}" data-idx="${idx}" title="Clique para ver os detalhes e selecionar">
            <div class="popup-queue-info">
              <div class="popup-queue-proto-row">
                <span class="popup-queue-proto">#${it.protocolo || 'Sem prot.'}</span>
                <span class="popup-queue-status ${isDone ? 'preenchido' : 'pendente'}">${isDone ? '✓ Preenchido' : 'Pendente'}</span>
              </div>
              <div class="popup-queue-name">${pac}</div>
            </div>
            <button type="button" class="btn-remove-queue-item" data-remove="${idx}" title="Remover da fila">✕</button>
          </div>
        `;
      }).join('');

      // Eventos de clique na lista da fila
      queueList.querySelectorAll('.popup-queue-item').forEach(el => {
        el.addEventListener('click', (e) => {
          if (e.target.closest('.btn-remove-queue-item')) return;
          const idx = Number(el.dataset.idx);
          if (currentQueue[idx]) {
            renderCard(currentQueue[idx]);
            renderFila(currentQueue);
          }
        });
      });

      queueList.querySelectorAll('.btn-remove-queue-item').forEach(btn => {
        btn.addEventListener('click', (e) => {
          e.stopPropagation();
          const idx = Number(btn.dataset.remove);
          const item = currentQueue[idx];
          if (item) {
            chrome.runtime.sendMessage({ 
              action: 'REMOVER_FICHA_FILA', 
              protocolo: item.protocolo,
              servidor: item.servidor || item.paciente
            }, () => {
              carregarDoStorage();
            });
          }
        });
      });
    } else {
      sectionQueue.style.display = 'none';
      statusQueueBadge.textContent = '0 na fila';
      statusQueueBadge.style.background = 'rgba(255, 255, 255, 0.15)';
      if (!currentPayload) {
        cardSemFicha.style.display = 'block';
      }
    }
  }

  function carregarDoStorage() {
    chrome.storage.local.get(['ambiental_latest_esisla', 'ambiental_esisla_queue'], (result) => {
      const fila = Array.isArray(result.ambiental_esisla_queue) ? result.ambiental_esisla_queue : [];
      let ativo = result.ambiental_latest_esisla || (fila.length > 0 ? fila[0] : null);
      renderCard(ativo);
      renderFila(fila);
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
        chrome.runtime.sendMessage({
          action: 'MARCAR_FICHA_PREENCHIDA',
          protocolo: currentPayload.protocolo,
          servidor: currentPayload.servidor || currentPayload.paciente
        }, () => {
          setTimeout(() => {
            carregarDoStorage();
            btnPreencherAbaAtiva.disabled = false;
            btnPreencherAbaAtiva.textContent = '⚡ Preencher Aba do e-SISLA';
          }, 800);
        });
      } else {
        btnPreencherAbaAtiva.disabled = false;
        btnPreencherAbaAtiva.textContent = '⚡ Preencher Aba do e-SISLA';
        alert((resp && resp.error) ? resp.error : 'Abra a aba do laudo no e-SISLA e tente novamente.');
      }
    });
  });

  // Limpar toda a fila
  if (btnLimparFila) {
    btnLimparFila.addEventListener('click', () => {
      if (confirm('Deseja limpar todos os laudos da fila do dia?')) {
        chrome.runtime.sendMessage({ action: 'LIMPAR_FILA' }, () => {
          carregarDoStorage();
        });
      }
    });
  }

  // Colar do clipboard
  btnColarClipboard.addEventListener('click', async () => {
    try {
      const text = await navigator.clipboard.readText();
      if (!text) { alert('A área de transferência está vazia.'); return; }
      const obj = JSON.parse(text);
      if (obj && (obj.protocolo || obj.campos_esisla || obj['voMedico.parRlCat'])) {
        chrome.runtime.sendMessage({ action: 'ADICIONAR_FICHA_FILA', payload: obj }, () => {
          carregarDoStorage();
        });
      } else {
        alert('O texto copiado não possui o formato de laudo do e-SISLA.');
      }
    } catch(err) {
      alert('Não foi possível ler a área de transferência ou o JSON é inválido: ' + err.message);
    }
  });

  carregarDoStorage();
});
