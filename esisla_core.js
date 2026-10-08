/**
 * Ambiental e-SISLA Core - Motor Clínico e Pericial Compartilhado
 * Padronização de Regras de Ouro do DPME, Sistemas Clínicos e Validações
 */

(function(global) {
  'use strict';

  // 1. Mapeamento oficial dos 12 sistemas/áreas clínicas do e-SISLA
  const MAPA_NOMES_ESISLA = {
    'aoal': 'Aparelho Osteomuscular e Tecido Conjuntivo',
    'em': 'Exame Mental',
    'ac': 'Aparelho Circulatório',
    'ar': 'Aparelho Respiratório',
    'tcspf': 'Tecido celular subcutâneo Pele e Fâneros',
    'ad': 'Aparelho Digestivo',
    'agu': 'Aparelho Geniturinário',
    'ahp': 'Aparelho Hemolinfopoiético',
    'ae': 'Aparelho Endócrino',
    'sn': 'Sistema Nervoso',
    'os': 'Órgãos dos Sentidos',
    'outro': 'Outros'
  };

  // 2. Detecção inteligente de sistema único para preenchimento de exame físico
  function detectarSistemaExameFisico(st, aux, texto, cidCode) {
    const fullObj = (typeof window !== 'undefined' && window.currentDetailFull) || {};
    const fullPayload = fullObj.payload || {};
    const fullAux = fullPayload.aux || fullObj.aux || {};

    const exTipo = String(
      st?.exameFisicoTipo || aux?.exameFisicoTipo ||
      st?.agilExameFisicoTipo || aux?.agilExameFisicoTipo ||
      st?.exame_fisico_tipo || aux?.exame_fisico_tipo ||
      fullPayload?.exameFisicoTipo || fullPayload?.agilExameFisicoTipo ||
      fullAux?.exameFisicoTipo || fullAux?.agilExameFisicoTipo ||
      fullObj?.exameFisicoTipo || fullObj?.exame_fisico_tipo ||
      ''
    ).trim().toLowerCase();

    const outrosSub = String(
      st?.outrosSubtipo || aux?.outrosSubtipo ||
      st?.areaExameClinico || aux?.areaExameClinico ||
      st?.outros_subtipo || aux?.outros_subtipo ||
      st?.area_exame_clinico || aux?.area_exame_clinico ||
      fullPayload?.outrosSubtipo || fullPayload?.areaExameClinico ||
      fullAux?.outrosSubtipo || fullAux?.areaExameClinico ||
      fullObj?.outrosSubtipo || fullObj?.outros_subtipo ||
      fullObj?.areaExameClinico || fullObj?.area_exame_clinico ||
      ''
    ).trim().toLowerCase();

    // 1. Subtipos selecionados quando a opção "Outros" foi detalhada pelo médico
    if (outrosSub.includes('geral') || outrosSub === 'e outros' || outrosSub === 'outros') return 'outro';
    if (outrosSub.includes('osteomuscular') || outrosSub.includes('ortop')) return 'aoal';
    if (outrosSub.includes('mental') || outrosSub.includes('psiqui')) return 'em';
    if (outrosSub.includes('circulat') || outrosSub.includes('cardio')) return 'ac';
    if (outrosSub.includes('respirat') || outrosSub.includes('pulmon')) return 'ar';
    if (outrosSub.includes('pele') || outrosSub.includes('fânero') || outrosSub.includes('fanero') || outrosSub.includes('subcut') || outrosSub.includes('dermat')) return 'tcspf';
    if (outrosSub.includes('digest') || outrosSub.includes('gastr')) return 'ad';
    if (outrosSub.includes('genit') || outrosSub.includes('urin') || outrosSub.includes('renal')) return 'agu';
    if (outrosSub.includes('hemolin') || outrosSub.includes('hemat')) return 'ahp';
    if (outrosSub.includes('endocrin') || outrosSub.includes('metabol') || outrosSub.includes('diabet')) return 'ae';
    if (outrosSub.includes('nervoso') || outrosSub.includes('neurol')) return 'sn';
    if (outrosSub.includes('sentidos') || outrosSub.includes('oftalm') || outrosSub.includes('otol')) return 'os';

    // 2. Precedência da seleção principal do médico em "Tipo de exame físico / mental"
    if (exTipo === 'exame mental' || (exTipo.includes('mental') && !exTipo.includes('físic'))) {
      return 'em';
    }
    if (exTipo.includes('osteomuscular') || exTipo.includes('conjutivo') || exTipo.includes('conjuntivo')) {
      return 'aoal';
    }
    if (exTipo.includes('geral') || exTipo === 'outros' || exTipo === 'e outros' || outrosSub === 'e outros' || outrosSub === 'outros' || exTipo.startsWith('outro')) {
      return 'outro';
    }
    if (exTipo.includes('circulat') || exTipo.includes('cardio')) return 'ac';
    if (exTipo.includes('respirat') || exTipo.includes('pulmon')) return 'ar';
    if (exTipo.includes('pele') || exTipo.includes('fânero') || exTipo.includes('subcut')) return 'tcspf';
    if (exTipo.includes('digest') || exTipo.includes('gastr')) return 'ad';
    if (exTipo.includes('genit') || exTipo.includes('urin')) return 'agu';
    if (exTipo.includes('hemolin') || exTipo.includes('hemat')) return 'ahp';
    if (exTipo.includes('endocrin') || exTipo.includes('metabol')) return 'ae';
    if (exTipo.includes('nervoso') || exTipo.includes('neurol')) return 'sn';
    if (exTipo.includes('sentidos') || exTipo.includes('oftalm') || exTipo.includes('otol')) return 'os';

    // 3. Fallback inteligente baseado no código CID-10
    const cUpper = String(cidCode || st?.cid || aux?.cid || '').trim().toUpperCase();
    if (cUpper) {
      if (cUpper.startsWith('F')) return 'em';
      if (cUpper.startsWith('M')) return 'aoal';
      if (cUpper.startsWith('I')) return 'ac';
      if (cUpper.startsWith('J')) return 'ar';
      if (cUpper.startsWith('L')) return 'tcspf';
      if (cUpper.startsWith('K')) return 'ad';
      if (cUpper.startsWith('N')) return 'agu';
      if (cUpper.startsWith('D5') || cUpper.startsWith('D6') || cUpper.startsWith('D7')) return 'ahp';
      if (cUpper.startsWith('E')) return 'ae';
      if (cUpper.startsWith('G')) return 'sn';
      if (cUpper.startsWith('H')) return 'os';
      if (cUpper.startsWith('S') || cUpper.startsWith('T')) return 'aoal';
    }

    return 'outro';
  }

  // 3. Sanitização de texto e truncamento seguro
  function sanitizarTexto(t, maxLen) {
    if (t === null || t === undefined) return '';
    let s = String(t).trim();
    if (maxLen && s.length > maxLen) {
      s = s.slice(0, maxLen).trim();
    }
    return s;
  }

  // 4. Verificação de conformidade jurídica DPME (Regras de Ouro)
  function validarConformidadeEsisla(dataObj) {
    const msgs = [];
    let hasCritical = false;

    if (!dataObj) return { valido: true, msgs: [], hasCritical: false };

    // Incoerências jurídicas
    if (dataObj.inconsistencias_juridicas && dataObj.inconsistencias_juridicas.length > 0) {
      hasCritical = true;
      msgs.push(`🚫 <strong>Incoerência Jurídica DPME:</strong> ${dataObj.inconsistencias_juridicas.join(' ')}`);
    }

    // Limites de 2.000 caracteres
    if (dataObj.campos_excedidos && dataObj.campos_excedidos.length > 0) {
      hasCritical = true;
      const lista = dataObj.campos_excedidos.map(c => `<strong>${c.nome}</strong> (${c.tamanho} carac.)`).join(', ');
      msgs.push(`📏 <strong>Campos excedem 2.000 caracteres:</strong> ${lista}`);
    }

    // Regra da Junta Médica (> 90 ou 180 dias)
    if (dataObj.alerta_junta) {
      msgs.push(`🏛️ <strong>Regra de Afastamento:</strong> ${dataObj.alerta_junta}`);
    }

    return {
      valido: !hasCritical,
      hasCritical,
      msgs
    };
  }

  // Exportação para o escopo global
  const EsislaCore = {
    MAPA_NOMES_ESISLA,
    detectarSistemaExameFisico,
    sanitizarTexto,
    validarConformidadeEsisla
  };

  if (typeof window !== 'undefined') {
    window.EsislaCore = EsislaCore;
    window.MAPA_NOMES_ESISLA = MAPA_NOMES_ESISLA;
  }
  global.EsislaCore = EsislaCore;
  global.MAPA_NOMES_ESISLA = MAPA_NOMES_ESISLA;

})(typeof window !== 'undefined' ? window : this);
