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
  function criarWidgetFlutuante() {
    // Apenas na janela principal ou no frame que contiver a barra de navegação/topo
    if (window.top !== window && !isEsislaDoc(document)) return;
    if (document.getElementById('ambientalEsislaWidget')) return;

    var widget = document.createElement('div');
    widget.id = 'ambientalEsislaWidget';
    widget.className = 'ambiental-widget-container';
    
    widget.innerHTML = `
      <div class="ambiental-widget-pill" id="ambientalWidgetPill">
        <div class="ambiental-widget-brand" id="ambientalWidgetTrigger" title="Clique para preencher a ficha do laudo">
          <span class="ambiental-widget-bolt">⚡</span>
          <span class="ambiental-widget-title">Ambiental e-SISLA</span>
          <span class="ambiental-widget-status-dot" id="ambientalWidgetDot"></span>
        </div>
        <div class="ambiental-widget-info" id="ambientalWidgetInfo">
          <span id="ambientalWidgetProto">Aguardando laudo...</span>
        </div>
        <button type="button" class="ambiental-widget-btn-fill" id="ambientalWidgetBtnFill" title="Preencher todos os campos do e-SISLA">
          ⚡ Preencher
        </button>
        <button type="button" class="ambiental-widget-btn-menu" id="ambientalWidgetBtnMenu" title="Mais opções (Colar JSON, Histórico)">
          ▾
        </button>
      </div>

      <div class="ambiental-widget-dropdown" id="ambientalWidgetDropdown" style="display:none">
        <div class="ambiental-widget-menu-item" id="ambientalMenuColarClip">
          📋 Colar da Área de Transferência
        </div>
        <div class="ambiental-widget-menu-item" id="ambientalMenuColarManual">
          ✍️ Inserir JSON Manualmente
        </div>
        <div class="ambiental-widget-menu-item" id="ambientalMenuRecarregar">
          🔄 Buscar Última Ficha do Ambiental
        </div>
        <div class="ambiental-widget-menu-divider"></div>
        <div class="ambiental-widget-menu-item" id="ambientalMenuMinimizar">
          ➖ Minimizar Botão
        </div>
      </div>
    `;

    document.body.appendChild(widget);

    // Atualiza estado do widget
    atualizarInfoWidget();

    // Event Listeners
    var btnFill = document.getElementById('ambientalWidgetBtnFill');
    var btnTrigger = document.getElementById('ambientalWidgetTrigger');
    var btnMenu = document.getElementById('ambientalWidgetBtnMenu');
    var dropdown = document.getElementById('ambientalWidgetDropdown');

    btnFill.addEventListener('click', dispararPreenchimentoAtual);
    btnTrigger.addEventListener('click', dispararPreenchimentoAtual);

    btnMenu.addEventListener('click', (e) => {
      e.stopPropagation();
      dropdown.style.display = dropdown.style.display === 'none' ? 'block' : 'none';
    });

    document.addEventListener('click', () => {
      if (dropdown) dropdown.style.display = 'none';
    });

    document.getElementById('ambientalMenuColarClip').addEventListener('click', colarDoClipboard);
    document.getElementById('ambientalMenuColarManual').addEventListener('click', abrirModalColagemManual);
    document.getElementById('ambientalMenuRecarregar').addEventListener('click', atualizarInfoWidget);
    document.getElementById('ambientalMenuMinimizar').addEventListener('click', () => {
      widget.classList.toggle('minimized');
    });

    // Torna o widget arrastável pela tela
    tornarArrastavel(widget);
  }

  function atualizarInfoWidget() {
    chrome.storage.local.get(['ambiental_latest_esisla'], (result) => {
      var payload = result.ambiental_latest_esisla;
      var protoEl = document.getElementById('ambientalWidgetProto');
      var dot = document.getElementById('ambientalWidgetDot');
      var btnFill = document.getElementById('ambientalWidgetBtnFill');

      if (payload && payload.protocolo) {
        var proto = payload.protocolo;
        var pac = payload.servidor || payload.paciente || '';
        if (pac.length > 15) pac = pac.slice(0, 15) + '...';
        if (protoEl) protoEl.textContent = `${proto} ${pac ? '· ' + pac : ''}`;
        if (dot) dot.style.background = '#00E676';
        if (btnFill) {
          btnFill.disabled = false;
          btnFill.style.opacity = '1';
        }
      } else {
        if (protoEl) protoEl.textContent = 'Nenhum laudo pronto';
        if (dot) dot.style.background = '#94A3B8';
      }
    });
  }

  function dispararPreenchimentoAtual() {
    chrome.storage.local.get(['ambiental_latest_esisla'], (result) => {
      var payload = result.ambiental_latest_esisla;
      if (payload) {
        executarPreenchimento(payload);
      } else {
        colarDoClipboard();
      }
    });
  }

  function colarDoClipboard() {
    if (navigator.clipboard && navigator.clipboard.readText) {
      navigator.clipboard.readText().then(text => {
        try {
          var parsed = JSON.parse(text);
          if (parsed && (parsed.campos_esisla || parsed['voMedico.parRlCat'] || parsed.protocolo)) {
            // Salva na memória da extensão também
            chrome.runtime.sendMessage({ action: 'SALVAR_FICHA', payload: parsed });
            executarPreenchimento(parsed);
            atualizarInfoWidget();
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
    if (areaName === 'local' && changes.ambiental_latest_esisla) {
      atualizarInfoWidget();
    }
  });

  // Inicializa o widget flutuante quando o DOM estiver pronto
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', criarWidgetFlutuante);
  } else {
    criarWidgetFlutuante();
  }

})();
