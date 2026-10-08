// Content Script: Motor de Preenchimento Inteligente e-SISLA (Manifest V3)
// Desenvolvido para o Sistema Ambiental - Perícia Médica do Estado de São Paulo

(function() {
  // Evita injeção dupla na mesma janela/frame
  if (window.__AMBIENTAL_ESISLA_INJECTED__) return;
  window.__AMBIENTAL_ESISLA_INJECTED__ = true;

  console.log('[Ambiental e-SISLA Extension] Content script carregado no frame:', window.location.href);

  // ==========================================
  // 1. LOCALIZADOR ROBUSTO DE DOM / FRAMES
  // ==========================================
  function findTargetDoc() {
    // 1. Verifica no próprio documento
    if (isEsislaDoc(document)) return { doc: document, win: window };

    // 2. Procura em window.frames
    for (var i = 0; i < window.frames.length; i++) {
      try {
        var w = window.frames[i];
        if (w && isEsislaDoc(w.document)) return { doc: w.document, win: w };
      } catch(_) {}
    }

    // 3. Procura em iframes e frames do DOM
    var iframes = document.querySelectorAll('iframe, frame');
    for (var j = 0; j < iframes.length; j++) {
      try {
        var ifrDoc = iframes[j].contentDocument || (iframes[j].contentWindow && iframes[j].contentWindow.document);
        var ifrWin = iframes[j].contentWindow || window;
        if (ifrDoc && isEsislaDoc(ifrDoc)) return { doc: ifrDoc, win: ifrWin };
      } catch(_) {}
    }

    // Se nenhum iframe específico tiver os campos, retorna o documento atual como contingência
    return { doc: document, win: window };
  }

  function isEsislaDoc(d) {
    if (!d) return false;
    try {
      return !!(
        d.querySelector('textarea[name="voMedico.parRlCat"]') ||
        d.getElementById('blocoGeral') ||
        d.querySelector('input[name="fl_d_prev"]') ||
        d.querySelector('input[name*="flPfinal"]') ||
        d.getElementById('idParEdtcspf') ||
        d.querySelector('input[name="voResult.numCrm"]') ||
        d.getElementById('justificaPericia') ||
        d.getElementById('strProtocolo') ||
        d.querySelector('input[name="strProtocolo"]') ||
        d.querySelector('input[type="image"][src*="btn_Buscar"]')
      );
    } catch(_) {
      return false;
    }
  }

  function isLaudoDoc(d) {
    if (!d) return false;
    try {
      return !!(
        d.querySelector('textarea[name="voMedico.parRlCat"]') ||
        d.getElementById('blocoGeral') ||
        d.querySelector('input[name="fl_d_prev"]') ||
        d.querySelector('input[name*="flPfinal"]') ||
        d.getElementById('idParEdtcspf') ||
        d.getElementById('justificaPericia')
      );
    } catch(_) {
      return false;
    }
  }

  // ==========================================
  // 2. MOTOR DE PREENCHIMENTO OFICIAL DPME
  // ==========================================
  function executarPreenchimento(payloadObj) {
    if (!payloadObj) {
      mostrarToast('❌ Nenhuma ficha encontrada. Gere a ficha no sistema Ambiental ou cole o JSON.', 'erro');
      return { success: false, error: 'Payload vazio' };
    }

    const { doc, win } = findTargetDoc();
    var campos = payloadObj.campos_esisla || payloadObj || {};
    var preenchidos = 0;
    var camposDetalhados = [];

    function trigger(el) {
      if (!el) return;
      try {
        el.dispatchEvent(new Event('input', { bubbles: true }));
        el.dispatchEvent(new Event('change', { bubbles: true }));
        el.dispatchEvent(new Event('blur', { bubbles: true }));
      } catch(_) {}
    }

    function destacarElemento(el) {
      if (!el) return;
      try {
        el.classList.add('ambiental-filled-glow');
        setTimeout(() => el.classList.remove('ambiental-filled-glow'), 3500);
      } catch(_) {}
    }

    function setInput(sel, val, nomeAmigavel) {
      if (val === undefined || val === null || val === '') return;
      var el = (typeof sel === 'string' && sel.startsWith('#')) ? doc.getElementById(sel.slice(1)) : doc.querySelector(sel);
      if (!el && typeof sel === 'string' && !sel.startsWith('#') && !sel.includes('[')) {
        el = doc.getElementById(sel) || doc.querySelector('[name="' + sel + '"]');
      }
      if (el) {
        if (el.hasAttribute('disabled')) el.removeAttribute('disabled');
        el.disabled = false;
        el.value = val;
        trigger(el);
        destacarElemento(el);
        preenchidos++;
        if (nomeAmigavel) camposDetalhados.push(nomeAmigavel);
      }
    }

    function setRadio(name, val, id, nomeAmigavel) {
      if (!val) return;
      var el = id ? doc.getElementById(id) : null;
      if (!el) el = doc.querySelector('input[type="radio"][name="' + name + '"][value="' + val + '"]');
      if (el) {
        el.checked = true;
        try { el.click(); } catch(_) {}
        el.checked = true;
        trigger(el);
        destacarElemento(el);
        preenchidos++;
        if (nomeAmigavel) camposDetalhados.push(nomeAmigavel);
      }
    }

    function setCheckbox(name, id, checked) {
      var el = id ? doc.getElementById(id) : null;
      if (!el) el = doc.querySelector('input[type="checkbox"][name="' + name + '"]');
      if (el) {
        var shouldCheck = !!checked && checked !== '0' && checked !== 0;
        if (el.checked !== shouldCheck) {
          try { el.click(); } catch(_) { el.checked = shouldCheck; }
        }
        el.checked = shouldCheck;
        trigger(el);
        if (shouldCheck) {
          destacarElemento(el);
          preenchidos++;
        }
      }
    }

    function sanitizeText(v, max) {
      if (!v) return '';
      var s = String(v);
      if (max && s.length > max) {
        console.warn(`[Ambiental e-SISLA] Truncado para caber no limite Oracle (${max} carac.):`, s.slice(0, 30) + '...');
        return s.slice(0, max);
      }
      return s;
    }

    try {
      // 1. Textareas Principais (Limites de 2.000 / 2.500 caracteres da Oracle/Prodesp)
      setInput('textarea[name="voMedico.parRlCat"]', sanitizeText(campos['voMedico.parRlCat'], 2000), 'Queixa e Duração');
      setInput('textarea[name="voMedico.parRlAp"]', sanitizeText(campos['voMedico.parRlAp'], 2000), 'Antecedentes');
      setInput('textarea[name="voMedico.parRlHda"]', sanitizeText(campos['voMedico.parRlHda'], 2500), 'Histórico (HDA)');

      // 2. Exame Físico Geral (Textarea e 12 Checkboxes)
      var cbs = [
        { n: 'voMedico.parEdtcspf', id: 'idParEdtcspf' },
        { n: 'voMedico.parEdAc', id: 'idParEdAc' },
        { n: 'voMedico.parEdAr', id: 'idParEdAr' },
        { n: 'voMedico.parEdAHp', id: 'idParEdAHp' },
        { n: 'voMedico.parEdAd', id: 'idParEdAd' },
        { n: 'voMedico.parEdAgu', id: 'idParEdAgu' },
        { n: 'voMedico.parEdAoal', id: 'idParEdAoal' },
        { n: 'voMedico.parEdAe', id: 'idParEdAe' },
        { n: 'voMedico.parEdSn', id: 'idParEdSn' },
        { n: 'voMedico.parEdOs', id: 'idParEdOs' },
        { n: 'voMedico.parEdEm', id: 'idParEdEm' },
        { n: 'voMedico.parEdOutro', id: 'idParEdOutro' }
      ];
      var temAlgumMarcado = false;
      cbs.forEach(function(item) {
        var isChecked = !!(campos[item.n] || campos[item.id]);
        setCheckbox(item.n, item.id, isChecked);
        if (isChecked) temAlgumMarcado = true;
      });

      if (temAlgumMarcado && typeof win.exameApresentado === 'function') {
        try { win.exameApresentado(); } catch(_) {}
      }

      var exApres = doc.getElementById('idExameApres') || doc.querySelector('textarea[name="voMedico.parRlExApres"]');
      if (exApres) {
        exApres.removeAttribute('disabled');
        exApres.disabled = false;
      }
      setInput('textarea[name="voMedico.parRlExApres"]', sanitizeText(campos['voMedico.parRlExApres'], 2500), 'Exame Físico');
      setInput('#idExameApres', sanitizeText(campos['voMedico.parRlExApres'], 2500));

      // 3. Descrição das Limitações
      setInput('textarea[name="voMedico.parRlReqExComp"]', sanitizeText(campos['voMedico.parRlReqExComp'], 2500), 'Limitações');

      // 4. Médico Assistente: Conforme diretriz oficial, o CRM do médico assistente NÃO deve ser colado no e-SISLA para evitar colar o CRM da perita
      // O campo de CRM do médico assistente permanece intocado
      setInput('input[name="voResult.strNomeMedico"]', sanitizeText(campos['voResult.strNomeMedico'], 60), 'Nome Assistente');

      // 5. Pressão Arterial e Pulso
      var sis = (campos['voMedico.lgPressArterialMax'] || campos['lgPressArterialMax'] || '').toString().replace(/\D/g, '').slice(0, 3);
      var dia = (campos['voMedico.lgPressArterialMin'] || campos['lgPressArterialMin'] || '').toString().replace(/\D/g, '').slice(0, 3);
      var pul = (campos['voMedico.lgPulsacao'] || campos['lgPulsacao'] || '').toString().replace(/\D/g, '').slice(0, 3);
      setInput('input[name="voMedico.lgPressArterialMax"]', sis, 'PA Máx');
      setInput('input[name="lgPressArterialMax"]', sis);
      setInput('#sistolicaPressao', sis);
      setInput('input[name="voMedico.lgPressArterialMin"]', dia, 'PA Mín');
      setInput('input[name="lgPressArterialMin"]', dia);
      setInput('#diastolicaPressao', dia);
      setInput('input[name="voMedico.lgPulsacao"]', pul, 'Pulso');
      setInput('input[name="lgPulsacao"]', pul);
      setInput('#pulsoPressao', pul);

      // 6. Biometria (Altura com vírgula, peso, IMC)
      var alt = campos['voMedico.lgAltura'] || campos['lgAltura'] || '';
      if (alt) {
        alt = String(alt).trim().replace(/[^\d,\.]/g, '');
        if (alt.includes('.')) alt = alt.replace('.', ',');
        else if (!alt.includes(',') && alt.length >= 3) alt = alt.slice(0, 1) + ',' + alt.slice(1, 3);
        alt = alt.slice(0, 4);
      }
      var peso = (campos['voMedico.lgPeso'] || campos['lgPeso'] || '').toString().replace(/\D/g, '').slice(0, 3);
      setInput('input[name="voMedico.lgAltura"]', alt, 'Altura');
      setInput('input[name="lgAltura"]', alt);
      setInput('#alturaBiotipo', alt);
      setInput('input[name="voMedico.lgPeso"]', peso, 'Peso');
      setInput('input[name="lgPeso"]', peso);
      setInput('#pesoBiotipo', peso);
      if (typeof win.TextoIMC === 'function') {
        try { win.TextoIMC(); } catch(_) {}
      }
      if (typeof win.calcularIMC === 'function') {
        try { win.calcularIMC(); } catch(_) {}
      }

      // 7. Quesitos Oficiais DPME
      var q1 = campos['fl_d_prev'] || 'N';
      var q2 = campos['fl_limit'] || 'N';
      var q3 = campos['fl_imped'] || 'N';
      var parecerVal = campos['voResult.voParecerFinal.flPfinal'] || 'F';

      setRadio('fl_d_prev', q1, q1 === 'S' ? 'idFl_d_prevS' : 'idFl_d_prevN', 'Quesito 1');
      if (typeof win.limpaCamposQuesitos === 'function') { try { win.limpaCamposQuesitos(q1); } catch(_) {} }
      setRadio('fl_limit', q2, q2 === 'S' ? 'idFl_limitS' : 'idFl_limitN', 'Quesito 2');
      if (typeof win.limpaCamposQuesitos === 'function') { try { win.limpaCamposQuesitos(q2); } catch(_) {} }
      setRadio('fl_imped', q3, q3 === 'S' ? 'idFl_impedS' : 'idFl_impedN', 'Quesito 3');
      if (typeof win.limpaCamposQuesitos === 'function') { try { win.limpaCamposQuesitos(q3); } catch(_) {} }

      // 8. Parecer Médico-Pericial (Suporta Radio e Checkbox do e-SISLA)
      function setParecerFinal(val) {
        var isFav = (val === 'F' || val === 'FAVORÁVEL' || val === 'Favorável');
        var targetVal = isFav ? 'F' : 'C';
        var targetId = isFav ? 'decPericialF' : 'decPericialC';
        var otherId = isFav ? 'decPericialC' : 'decPericialF';
        var targetName = 'voResult.voParecerFinal.flPfinal';

        function findInput(idPref, vPref, isFavFlag) {
          var el = doc.getElementById(idPref);
          if (!el) el = doc.getElementById(isFavFlag ? 'flPfinalF' : 'flPfinalC');
          if (!el) el = doc.getElementById(isFavFlag ? 'idFlPfinalF' : 'idFlPfinalC');
          if (!el) el = doc.querySelector('input[name="' + targetName + '"][value="' + vPref + '"]');
          if (!el) el = doc.querySelector('input[name*="flPfinal"][value="' + vPref + '"]');
          if (!el) el = doc.querySelector('input[name*="decPericial"][value="' + vPref + '"]');
          if (!el) {
            var labels = doc.querySelectorAll('label, span, td, b, font');
            var searchWord = isFavFlag ? 'Favor' : 'Contr';
            for (var k = 0; k < labels.length; k++) {
              var txt = (labels[k].textContent || '').trim();
              if (txt.indexOf(searchWord) !== -1) {
                var inp = labels[k].querySelector('input') || 
                          (labels[k].htmlFor ? doc.getElementById(labels[k].htmlFor) : null) ||
                          labels[k].previousElementSibling ||
                          labels[k].nextElementSibling;
                if (inp && (inp.tagName === 'INPUT' || (inp = inp.querySelector('input')))) {
                  el = inp;
                  break;
                }
              }
            }
          }
          return el;
        }

        var targetEl = findInput(targetId, targetVal, isFav);
        var otherEl = findInput(otherId, isFav ? 'C' : 'F', !isFav);

        if (otherEl) {
          otherEl.checked = false;
          trigger(otherEl);
        }

        if (targetEl) {
          if (targetEl.hasAttribute('disabled')) targetEl.removeAttribute('disabled');
          targetEl.disabled = false;
          if (!targetEl.checked) {
            try { targetEl.click(); } catch(_) {}
          }
          targetEl.checked = true;
          trigger(targetEl);
          destacarElemento(targetEl);
          preenchidos++;
          camposDetalhados.push('Parecer ' + (isFav ? 'Favorável' : 'Contrário'));
        }

        if (typeof win.mudaSituacao === 'function') { try { win.mudaSituacao(); } catch(_) {} }
        if (typeof win.escondeCampos === 'function') { try { win.escondeCampos(targetVal); } catch(_) {} }

        if (targetEl) {
          targetEl.checked = true;
          trigger(targetEl);
        }
        if (otherEl) otherEl.checked = false;

        var bFav = doc.getElementById('blocoFavoravel');
        var bJust = doc.getElementById('blocoJustificativa');
        if (isFav) {
          if (bFav) bFav.style.display = 'block';
          if (bJust && campos['voMedico.parRlComp']) bJust.style.display = 'block';
        } else {
          if (bFav) bFav.style.display = 'none';
          if (bJust) bJust.style.display = 'block';
        }
      }
      setParecerFinal(parecerVal);

      // 9. Concessão (Dias, Início, CIDs)
      var diasSol = (campos['voResult.voParecerFinal.qtDiasPm'] || '').toString().replace(/\D/g, '').slice(0, 3);
      var dtIniSol = sanitizeText(campos['voResult.voParecerFinal.dtIniPm'], 10);
      setInput('input[name="voResult.voParecerFinal.qtDiasPm"]', diasSol, 'Dias');
      setInput('#qtDiasPm', diasSol);
      setInput('input[name="voResult.voParecerFinal.dtIniPm"]', dtIniSol, 'Data Início');
      if (typeof win.preenchePeriodo2 === 'function') {
        try { win.preenchePeriodo2(); } catch(_) {}
      }

      // CID 1
      var cid1 = sanitizeText(campos['cdCidPm'] || campos['voResult.voParecerFinal.cdCidPm'], 5);
      var descrCid1 = sanitizeText(campos['nmCidPm'] || campos['voResult.voParecerFinal.nmCidPm'], 65);
      setInput('input[name="cdCidPm"]', cid1, 'CID Principal');
      setInput('input[name="voResult.voParecerFinal.cdCidPm"]', cid1);
      setInput('#cdCidPm', cid1);
      var elNmCid1 = doc.getElementById('nmCidPm') || doc.querySelector('input[name="nmCidPm"]') || doc.querySelector('input[name="voResult.voParecerFinal.nmCidPm"]');
      if (elNmCid1) {
        elNmCid1.removeAttribute('disabled');
        elNmCid1.disabled = false;
        elNmCid1.value = descrCid1;
        trigger(elNmCid1);
        destacarElemento(elNmCid1);
      }
      setInput('#descrCidx', descrCid1);
      if (cid1 && typeof win.carregaAjaxCid === 'function') {
        try { win.carregaAjaxCid('cdCidPm', 'nmCidPm'); } catch(_) {}
      }

      // CID 2 (Secundário)
      var cid2 = sanitizeText(campos['cdCid2Pm'] || campos['voResult.voParecerFinal.cdCid2Pm'], 5);
      var descrCid2 = sanitizeText(campos['voResult.voParecerFinal.nmCidPm2'] || campos['voResult.voParecerFinal.nmCid2Pm'] || campos['nmCidPm2'], 65);
      if (cid2) {
        setInput('input[name="cdCid2Pm"]', cid2, 'CID Secundário');
        setInput('input[name="voResult.voParecerFinal.cdCid2Pm"]', cid2);
        setInput('#cdCid2Pm', cid2);
        var elNmCid2 = doc.getElementById('nmCid2Pm') || doc.querySelector('input[name="voResult.voParecerFinal.nmCidPm2"]') || doc.querySelector('input[name="voResult.voParecerFinal.nmCid2Pm"]');
        if (elNmCid2) {
          elNmCid2.removeAttribute('disabled');
          elNmCid2.disabled = false;
          elNmCid2.value = descrCid2;
          trigger(elNmCid2);
          destacarElemento(elNmCid2);
        }
        setInput('#descrCid2x', descrCid2);
        if (cid2 && typeof win.carregaAjaxCid === 'function') {
          try { win.carregaAjaxCid('cdCid2Pm', 'nmCid2Pm'); } catch(_) {}
        }
      }

      // 10. Justificativa Parecer Médico
      var elJust = doc.getElementById('justificaPericia') || doc.querySelector('textarea[name="voMedico.parRlComp"]');
      if (elJust) {
        elJust.removeAttribute('disabled');
        elJust.disabled = false;
      }
      setInput('textarea[name="voMedico.parRlComp"]', sanitizeText(campos['voMedico.parRlComp'], 2000), 'Justificativa');
      setInput('#justificaPericia', sanitizeText(campos['voMedico.parRlComp'], 2000));

      // 11. Rolagem suave para conferência médica
      var bg = doc.getElementById('blocoGeral') || doc.querySelector('fieldset') || doc.querySelector('textarea[name="voMedico.parRlCat"]');
      if (bg) {
        bg.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }

      // 12. Notificação visual de sucesso
      var proto = payloadObj.protocolo || 'Laudo';
      mostrarToast(`✅ ${proto}: ${preenchidos} campos preenchidos com sucesso! Role a página para conferir antes de concluir.`, 'sucesso');

      return { success: true, count: preenchidos };
    } catch(err) {
      console.error('[Ambiental e-SISLA] Erro durante o preenchimento:', err);
      mostrarToast('❌ Erro ao preencher campos do e-SISLA: ' + err.message, 'erro');
      return { success: false, error: err.message };
    }
  }

  // ==========================================
  // 3. WIDGET FLUTUANTE NA TELA DO E-SISLA
  // ==========================================
  // ==========================================
  // 3. WIDGET FLUTUANTE NA TELA DO E-SISLA & RECONHECIMENTO INTELIGENTE
  // ==========================================
  var activeMatchedPayload = null;
  var currentQueue = [];

  function normalizarTexto(str) {
    return String(str || '')
      .normalize('NFD')
      .replace(/[\u0300-\u036f]/g, '')
      .toLowerCase()
      .replace(/[^a-z0-9\s]/g, '')
      .trim();
  }

  function extrairIdentificacaoTela() {
    var { doc } = findTargetDoc();
    var protocolos = new Set();
    var nomes = new Set();
    var textos = [];

    function scan(d) {
      if (!d) return;
      try {
        // 1. Inputs e campos
        var inps = d.querySelectorAll('input, textarea, select');
        inps.forEach(el => {
          var n = (el.name || el.id || '').toLowerCase();
          var v = String(el.value || '').trim();
          if (/protocolo|atendimento|requerimento|laudo/.test(n) && v) {
            var m = v.match(/\d{6,12}/);
            if (m) protocolos.add(m[0]);
          }
          if (/servidor|paciente|periciado|nome/.test(n) && v && v.length >= 5 && !/crm|medico|perito|assistente/i.test(n)) {
            nomes.add(v);
          }
        });

        // 2. Células de tabelas e spans do cabeçalho
        var cells = d.querySelectorAll('td, th, span, b, div, p, font');
        cells.forEach(el => {
          var t = (el.textContent || '').trim();
          if (t.length >= 4 && t.length <= 160) {
            var mProt = t.match(/(?:protocolo|atendimento|requerimento|n[ºo])\s*[:\.]?\s*(\d{6,12})/i);
            if (mProt) protocolos.add(mProt[1]);
            
            var mNome = t.match(/(?:servidor|paciente|periciado|nome|nome\s+do\s+servidor)\s*[:\.]?\s*([A-ZÀ-Ú\s]{5,60})/i);
            if (mNome && !/perito|m[ée]dico|crm|assistente|diretor|unidade/i.test(mNome[1])) {
              nomes.add(mNome[1].trim());
            }

            if (/^\d{8,10}$/.test(t)) {
              protocolos.add(t);
            }
          }
        });

        var bodyTxt = (d.body ? d.body.innerText || d.body.textContent : '') || '';
        textos.push(bodyTxt.slice(0, 6000));
      } catch(_) {}
    }

    scan(document);
    if (doc !== document) scan(doc);

    try {
      var ifrs = document.querySelectorAll('iframe, frame');
      ifrs.forEach(ifr => {
        try {
          var ifrDoc = ifr.contentDocument || (ifr.contentWindow && ifr.contentWindow.document);
          if (ifrDoc) scan(ifrDoc);
        } catch(_) {}
      });
    } catch(_) {}

    return {
      protocolos: Array.from(protocolos),
      nomes: Array.from(nomes),
      rawText: textos.join(' ')
    };
  }

  function encontrarMatchNaTela(fila, ident) {
    if (!Array.isArray(fila) || !fila.length) return null;

    var rawLower = normalizarTexto(ident.rawText);

    // Passo 1: Busca por Protocolo (exatidão de 100%)
    for (var i = 0; i < fila.length; i++) {
      var item = fila[i];
      var protoDigits = String(item.protocolo || '').replace(/\D/g, '');
      if (protoDigits.length >= 6) {
        if (ident.protocolos.includes(protoDigits) || rawLower.includes(protoDigits)) {
          return { laudo: item, motivo: 'protocolo' };
        }
      }
    }

    // Passo 2: Busca por Nome do Servidor (exatidão de 95%)
    for (var j = 0; j < fila.length; j++) {
      var it = fila[j];
      var nomeNorm = normalizarTexto(it.servidor || it.paciente || '');
      var partes = nomeNorm.split(/\s+/).filter(w => w.length >= 3);
      if (partes.length >= 2) {
        var nomeCompletoNoTexto = rawLower.includes(nomeNorm);
        var primeiroEUltimoNoTexto = rawLower.includes(partes[0]) && rawLower.includes(partes[partes.length - 1]);
        
        var nomeNasCelulas = ident.nomes.some(n => {
          var nNorm = normalizarTexto(n);
          return nNorm.includes(nomeNorm) || (nNorm.includes(partes[0]) && nNorm.includes(partes[partes.length - 1]));
        });

        if (nomeCompletoNoTexto || (primeiroEUltimoNoTexto && (nomeNasCelulas || ident.nomes.length > 0))) {
          return { laudo: it, motivo: 'nome' };
        }
      }
    }

    return null;
  }

  function criarWidgetFlutuante() {
    if (window.top !== window && !isEsislaDoc(document)) return;
    if (document.getElementById('ambientalEsislaWidget')) return;

    var widget = document.createElement('div');
    widget.id = 'ambientalEsislaWidget';
    widget.className = 'ambiental-widget-container';
    
    widget.innerHTML = `
      <div class="ambiental-widget-pill" id="ambientalWidgetPill">
        <div class="ambiental-widget-brand" id="ambientalWidgetTrigger" title="Clique para verificar correspondência e preencher">
          <span class="ambiental-widget-bolt">⚡</span>
          <span class="ambiental-widget-title">Ambiental e-SISLA</span>
          <span class="ambiental-widget-status-dot" id="ambientalWidgetDot"></span>
        </div>
        <div class="ambiental-widget-info" id="ambientalWidgetInfo">
          <span id="ambientalWidgetProto">Analisando periciado...</span>
        </div>
        <button type="button" class="ambiental-widget-btn-fill disabled" id="ambientalWidgetBtnFill" title="Aguardando identificação do periciado" disabled>
          🔒 Bloqueado
        </button>
        <button type="button" class="ambiental-widget-btn-menu" id="ambientalWidgetBtnMenu" title="Fila de laudos do dia e opções">
          ▾
        </button>
      </div>

      <div class="ambiental-widget-dropdown" id="ambientalWidgetDropdown" style="display:none">
        <div id="ambientalQueueContainer"></div>
        <div class="ambiental-widget-menu-item" id="ambientalMenuColarClip">
          📋 Colar da Área de Transferência
        </div>
        <div class="ambiental-widget-menu-item" id="ambientalMenuColarManual">
          ✍️ Inserir JSON Manualmente
        </div>
        <div class="ambiental-widget-menu-item" id="ambientalMenuRecarregar">
          🔄 Re-escanear Periciado na Tela
        </div>
        <div class="ambiental-widget-menu-divider"></div>
        <div class="ambiental-widget-menu-item" id="ambientalMenuMinimizar">
          ➖ Minimizar Botão
        </div>
      </div>
    `;

    document.body.appendChild(widget);

    atualizarInfoWidget();

    var btnFill = document.getElementById('ambientalWidgetBtnFill');
    var btnTrigger = document.getElementById('ambientalWidgetTrigger');
    var btnMenu = document.getElementById('ambientalWidgetBtnMenu');
    var dropdown = document.getElementById('ambientalWidgetDropdown');

    btnFill.addEventListener('click', dispararPreenchimentoAtual);
    btnTrigger.addEventListener('click', () => {
      if (activeMatchedPayload) {
        dispararPreenchimentoAtual();
      } else {
        dropdown.style.display = dropdown.style.display === 'none' ? 'block' : 'none';
      }
    });

    btnMenu.addEventListener('click', (e) => {
      e.stopPropagation();
      dropdown.style.display = dropdown.style.display === 'none' ? 'block' : 'none';
    });

    document.addEventListener('click', () => {
      if (dropdown) dropdown.style.display = 'none';
    });

    document.getElementById('ambientalMenuColarClip').addEventListener('click', colarDoClipboard);
    document.getElementById('ambientalMenuColarManual').addEventListener('click', abrirModalColagemManual);
    document.getElementById('ambientalMenuRecarregar').addEventListener('click', () => {
      atualizarInfoWidget();
      mostrarToast('🔄 Tela do e-SISLA re-escaneada!', 'sucesso');
    });
    document.getElementById('ambientalMenuMinimizar').addEventListener('click', () => {
      widget.classList.toggle('minimized');
    });

    tornarArrastavel(widget);
  }

  function renderizarListaFilaNoDropdown(fila) {
    var container = document.getElementById('ambientalQueueContainer');
    if (!container) return;

    if (!fila || !fila.length) {
      container.innerHTML = `
        <div class="ambiental-widget-menu-header">
          <span>📋 Fila de Laudos do Dia (0)</span>
        </div>
        <div style="padding:10px 14px;font-size:11px;color:#94A3B8;line-height:1.35">
          Nenhuma ficha na fila.<br>No sistema Ambiental, abra a Ficha e confirme para adicionar à fila.
        </div>
        <div class="ambiental-widget-menu-divider"></div>
      `;
      return;
    }

    var htmlItens = fila.map((it, idx) => {
      var isMatch = activeMatchedPayload && String(activeMatchedPayload.protocolo || '') === String(it.protocolo || '');
      var isDone = it.status === 'preenchido';
      var pac = it.servidor || it.paciente || 'Servidor';
      return `
        <div class="ambiental-queue-item ${isMatch ? 'active-match' : ''}" data-idx="${idx}" title="Clique para selecionar este laudo manualmente">
          <div class="queue-item-row">
            <strong style="color:${isMatch ? '#00C95A' : '#0F172A'}">${it.protocolo || 'Sem prot.'}</strong>
            <span class="queue-status ${isDone ? 'preenchido' : 'pendente'}">${isDone ? '✓ Preenchido' : 'Pendente'}</span>
          </div>
          <div class="queue-item-name">${pac}</div>
        </div>
      `;
    }).join('');

    container.innerHTML = `
      <div class="ambiental-widget-menu-header">
        <span>📋 Fila do Dia (${fila.length})</span>
        <button type="button" id="btnLimparFilaDropdown" style="background:transparent;border:none;color:#EF4444;cursor:pointer;font-size:11px;font-weight:700;padding:2px 4px" title="Limpar todos os laudos da fila">🗑️ Limpar</button>
      </div>
      <div class="ambiental-queue-items-list" id="ambientalQueueList">
        ${htmlItens}
      </div>
      <div class="ambiental-widget-menu-divider"></div>
    `;

    var btnClear = document.getElementById('btnLimparFilaDropdown');
    if (btnClear) {
      btnClear.addEventListener('click', (e) => {
        e.stopPropagation();
        if (confirm('Deseja limpar todos os laudos da fila da extensão?')) {
          chrome.runtime.sendMessage({ action: 'LIMPAR_FILA' }, () => {
            atualizarInfoWidget();
          });
        }
      });
    }

    var items = container.querySelectorAll('.ambiental-queue-item');
    items.forEach(el => {
      el.addEventListener('click', (e) => {
        e.stopPropagation();
        var idx = Number(el.dataset.idx);
        if (fila[idx]) {
          selecionarLaudoManualmente(fila[idx]);
          var dropdown = document.getElementById('ambientalWidgetDropdown');
          if (dropdown) dropdown.style.display = 'none';
        }
      });
    });
  }

  var isSearchModeActive = false;
  var currentSearchCandidate = null;
  var autoFillPollingInterval = null;

  function detectarCampoPesquisaProtocolo() {
    function findInDoc(d) {
      if (!d) return null;
      try {
        var inp = d.getElementById('strProtocolo') ||
                  d.querySelector('input[name="strProtocolo"]') ||
                  d.querySelector('input[name="protocolo"]') ||
                  d.querySelector('input[name*="Protocolo"]');
        if (inp) return { input: inp, doc: d };
      } catch(_) {}
      return null;
    }

    var res = findInDoc(document);
    if (res) return res;

    // Busca em frames e iframes
    var iframes = document.querySelectorAll('iframe, frame');
    for (var i = 0; i < iframes.length; i++) {
      try {
        var idoc = iframes[i].contentDocument || (iframes[i].contentWindow && iframes[i].contentWindow.document);
        var r = findInDoc(idoc);
        if (r) return r;
      } catch(_) {}
    }

    return null;
  }

  function clicarBotaoBuscarEsisla(targetDoc) {
    function findBtn(d) {
      if (!d) return null;
      try {
        return d.querySelector('input[type="image"][src*="btn_Buscar"]') ||
               d.querySelector('input.botao_side[src*="Buscar"]') ||
               d.querySelector('input.botao_side[title="Buscar"]') ||
               d.querySelector('input[type="image"][title="Buscar"]') ||
               d.querySelector('input[src*="btn_Buscar"]') ||
               d.querySelector('input[src*="Buscar"]') ||
               d.querySelector('input[value="Buscar"]') ||
               d.querySelector('button[title="Buscar"]');
      } catch(_) {
        return null;
      }
    }

    var btn = findBtn(targetDoc || document);
    if (btn) {
      btn.click();
      return true;
    }

    var iframes = document.querySelectorAll('iframe, frame');
    for (var i = 0; i < iframes.length; i++) {
      try {
        var idoc = iframes[i].contentDocument || (iframes[i].contentWindow && iframes[i].contentWindow.document);
        var b = findBtn(idoc);
        if (b) {
          b.click();
          return true;
        }
      } catch(_) {}
    }

    return false;
  }

  function renderizarAssistenteBuscaInline(input, candidate, doc) {
    if (!input || !candidate) return;
    var d = doc || document;

    var existing = d.getElementById('ambientalSearchInlineCard');
    var proto = candidate.protocolo || 'Sem Prot.';
    var pac = candidate.servidor || candidate.paciente || 'Servidor';

    if (existing) {
      var protoStrong = existing.querySelector('strong');
      var pacSmall = existing.querySelector('small');
      if (protoStrong) protoStrong.textContent = `Próximo da Fila: Prot. ${proto}`;
      if (pacSmall) pacSmall.textContent = pac;
      return;
    }

    var card = d.createElement('div');
    card.id = 'ambientalSearchInlineCard';
    card.className = 'ambiental-search-inline-card';
    card.innerHTML = `
      <div class="search-inline-info">
        <span class="search-inline-bolt">⚡</span>
        <div>
          <strong>Próximo da Fila: Prot. ${proto}</strong>
          <small>${pac}</small>
        </div>
      </div>
      <button type="button" class="btn-search-entrar-preencher" id="btnSearchInlineEntrarPreencher" title="Preenche o protocolo, pesquisa e preenche o laudo automaticamente ao abrir">
        ⚡ Entrar e Preencher
      </button>
    `;

    var parentP = input.closest('p') || input.parentElement;
    if (parentP && parentP.parentElement) {
      parentP.parentElement.insertBefore(card, parentP.nextSibling);
    } else if (input.parentElement) {
      input.parentElement.appendChild(card);
    }

    var btn = card.querySelector('#btnSearchInlineEntrarPreencher');
    if (btn) {
      btn.addEventListener('click', (e) => {
        e.preventDefault();
        e.stopPropagation();
        acionarEntrarEPreencher(candidate, { input: input, doc: d });
      });
    }
  }

  function acionarEntrarEPreencher(payload, searchContext) {
    if (!payload || !payload.protocolo) {
      mostrarToast('❌ Nenhum protocolo válido encontrado para busca.', 'erro');
      return;
    }

    var protoDigits = String(payload.protocolo).replace(/\D/g, '');
    var pac = payload.servidor || payload.paciente || 'Servidor';

    // 1. Preenche o campo de protocolo na tela
    var sc = searchContext || detectarCampoPesquisaProtocolo();
    if (sc && sc.input) {
      sc.input.focus();
      sc.input.value = protoDigits;
      try {
        sc.input.dispatchEvent(new Event('input', { bubbles: true }));
        sc.input.dispatchEvent(new Event('change', { bubbles: true }));
        sc.input.dispatchEvent(new KeyboardEvent('keyup', { bubbles: true }));
      } catch(_) {}
      try {
        sc.input.classList.add('ambiental-filled-glow');
        setTimeout(() => sc.input.classList.remove('ambiental-filled-glow'), 2000);
      } catch(_) {}
    }

    // 2. Salva a diretiva para preenchimento automático assim que a ficha abrir
    chrome.storage.local.set({
      ambiental_auto_fill_target: {
        protocolo: protoDigits,
        servidor: pac,
        payload: payload,
        timestamp: Date.now()
      }
    }, () => {
      mostrarToast(`⏳ Protocolo ${protoDigits} preenchido. Clicando em Buscar...`, 'info');

      // 3. Clica no botão Buscar após 160ms
      setTimeout(() => {
        var clicou = clicarBotaoBuscarEsisla(sc ? sc.doc : document);
        if (!clicou && sc && sc.input && sc.input.form) {
          sc.input.form.submit();
        }

        // Inicia observador para preencher assim que o formulário do laudo aparecer
        iniciarObservadorAutoFill();
      }, 160);
    });
  }

  function verificarAutoFillPendente() {
    chrome.storage.local.get(['ambiental_auto_fill_target'], (res) => {
      var target = res.ambiental_auto_fill_target;
      if (!target || !target.payload) return;

      if (Date.now() - (target.timestamp || 0) > 120000) {
        chrome.storage.local.remove(['ambiental_auto_fill_target']);
        return;
      }

      var { doc } = findTargetDoc();
      if (isLaudoDoc(doc)) {
        if (autoFillPollingInterval) {
          clearInterval(autoFillPollingInterval);
          autoFillPollingInterval = null;
        }

        chrome.storage.local.remove(['ambiental_auto_fill_target'], () => {
          var execRes = executarPreenchimento(target.payload);
          if (execRes && execRes.success) {
            chrome.runtime.sendMessage({
              action: 'MARCAR_FICHA_PREENCHIDA',
              protocolo: target.protocolo,
              servidor: target.servidor
            });
            mostrarToast(`🎉 Atendimento de ${target.servidor} (Prot. ${target.protocolo}) preenchido com sucesso!`, 'sucesso');
            atualizarInfoWidget();
          }
        });
      }
    });
  }

  function iniciarObservadorAutoFill() {
    if (autoFillPollingInterval) clearInterval(autoFillPollingInterval);
    var attempts = 0;
    autoFillPollingInterval = setInterval(() => {
      attempts++;
      verificarAutoFillPendente();
      if (attempts >= 40) {
        clearInterval(autoFillPollingInterval);
        autoFillPollingInterval = null;
      }
    }, 300);
  }

  function selecionarLaudoManualmente(item) {
    if (!item) return;
    activeMatchedPayload = item;
    var btnFill = document.getElementById('ambientalWidgetBtnFill');
    var protoEl = document.getElementById('ambientalWidgetProto');
    var dot = document.getElementById('ambientalWidgetDot');
    var pac = item.servidor || item.paciente || 'Servidor';
    var pacShort = pac.length > 18 ? pac.slice(0, 18) + '…' : pac;

    var sc = detectarCampoPesquisaProtocolo();
    if (sc && sc.input) {
      currentSearchCandidate = item;
      isSearchModeActive = true;
      renderizarAssistenteBuscaInline(sc.input, item, sc.doc);
      if (protoEl) {
        protoEl.innerHTML = `<span style="color:#0284C7;font-weight:800">🔍 Prot. ${item.protocolo}</span> · ${pacShort}`;
        protoEl.title = `Laudo de ${pac} (${item.protocolo}) selecionado para busca. Clique em Entrar e Preencher!`;
      }
      if (dot) {
        dot.style.background = '#0284C7';
        dot.style.boxShadow = '0 0 8px rgba(2, 132, 199, 0.6)';
      }
      if (btnFill) {
        btnFill.disabled = false;
        btnFill.classList.remove('disabled');
        btnFill.classList.add('search-mode');
        btnFill.style.opacity = '1';
        btnFill.style.pointerEvents = 'auto';
        btnFill.innerHTML = '⚡ Entrar e Preencher';
        btnFill.title = `Preencher protocolo ${item.protocolo}, clicar em Buscar e preencher a ficha ao abrir`;
      }
      mostrarToast(`⚡ Laudo de ${pac} (${item.protocolo}) selecionado para busca. Clique em Entrar e Preencher!`, 'info');
      return;
    }

    if (protoEl) {
      protoEl.innerHTML = `<span style="color:#0284C7;font-weight:800">📋 ${item.protocolo}</span> · ${pacShort}`;
      protoEl.title = `Laudo selecionado manualmente: ${pac} (${item.protocolo})`;
    }
    if (dot) {
      dot.style.background = '#0284C7';
      dot.style.boxShadow = '0 0 8px rgba(2, 132, 199, 0.6)';
    }
    if (btnFill) {
      btnFill.disabled = false;
      btnFill.classList.remove('disabled');
      btnFill.classList.remove('search-mode');
      btnFill.style.opacity = '1';
      btnFill.style.pointerEvents = 'auto';
      btnFill.innerHTML = '⚡ Preencher';
      btnFill.title = `Preencher laudo de ${pac}`;
    }
    mostrarToast(`⚡ Laudo de ${pac} (${item.protocolo}) selecionado manualmente. Clique em Preencher!`, 'sucesso');
  }

  function atualizarInfoWidget() {
    chrome.storage.local.get(['ambiental_esisla_queue', 'ambiental_latest_esisla'], (result) => {
      var fila = Array.isArray(result.ambiental_esisla_queue) ? result.ambiental_esisla_queue : [];
      if (!fila.length && result.ambiental_latest_esisla) {
        fila = [result.ambiental_latest_esisla];
      }
      currentQueue = fila;

      var ident = extrairIdentificacaoTela();
      var matchResult = encontrarMatchNaTela(fila, ident);

      var protoEl = document.getElementById('ambientalWidgetProto');
      var dot = document.getElementById('ambientalWidgetDot');
      var btnFill = document.getElementById('ambientalWidgetBtnFill');

      renderizarListaFilaNoDropdown(fila);

      // CASO 1: Encontrou tela de laudo com match de paciente/protocolo
      if (matchResult && matchResult.laudo) {
        isSearchModeActive = false;
        currentSearchCandidate = null;
        activeMatchedPayload = matchResult.laudo;
        var laudo = matchResult.laudo;
        var proto = laudo.protocolo || '';
        var pac = laudo.servidor || laudo.paciente || 'Servidor';
        var pacShort = pac.length > 18 ? pac.slice(0, 18) + '…' : pac;

        if (protoEl) {
          protoEl.innerHTML = `<span style="color:#00C95A;font-weight:800">✓ ${proto}</span> · ${pacShort}`;
          protoEl.title = `Periciado identificado na tela: ${pac} (Prot. ${proto}) [via ${matchResult.motivo}]`;
        }
        if (dot) {
          dot.style.background = '#00E676';
          dot.style.boxShadow = '0 0 8px #00E676';
        }
        if (btnFill) {
          btnFill.disabled = false;
          btnFill.classList.remove('disabled');
          btnFill.classList.remove('search-mode');
          btnFill.style.opacity = '1';
          btnFill.style.pointerEvents = 'auto';
          btnFill.innerHTML = '⚡ Preencher';
          btnFill.title = `Clique para preencher o laudo de ${pac}`;
        }
        return;
      }

      // CASO 2: Tela de busca de protocolo (strProtocolo + btn_Buscar)
      var sc = detectarCampoPesquisaProtocolo();
      if (sc && sc.input && fila.length > 0) {
        var candidate = currentSearchCandidate || fila.find(f => f.status !== 'preenchido') || fila[0];
        currentSearchCandidate = candidate;
        isSearchModeActive = true;
        activeMatchedPayload = null;

        var candProto = candidate.protocolo || '';
        var candPac = candidate.servidor || candidate.paciente || 'Servidor';
        var candShort = candPac.length > 18 ? candPac.slice(0, 18) + '…' : candPac;

        renderizarAssistenteBuscaInline(sc.input, candidate, sc.doc);

        if (protoEl) {
          protoEl.innerHTML = `<span style="color:#0284C7;font-weight:800">🔍 Prot. ${candProto}</span> · ${candShort}`;
          protoEl.title = `Pronto para buscar e preencher: ${candPac} (Prot. ${candProto}). Clique em 'Entrar e Preencher'!`;
        }
        if (dot) {
          dot.style.background = '#0284C7';
          dot.style.boxShadow = '0 0 8px rgba(2, 132, 199, 0.6)';
        }
        if (btnFill) {
          btnFill.disabled = false;
          btnFill.classList.remove('disabled');
          btnFill.classList.add('search-mode');
          btnFill.style.opacity = '1';
          btnFill.style.pointerEvents = 'auto';
          btnFill.innerHTML = '⚡ Entrar e Preencher';
          btnFill.title = `Preencher protocolo ${candProto}, clicar em Buscar e preencher a ficha ao abrir!`;
        }
        return;
      }

      // CASO 3: Sem match / bloqueado
      isSearchModeActive = false;
      currentSearchCandidate = null;
      activeMatchedPayload = null;
      if (dot) dot.style.boxShadow = 'none';

      if (btnFill) {
        btnFill.disabled = true;
        btnFill.classList.add('disabled');
        btnFill.classList.remove('search-mode');
        btnFill.style.opacity = '0.55';
        btnFill.style.pointerEvents = 'none';
        btnFill.innerHTML = '🔒 Bloqueado';
        btnFill.title = 'Abra no e-SISLA a tela de busca ou a tela do periciado que possui laudo na fila para liberar o preenchimento.';
      }

      if (protoEl) {
        if (fila.length > 0) {
          protoEl.innerHTML = `<span style="color:#F59E0B">⚠️ Periciado não bate</span> <small style="color:#94A3B8">(${fila.length} na fila)</small>`;
          protoEl.title = `${fila.length} laudo(s) disponível(is) na fila, mas nenhum coincide com o protocolo/nome desta tela. Abra a tela de busca ou selecione manualmente no menu ▾.`;
          if (dot) dot.style.background = '#F59E0B';
        } else {
          protoEl.textContent = 'Fila vazia (gere no Ambiental)';
          protoEl.title = 'Gere a ficha de um periciado no sistema Ambiental para adicionar à fila.';
          if (dot) dot.style.background = '#94A3B8';
        }
      }
    });
  }

  function dispararPreenchimentoAtual() {
    if (isSearchModeActive && currentSearchCandidate) {
      var sc = detectarCampoPesquisaProtocolo();
      acionarEntrarEPreencher(currentSearchCandidate, sc);
      return;
    }

    if (!activeMatchedPayload) {
      mostrarToast('🔒 Nenhum periciado correspondente identificado na tela do e-SISLA. Selecione um laudo no menu ▾.', 'erro');
      return;
    }
    var res = executarPreenchimento(activeMatchedPayload);
    if (res && res.success) {
      chrome.runtime.sendMessage({
        action: 'MARCAR_FICHA_PREENCHIDA',
        protocolo: activeMatchedPayload.protocolo,
        servidor: activeMatchedPayload.servidor || activeMatchedPayload.paciente
      });
      atualizarInfoWidget();
    }
  }

  function colarDoClipboard() {
    if (navigator.clipboard && navigator.clipboard.readText) {
      navigator.clipboard.readText().then(text => {
        try {
          var parsed = JSON.parse(text);
          if (parsed && (parsed.campos_esisla || parsed['voMedico.parRlCat'] || parsed.protocolo)) {
            chrome.runtime.sendMessage({ action: 'ADICIONAR_FICHA_FILA', payload: parsed }, () => {
              executarPreenchimento(parsed);
              atualizarInfoWidget();
            });
          } else {
            abrirModalColagemManual();
          }
        } catch(_) {
          abrirModalColagemManual();
        }
      }).catch(() => {
        abrirModalColagemManual();
      });
    } else {
      abrirModalColagemManual();
    }
  }

  function abrirModalColagemManual() {
    var old = document.getElementById('ambientalPasteModal');
    if (old) old.remove();

    var modal = document.createElement('div');
    modal.id = 'ambientalPasteModal';
    modal.className = 'ambiental-paste-modal-backdrop';
    modal.innerHTML = `
      <div class="ambiental-paste-dialog">
        <div class="ambiental-paste-head">
          <div style="display:flex;align-items:center;gap:8px">
            <span style="font-size:20px">⚡</span>
            <strong>Preencher e-SISLA com JSON</strong>
          </div>
          <button type="button" class="ambiental-paste-close" id="ambientalPasteClose">✕</button>
        </div>
        <div class="ambiental-paste-body">
          <p>Cole o JSON do laudo gerado no sistema <strong>Ambiental</strong> abaixo e clique em <em>Preencher Agora</em>:</p>
          <textarea id="ambientalPasteText" placeholder='Cole aqui com Ctrl + V {"protocolo": ...}'></textarea>
        </div>
        <div class="ambiental-paste-foot">
          <button type="button" class="ambiental-btn-sec" id="ambientalPasteCancel">Cancelar</button>
          <button type="button" class="ambiental-btn-pri" id="ambientalPasteExec">⚡ Preencher Agora</button>
        </div>
      </div>
    `;

    document.body.appendChild(modal);

    var ta = document.getElementById('ambientalPasteText');
    ta.focus();

    function fechar() { modal.remove(); }
    document.getElementById('ambientalPasteClose').onclick = fechar;
    document.getElementById('ambientalPasteCancel').onclick = fechar;

    document.getElementById('ambientalPasteExec').onclick = () => {
      var val = ta.value.trim();
      if (!val) { alert('Por favor, cole o JSON do laudo.'); return; }
      try {
        var obj = JSON.parse(val);
        chrome.runtime.sendMessage({ action: 'SALVAR_FICHA', payload: obj });
        executarPreenchimento(obj);
        atualizarInfoWidget();
        fechar();
      } catch(e) {
        alert('JSON inválido: ' + e.message);
      }
    };
  }

  function mostrarToast(msg, tipo) {
    var old = document.getElementById('ambientalToast');
    if (old) old.remove();

    var toast = document.createElement('div');
    toast.id = 'ambientalToast';
    toast.className = 'ambiental-floating-toast ' + (tipo || 'sucesso');
    toast.textContent = msg;

    document.body.appendChild(toast);

    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translate(-50%, -15px)';
      setTimeout(() => toast.remove(), 400);
    }, 5500);
  }

  function tornarArrastavel(el) {
    var isDragging = false;
    var currentX, currentY, initialX, initialY;
    var pill = el.querySelector('#ambientalWidgetPill');

    pill.addEventListener('mousedown', dragStart);

    function dragStart(e) {
      if (e.target.closest('button') || e.target.closest('.ambiental-widget-dropdown')) return;
      initialX = e.clientX - el.offsetLeft;
      initialY = e.clientY - el.offsetTop;
      isDragging = true;
      document.addEventListener('mousemove', drag);
      document.addEventListener('mouseup', dragEnd);
    }

    function drag(e) {
      if (!isDragging) return;
      e.preventDefault();
      currentX = e.clientX - initialX;
      currentY = e.clientY - initialY;
      
      // Restringe aos limites da janela
      currentX = Math.max(10, Math.min(window.innerWidth - el.offsetWidth - 10, currentX));
      currentY = Math.max(10, Math.min(window.innerHeight - el.offsetHeight - 10, currentY));

      el.style.left = currentX + 'px';
      el.style.top = currentY + 'px';
      el.style.right = 'auto';
    }

    function dragEnd() {
      isDragging = false;
      document.removeEventListener('mousemove', drag);
      document.removeEventListener('mouseup', dragEnd);
    }
  }

  // ==========================================
  // 4. LISTENER PARA MENSAGENS EXTERNAS / POPUP
  // ==========================================
  chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === 'EXEC_PREENCHIMENTO') {
      var res = executarPreenchimento(request.payload);
      sendResponse(res);
      return true;
    }
    if (request.action === 'PING') {
      sendResponse({ status: 'alive' });
      return true;
    }
  });

  // Escuta atualizações de storage para atualizar o widget instantaneamente
  chrome.storage.onChanged.addListener((changes, areaName) => {
    if (areaName === 'local') {
      if (changes.ambiental_latest_esisla || changes.ambiental_esisla_queue) {
        atualizarInfoWidget();
      }
      if (changes.ambiental_auto_fill_target && changes.ambiental_auto_fill_target.newValue) {
        verificarAutoFillPendente();
        iniciarObservadorAutoFill();
      }
    }
  });

  // Re-escaneia periodicamente a tela para detectar trocas de abas ou formulários no e-SISLA sem reload
  setInterval(() => {
    atualizarInfoWidget();
    verificarAutoFillPendente();
  }, 3000);

  function inicializarModuloEsisla() {
    criarWidgetFlutuante();
    verificarAutoFillPendente();
    iniciarObservadorAutoFill();
  }

  // Inicializa o widget flutuante e verificação de auto-fill quando o DOM estiver pronto
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', inicializarModuloEsisla);
  } else {
    inicializarModuloEsisla();
  }

})();
