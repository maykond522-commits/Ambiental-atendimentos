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

  function sanitizarNomeServidor(rawName) {
    const s = String(rawName || '').trim();
    if (!s || s.length > 90) return '';
    if (/^(?:de\s+\d+\s+anos|relatou\b|n[ãa]o\s+readaptad|com\s+queixa\b|servidor(?:\(a\))?\s+de\s+\d+)/i.test(s)) return '';
    if (/\b(?:relatou\s+n[ãa]o\s+ser\s+readaptad|com\s+queixa\s+de|em\s+acompanhamento)\b/i.test(s)) return '';
    return s;
  }

  function renderCard(payload) {
    currentPayload = payload;
    if (payload && payload.protocolo) {
      cardComFicha.style.display = 'block';
      cardSemFicha.style.display = 'none';

      badgeProtocol.textContent = payload.protocolo;
      
      const isFav = (payload['voResult.voParecerFinal.flPfinal'] === 'F' || payload.parecer === 'FAVORÁVEL');
      badgeParecer.textContent = isFav ? 'Favorável' : 'Contrário';
      badgeParecer.className = 'badge-parecer ' + (isFav ? 'favoravel' : 'contrario');

      const pac = sanitizarNomeServidor(payload.servidor || payload.paciente) || 'Servidor';
      cardPatient.textContent = pac;
      cardPatient.title = pac;
      
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
        const pac = sanitizarNomeServidor(it.servidor || it.paciente) || 'Servidor';
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

  // Extrai campos estruturados a partir do texto formatado da Ficha e-Sisla (Portal Médico / Adm)
  function extrairPayloadDeTextoEsisla(rawText) {
    if (!rawText || typeof rawText !== 'string') return null;
    const str = rawText.replace(/\r/g, '');
    if (str.length < 30) return null;

    function extrair(texto, inis, fims) {
      const arrIni = Array.isArray(inis) ? inis : [inis];
      let posIni = -1;
      let matchedIni = '';
      for (const i of arrIni) {
        const idx = texto.indexOf(i);
        if (idx !== -1 && (posIni === -1 || idx < posIni)) {
          posIni = idx;
          matchedIni = i;
        }
      }
      if (posIni === -1) return '';
      const start = posIni + matchedIni.length;
      if (!fims) return texto.slice(start).trim();
      const arrFim = Array.isArray(fims) ? fims : [fims];
      let posFim = -1;
      for (const f of arrFim) {
        const idx = texto.indexOf(f, start);
        if (idx !== -1 && (posFim === -1 || idx < posFim)) {
          posFim = idx;
        }
      }
      if (posFim === -1) return texto.slice(start).trim();
      return texto.slice(start, posFim).trim();
    }

    const protoMatch = str.match(/^(?:Atendimento|Protocolo)\s*[:#]\s*([A-Za-z0-9_\-\.]+)/im);
    const protocolo = protoMatch ? protoMatch[1].trim() : 'ATD_' + Date.now();
    const pacMatch = str.match(/^(?:Nome(?:\s+do\s+(?:Servidor|Periciado))?|Periciado|Paciente)\s*:\s*([^\n\r]+)/im);
    const servidor = sanitizarNomeServidor(pacMatch ? pacMatch[1].trim() : '') || 'Servidor';

    const queixa = extrair(str, ['(*) Queixa e Duração:', '(*)Queixa e Duração:', '(*) Queixa e Duração', 'Queixa e Duração:'], ['Antecedentes Mórbidos:', 'Antecedentes Mórbidos', '(*) Antecedentes']);
    const antecedentes = extrair(str, ['Antecedentes Mórbidos:', 'Antecedentes Mórbidos', '(*) Antecedentes'], ['Atestado/Relatório/Exames Complementares:', 'Atestado/Relatório:', 'Atestado / Relatório', 'Atestado', '(*) Exame Físico', '(*)Exame Físico']);
    const atestado = extrair(str, ['Atestado/Relatório/Exames Complementares:', 'Atestado/Relatório:', 'Atestado / Relatório / Exames Complementares:', 'Atestado / Relatório', 'Atestados:'], ['Pressão Arterial', 'Sistólica', 'Altura:', '(*) Exame Físico Geral', '(*)Exame Físico Geral', 'Exame Físico Geral', '(*) Exame Físico']) || 'Em anexo.';
    const exameFisico = extrair(str, ['(*) Exame Físico Geral:', '(*)Exame Físico Geral:', '(*) Exame Físico Geral', 'Exame Físico Geral:'], ['Descrição das Alterações Clínicas', 'Descrição das Alterações', '(*) Descrição da(s) Limitação', '(*)Descrição da(s) Limitação']);
    const limitacoes = extrair(str, ['(*)Descrição da(s) Limitação(ções) Física(s) e/ou Mental(is) encontrada(s):', '(*) Descrição da(s) Limitação(ções) Física(s) e/ou Mental(is) encontrada(s):', '(*) Descrição da(s) Limitação(ções) Física(s) e/ou Mental(is):', '(*)Descrição da(s) Limitação', '(*) Descrição da(s) Limitação', 'Descrição da(s) Limitação:'], ['(*) Parecer Médico:', '(*)Parecer Médico:', '(*) Parecer Médico', 'Parecer Médico:']);

    const parecerStr = extrair(str, ['(*) Parecer Médico:', '(*)Parecer Médico:', 'Parecer Médico:'], ['Nº Dias:', 'Nº Dias', 'Dias:', 'Data Início:']);
    const isContrario = /CONTR[ÁA]RIO/i.test(parecerStr) || /PARECER:\s*CONTR[ÁA]RIO/i.test(str);
    const flPfinal = isContrario ? 'C' : 'F';

    let dias = extrair(str, ['Nº Dias:', 'Nº Dias', 'Dias Concedidos:', 'Dias:'], ['Data Início:', 'Data Início', 'CID 10:']);
    dias = dias.replace(/\D/g, '');
    if (flPfinal === 'C') dias = '0';
    else if (!dias || dias === '0') dias = '1';

    let dtIni = extrair(str, ['Data Início:', 'Data Início'], ['CID 10:', 'CID 10', 'CID:', 'Descrição:']);
    dtIni = dtIni.split('\n')[0].trim();

    let cid1 = extrair(str, ['CID 10 Principal:', 'CID 10:', 'CID 10', 'CID:'], ['Descrição:', 'Descrição', 'CID 10 Secundário:']);
    const mCid1 = cid1.match(/[A-Za-z]\d{2}(?:\.\d{1,2})?/);
    cid1 = mCid1 ? mCid1[0].toUpperCase() : '';

    let descrCid1 = extrair(str, ['Descrição:', 'Descrição'], ['CID 10 Secundário:', 'CID 10 Secundário', '(*) Resposta aos Quesitos', '(*) Justificativa']);
    descrCid1 = descrCid1.split('\n')[0].trim();

    let cid2 = extrair(str, ['CID 10 Secundário:', 'CID Secundário:'], ['Descrição Secundária:', '(*) Resposta aos Quesitos', '(*) Justificativa']);
    const mCid2 = cid2.match(/[A-Za-z]\d{2}(?:\.\d{1,2})?/);
    cid2 = mCid2 ? mCid2[0].toUpperCase() : '';

    let descrCid2 = extrair(str, ['Descrição Secundária:'], ['(*) Resposta aos Quesitos', '(*) Justificativa']);
    descrCid2 = descrCid2.split('\n')[0].trim();

    const q1Sim = /1\)\s*H[áa]\s*doen[çc]a[^\n]*\bSIM\b/i.test(str);
    const q2Sim = /2\)\s*A\(s\)\s*doen[çc]a[^\n]*\bSIM\b/i.test(str);
    const q3Sim = /3\)\s*A\(s\)\s*limita[çc][^\n]*\bSIM\b/i.test(str);

    const fl_d_prev = q1Sim ? 'S' : (flPfinal === 'C' ? 'S' : 'S');
    const fl_limit = q2Sim ? 'S' : (flPfinal === 'C' ? 'N' : 'S');
    const fl_imped = q3Sim ? 'S' : (flPfinal === 'C' ? 'N' : 'S');

    const justif = extrair(str, ['(*) Justificativa Parecer Médico:', '(*) Justificativa Parecer Final:', 'Justificativa:']);

    const paSis = (str.match(/Sist[óo]lica(?:\s*\(mmHg\))?[:\s]*(\d+)/i) || [])[1] || '';
    const paDia = (str.match(/Diast[óo]lica(?:\s*\(mmHg\))?[:\s]*(\d+)/i) || [])[1] || '';
    const pulso = (str.match(/Pulso(?:\s*\(bpm\))?[:\s]*(\d+)/i) || [])[1] || '';
    const altRaw = (str.match(/Altura[:\s]*([\d,\.]+)/i) || [])[1] || '';
    const pesoRaw = (str.match(/Peso[:\s]*(\d+)/i) || [])[1] || '';

    const cb = {
      'voMedico.parEdtcspf': /TCSPF|Tecido Celular Subcutâneo/i.test(str),
      'voMedico.parEdAc': /Aparelho Circulatório/i.test(str),
      'voMedico.parEdAr': /Aparelho Respiratório/i.test(str),
      'voMedico.parEdAHp': /Aparelho Hemolinfopoético/i.test(str),
      'voMedico.parEdAd': /Aparelho Digestivo/i.test(str),
      'voMedico.parEdAgu': /Aparelho Geniturinário/i.test(str),
      'voMedico.parEdAoal': /Órgãos dos Sentidos/i.test(str),
      'voMedico.parEdAe': /Aparelho Endócrino/i.test(str),
      'voMedico.parEdSn': /Sistema Nervoso/i.test(str),
      'voMedico.parEdOs': /Osteoarticular/i.test(str),
      'voMedico.parEdEm': /Estado Mental/i.test(str),
      'voMedico.parEdOutro': /Outros/i.test(str)
    };
    if (!Object.values(cb).some(Boolean) && exameFisico) {
      cb['voMedico.parEdOutro'] = true;
    }

    const camposEsisla = {
      'voMedico.parRlCat': queixa,
      'voMedico.parRlAp': antecedentes || 'Nega',
      'voMedico.parRlHda': atestado || 'Em anexo.',
      'voMedico.parRlExApres': exameFisico,
      'voMedico.parRlReqExComp': limitacoes,
      'fl_d_prev': fl_d_prev,
      'fl_limit': fl_limit,
      'fl_imped': fl_imped,
      'voResult.voParecerFinal.flPfinal': flPfinal,
      'voResult.voParecerFinal.qtDiasPm': dias,
      'voResult.voParecerFinal.dtIniPm': dtIni,
      'cdCidPm': cid1,
      'nmCidPm': descrCid1,
      'cdCid2Pm': cid2,
      'voResult.voParecerFinal.nmCidPm2': descrCid2,
      'voResult.voParecerFinal.cdCidPm': cid1,
      'voResult.voParecerFinal.nmCidPm': descrCid1,
      'voResult.voParecerFinal.cdCid2Pm': cid2,
      'voResult.voParecerFinal.nmCid2Pm': descrCid2,
      'voMedico.parRlComp': justif,
      'voMedico.lgPressArterialMax': paSis,
      'voMedico.lgPressArterialMin': paDia,
      'voMedico.lgPulsacao': pulso,
      'voMedico.lgAltura': altRaw,
      'voMedico.lgPeso': pesoRaw,
      ...cb
    };

    return {
      protocolo,
      servidor,
      paciente: servidor,
      ...camposEsisla,
      campos_esisla: camposEsisla,
      timestamp: new Date().toISOString()
    };
  }

  // Colar do clipboard (suporta JSON estruturado ou Texto puro da Ficha do Médico/Admin)
  btnColarClipboard.addEventListener('click', async () => {
    try {
      const text = await navigator.clipboard.readText();
      if (!text || !text.trim()) { alert('A área de transferência está vazia.'); return; }
      
      let obj = null;
      try {
        obj = JSON.parse(text);
      } catch(_) {
        obj = extrairPayloadDeTextoEsisla(text);
      }

      if (obj && (obj.protocolo || obj.campos_esisla || obj['voMedico.parRlCat'] || obj['voResult.voParecerFinal.flPfinal'])) {
        chrome.runtime.sendMessage({ action: 'ADICIONAR_FICHA_FILA', payload: obj }, () => {
          carregarDoStorage();
        });
      } else {
        alert('O texto copiado não possui o formato de laudo do e-SISLA.');
      }
    } catch(err) {
      alert('Não foi possível ler a área de transferência ou o formato é inválido: ' + err.message);
    }
  });

  carregarDoStorage();
});
