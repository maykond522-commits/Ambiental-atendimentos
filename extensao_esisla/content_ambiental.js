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

  function sanitizarNomeServidor(rawName) {
    const s = String(rawName || '').trim();
    if (!s || s.length > 90) return '';
    if (/^(?:de\s+\d+\s+anos|relatou\b|n[ãa]o\s+readaptad|com\s+queixa\b|servidor(?:\(a\))?\s+de\s+\d+)/i.test(s)) return '';
    if (/\b(?:relatou\s+n[ãa]o\s+ser\s+readaptad|com\s+queixa\s+de|em\s+acompanhamento)\b/i.test(s)) return '';
    return s;
  }

  function obterNomeServidorSeguro(payload) {
    const subTxt = (document.getElementById('doctorEsislaSub')?.textContent || document.getElementById('esislaSub')?.textContent || '');
    const subPacMatch = subTxt.match(/·\s*([^·]+)\s*·/);
    const domNome = sanitizarNomeServidor(subPacMatch ? subPacMatch[1].trim() : '');
    const payloadNome = sanitizarNomeServidor(payload?.servidor || payload?.paciente || '');
    if (payloadNome && payloadNome !== 'Servidor') return payloadNome;
    if (domNome && domNome !== 'Servidor(a)' && domNome !== 'Servidor') return domNome;

    // Tenta encontrar em cards da agenda ou cabeçalhos visíveis pelo protocolo
    const proto = payload?.protocolo;
    if (proto) {
      const cards = Array.from(document.querySelectorAll('.agenda-item-card'));
      for (const card of cards) {
        if (card.textContent.includes(proto)) {
          const nameEl = card.querySelector('.agenda-patient-name');
          if (nameEl && nameEl.textContent.trim()) {
            const clean = sanitizarNomeServidor(nameEl.textContent.trim());
            if (clean) return clean;
          }
        }
      }
    }
    return payloadNome || domNome || 'Servidor';
  }

  // Exibe o card interativo dando ao médico a ESCOLHA de adicionar ou não aquela ficha à fila
  function exibirOpcaoCopiarParaFila(payload) {
    if (!payload) return;
    const pac = obterNomeServidorSeguro(payload);
    payload.servidor = pac;
    payload.paciente = pac;
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

    const cid = payload.cdCidPm || payload['voResult.voParecerFinal.cdCidPm'] || '';
    const dias = payload['voResult.voParecerFinal.qtDiasPm'] || payload.dias || '';

    const prompt = document.createElement('div');
    prompt.id = 'ambientalExtensionQueuePrompt';
    prompt.className = 'ambiental-ext-queue-prompt';
    prompt.innerHTML = `
      <div style="display:flex;align-items:center;justify-content:space-between;gap:8px;margin-bottom:6px">
        <div style="display:flex;align-items:center;gap:6px;min-width:0;flex:1">
          <span style="font-size:15px;line-height:1;flex-shrink:0">⚡</span>
          <strong style="font-size:12px;color:#0F172A;white-space:nowrap;overflow:hidden;text-overflow:ellipsis" title="${pac.replace(/"/g, '&quot;')}">${pac}</strong>
        </div>
        <button type="button" class="btn-ext-prompt-close" style="background:transparent;border:none;color:#94A3B8;cursor:pointer;font-size:14px;padding:0 2px;line-height:1;flex-shrink:0" title="Fechar">✕</button>
      </div>

      <div style="font-size:11px;color:#475569;margin-bottom:8px;display:flex;align-items:center;gap:6px;flex-wrap:wrap">
        <span>Prot: <strong style="color:#0369A1">${proto}</strong></span>
        ${cid ? `<span>· CID: <strong>${cid}</strong>${dias ? ` (${dias}d)` : ''}</span>` : ''}
      </div>

      <div style="display:flex;align-items:center;justify-content:flex-end;gap:6px">
        <button type="button" class="btn-ext-prompt-ignore" style="background:#FFFFFF;border:1px solid #CBD5E1;color:#64748B;font-size:10.5px;font-weight:700;padding:4px 8px;border-radius:5px;cursor:pointer">
          Agora Não
        </button>
        <button type="button" class="btn-ext-prompt-add" style="background:linear-gradient(135deg, #0284C7 0%, #0369A1 100%);color:#FFFFFF;border:none;font-size:10.5px;font-weight:800;padding:4.5px 10px;border-radius:5px;cursor:pointer;box-shadow:0 1px 4px rgba(2,132,199,0.25)">
          ⚡ Adicionar à Fila
        </button>
      </div>
    `;

    prompt.style.cssText = `
      position: fixed;
      bottom: 16px;
      right: 16px;
      width: min(300px, 88vw);
      background: #FFFFFF;
      border: 1.5px solid #0284C7;
      border-left: 4px solid #0284C7;
      border-radius: 10px;
      padding: 9px 12px;
      box-shadow: 0 8px 24px rgba(15, 23, 42, 0.14);
      z-index: 2147483647;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      animation: ambientalPromptSlideUp 0.25s cubic-bezier(0.16, 1, 0.3, 1);
      transition: opacity 0.2s, transform 0.2s;
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
    const pac = obterNomeServidorSeguro(payload);
    const proto = payload.protocolo || '';

    toast.innerHTML = `
      <div style="display:flex;align-items:center;gap:10px;">
        <span style="font-size:20px;line-height:1">✅</span>
        <div style="min-width:0;flex:1">
          <strong style="display:block;font-size:12.5px;color:#0F172A">Adicionado à Fila e-SISLA!</strong>
          <span style="display:block;font-size:11px;color:#475569;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:260px">${pac} ${proto ? `(Prot. ${proto})` : ''}</span>
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
      if (p) {
        const pac = obterNomeServidorSeguro(p);
        p.servidor = pac;
        p.paciente = pac;
      }
      if (event.data.forceQueue || event.data.autoAdd) {
        salvarNaFila(p);
      } else {
        exibirOpcaoCopiarParaFila(p);
      }
    }
  });

  // Extrai payload a partir do texto ou da tela médica caso o localStorage ainda não tenha sincronizado
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

    const subTxt = (document.getElementById('doctorEsislaSub')?.textContent || document.getElementById('esislaSub')?.textContent || '');
    const protoMatch = str.match(/^(?:Atendimento|Protocolo)\s*[:#]\s*([A-Za-z0-9_\-\.]+)/im);
    const subMatch = subTxt.match(/Atendimento\s+([^·\s]+)/i);
    const protocolo = protoMatch ? protoMatch[1].trim() : (subMatch ? subMatch[1].trim() : 'ATD_' + Date.now());

    const subPacMatch = subTxt.match(/·\s*([^·]+)\s*·/i);
    const domNome = sanitizarNomeServidor(subPacMatch ? subPacMatch[1].trim() : '');
    const pacMatch = str.match(/^(?:Nome(?:\s+do\s+(?:Servidor|Periciado))?|Periciado|Paciente)\s*:\s*([^\n\r]+)/im);
    const textNome = sanitizarNomeServidor(pacMatch ? pacMatch[1].trim() : '');
    const servidor = (domNome && domNome !== 'Servidor(a)' ? domNome : '') || textNome || domNome || 'Servidor';

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

  function extrairPayloadDoDOM() {
    const docEl = document.getElementById('doctorEsislaText');
    const admEl = document.getElementById('esislaText');
    const txt = (docEl && docEl.value) ? docEl.value : (admEl && admEl.value ? admEl.value : '');
    if (txt && txt.trim().length > 30) {
      return extrairPayloadDeTextoEsisla(txt);
    }
    return null;
  }

  // 2. Monitora mudanças no localStorage ou no DOM da página (contingência quando gerada)
  function checkLocalStorage() {
    try {
      let parsed = null;
      const raw = localStorage.getItem('ambiental_esisla_current_payload');
      if (raw) {
        try { parsed = JSON.parse(raw); } catch(_) {}
      }
      if (!parsed || !parsed.protocolo || !parsed.campos_esisla) {
        parsed = extrairPayloadDoDOM();
      }
      if (parsed && (parsed.timestamp || parsed.protocolo)) {
        const syncKey = String(parsed.timestamp || parsed.protocolo);
        if (!window._lastSyncTime || window._lastSyncTime !== syncKey) {
          window._lastSyncTime = syncKey;
          exibirOpcaoCopiarParaFila(parsed);
        }
      }
    } catch(_) {}
  }

  setInterval(checkLocalStorage, 1500);

  // 3. Clique em botões de copiar explícito no sistema Ambiental (Médicos e Adm): adiciona diretamente à fila
  document.addEventListener('click', (e) => {
    const btn = e.target.closest(
      '#copyEsislaBtn, #btnCopyEsislaJson, #btnCopiarLaudoEsisla, #esislaCopyHeaderBtn, ' +
      '#btnDoctorCopyEsislaFull, #btnDoctorSendToExtension, .btn-doctor-esisla-copy, ' +
      '.btn-copy-card-block, .btn-copy-mini, .top-btn-esisla, ' +
      '[onclick*="copiarLaudoEsisla"], [onclick*="copyEsisla"], [onclick*="copyEsislaJson"], ' +
      '[onclick*="copyDoctorEsisla"], [onclick*="enviarDoctorEsisla"]'
    );
    if (btn) {
      setTimeout(() => {
        try {
          let parsed = null;
          const raw = localStorage.getItem('ambiental_esisla_current_payload');
          if (raw) {
            try { parsed = JSON.parse(raw); } catch(_) {}
          }
          if (!parsed || !parsed.campos_esisla || !parsed.protocolo) {
            parsed = extrairPayloadDoDOM();
          }
          if (parsed && (parsed.campos_esisla || parsed.protocolo)) {
            salvarNaFila(parsed);
          }
        } catch(_) {}
      }, 150);
    }
  }, true);

  // 4. Se o usuário copiar JSON ou texto da ficha e-SISLA para a área de transferência
  window.addEventListener('copy', () => {
    setTimeout(() => {
      try {
        let parsed = null;
        const raw = localStorage.getItem('ambiental_esisla_current_payload');
        if (raw) {
          try { parsed = JSON.parse(raw); } catch(_) {}
        }
        if (!parsed || !parsed.campos_esisla || !parsed.protocolo) {
          parsed = extrairPayloadDoDOM();
        }
        if (parsed && (parsed.campos_esisla || parsed.protocolo)) {
          salvarNaFila(parsed);
        }
      } catch(_) {}
    }, 200);
  });

  // 5. Recepção de Agenda Capturada no e-SISLA para Importação 1-Clique no Ambiental
  try {
    chrome.runtime.onMessage.addListener((msg) => {
      if (msg && msg.action === 'AGENDA_ESISLA_DISPONIVEL' && msg.payload) {
        exibirPromptImportarAgenda(msg.payload);
      }
    });
  } catch(_) {}

  function exibirPromptImportarAgenda(payload) {
    if (!payload || !payload.itens || !payload.itens.length) return;
    const existing = document.getElementById('ambientalAgendaImportPrompt');
    if (existing) existing.remove();

    const count = payload.itens.length;
    const prompt = document.createElement('div');
    prompt.id = 'ambientalAgendaImportPrompt';
    prompt.style.cssText = `
      position: fixed;
      bottom: 24px;
      right: 24px;
      z-index: 999999;
      background: #FFFFFF;
      border: 1.5px solid #0284C7;
      border-radius: 12px;
      padding: 14px 16px;
      box-shadow: 0 10px 30px rgba(2, 132, 199, 0.25);
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      max-width: 380px;
      animation: slideUp 0.25s ease-out;
    `;
    prompt.innerHTML = `
      <div style="display:flex;align-items:flex-start;justify-content:space-between;gap:10px;margin-bottom:8px">
        <div style="display:flex;align-items:center;gap:8px">
          <span style="font-size:22px">📅</span>
          <div>
            <strong style="font-size:13.5px;color:#0F172A;display:block">Agenda do e-SISLA Capturada!</strong>
            <span style="font-size:11.5px;color:#0284C7;font-weight:700">${count} periciado(s) identificados na grade</span>
          </div>
        </div>
        <button type="button" id="btnFecharPromptAgenda" style="background:transparent;border:none;color:#94A3B8;cursor:pointer;font-size:16px;padding:2px 6px">✕</button>
      </div>
      <div style="font-size:11.5px;color:#475569;margin-bottom:12px;line-height:1.4">
        Deseja importar automaticamente estes agendamentos para a sua <strong>Agenda Médica</strong> no sistema Ambiental?
      </div>
      <div style="display:flex;align-items:center;justify-content:flex-end;gap:8px">
        <button type="button" id="btnIgnorarAgenda" style="background:#FFFFFF;border:1px solid #CBD5E1;color:#64748B;font-size:11.5px;font-weight:700;padding:6px 12px;border-radius:7px;cursor:pointer">
          Dispensar
        </button>
        <button type="button" id="btnExecutarImportarAgenda" style="background:linear-gradient(135deg, #0284C7 0%, #0369A1 100%);color:#FFFFFF;border:none;font-size:11.5px;font-weight:800;padding:6.5px 14px;border-radius:7px;cursor:pointer;box-shadow:0 2px 6px rgba(2,132,199,0.3)">
          ⚡ Importar para Minha Agenda
        </button>
      </div>
    `;

    document.body.appendChild(prompt);

    document.getElementById('btnFecharPromptAgenda').addEventListener('click', () => prompt.remove());
    document.getElementById('btnIgnorarAgenda').addEventListener('click', () => prompt.remove());
    document.getElementById('btnExecutarImportarAgenda').addEventListener('click', async () => {
      const btn = document.getElementById('btnExecutarImportarAgenda');
      btn.disabled = true;
      btn.innerText = 'Importando...';
      try {
        if (window.AmbientalAPI?.esisla?.importarAgenda) {
          await window.AmbientalAPI.esisla.importarAgenda(payload);
        } else {
          await fetch('/api/esisla/importar-agenda', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
          });
        }
        prompt.innerHTML = `
          <div style="display:flex;align-items:center;gap:8px;color:#16A34A;font-weight:800;font-size:13px">
            <span>✅</span> ${count} agendamentos importados com sucesso!
          </div>
        `;
        setTimeout(() => prompt.remove(), 2500);
        if (typeof window.carregarAgenda === 'function') window.carregarAgenda();
        if (typeof window.carregarAtendimentos === 'function') window.carregarAtendimentos();
      } catch(err) {
        alert('Erro ao importar agenda: ' + (err.message || 'Falha na requisição'));
        prompt.remove();
      }
    });
  }

})();
