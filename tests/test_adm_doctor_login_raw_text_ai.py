# -*- coding: utf-8 -*-
"""
Validação da regra de negócio:
1. Ao importar o e-SISLA, mantém o preenchimento de campos cadastrais específicos.
2. Se houver anotações no campo 'Texto Bruto (Anotações do Médico e/ou Dados do Sistema)',
   o texto é considerado AFIRMAÇÃO DO MÉDICO PERITO e a IA preenche os demais campos clínicos
   (queixa, exame físico, limitações, parecer, justificativa), deixando-os formais e robustos,
   sem acrescentar nada.
3. Habilitado exclusivamente para ADM ao entrar em login médico.
"""
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parent.parent
APP_PY = (ROOT / "app.py").read_text(encoding="utf-8")
ATTENDANCE_HTML = (ROOT / "ambiental_avaliacao_medica_lts_cid_assistente.html").read_text(encoding="utf-8")

def test_raw_text_prompt_affirmation_and_strict_fidelity():
    # 1. Validação do prompt de IA em app.py
    assert 'DIRETRIZ FUNDAMENTAL:' in APP_PY
    assert 'AFIRMAÇÃO DIRETA DO MÉDICO PERITO' in APP_PY
    assert 'ESTILO DE REDAÇÃO - FORMAL E ROBUSTO:' in APP_PY
    assert 'REGRA DE FIDELIDADE FÁTICA RIGOROSA (SEM ACRESCENTAR NADA):' in APP_PY
    assert 'NÃO INVENTE fatos clínicos' in APP_PY

def test_backend_auth_adm_in_doctor_login():
    # 2. Validação no endpoint /api/ai/preencher-ficha
    assert 'is_adm_in_doctor_login = (real_role == "Administrador") or (user_role == "Administrador") or is_impersonating' in APP_PY
    assert 'O preenchimento automático de campos clínicos via IA a partir do Texto Bruto é habilitado apenas para Administradores ao entrar em login médico.' in APP_PY

def test_frontend_adm_in_doctor_login_guard_and_ui():
    # 3. Validação no frontend ambiental_avaliacao_medica_lts_cid_assistente.html
    assert 'function isAdmInDoctorLogin()' in ATTENDANCE_HTML
    assert 'window.isAdmInDoctorLogin = isAdmInDoctorLogin;' in ATTENDANCE_HTML
    assert 'id="badgeStatusAdmDoctorLogin"' in ATTENDANCE_HTML
    assert 'Modo Administrador em Login Médico Ativo:' in ATTENDANCE_HTML
    assert 'O preenchimento automático de campos clínicos via IA a partir do Texto Bruto é habilitado apenas para Administradores ao entrar em login médico.' in ATTENDANCE_HTML
    assert 'Texto Bruto (Anotações do Médico e/ou Dados do Sistema):' in ATTENDANCE_HTML

def test_merge_cadastral_esisla_with_clinical_ai():
    # 4. Validação de preservação dos dados cadastrais do e-SISLA ao aplicar o preenchimento com IA
    assert 'state.nomePaciente = esislaNome || dados.nome_paciente || state.nomePaciente || "";' in ATTENDANCE_HTML
    assert 'state.cpfPaciente = esislaCpf ? toFormattedCpf(esislaCpf) : (toFormattedCpf(dados.cpf_paciente) || state.cpfPaciente || "");' in ATTENDANCE_HTML
    assert 'state.cargo = esislaCargo || dados.cargo || state.cargo || "";' in ATTENDANCE_HTML

def test_doenca_motivo_prompt_and_fallback_normalization():
    # 5. Validação do preenchimento e robustez de doenca_motivo em app.py
    assert 'doenca_motivo: CAMPO OBRIGATÓRIO — Responde diretamente à pergunta: "Qual a doença está tratando que motivou o afastamento?".' in APP_PY
    assert 'd_motivo = (result.doenca_motivo or "").strip()' in APP_PY
    assert 'body["doencaMotivo"] = result.doenca_motivo' in APP_PY

def test_frontend_doenca_motivo_applied_to_both_titular_and_agil():
    # 6. Validação de que doencaMotivo é preenchido tanto no modo estendido quanto no ágil
    assert 'const doencaParaPreencher = (dados.doenca_motivo || dados.doencaMotivo || state.doencaMotivo || state.aux?.doencaMotivo || "").trim();' in ATTENDANCE_HTML
    assert 'setVal("doencaMotivo", doencaParaPreencher);' in ATTENDANCE_HTML
    assert 'setVal("agilDoencaMotivo", doencaParaPreencher);' in ATTENDANCE_HTML
    assert 'state.aux.doencaMotivo = doencaParaPreencher;' in ATTENDANCE_HTML

def test_frontend_novos_campos_obrigatorios_inicio_freq_sintomas():
    # 7. Validação de que inicioTratamento, freqConsultas e sintomasLimitacao são preenchidos
    assert 'inicio_tratamento: CAMPO OBRIGATÓRIO' in APP_PY
    assert 'freq_consultas: CAMPO OBRIGATÓRIO' in APP_PY
    assert 'sintomas_limitacao: CAMPO OBRIGATÓRIO' in APP_PY
    assert 'const inicioTratParaPreencher = (dados.inicio_tratamento || dados.inicioTratamento || state.inicioTratamento || state.aux?.inicioTratamento || "2026").trim();' in ATTENDANCE_HTML
    assert 'const freqConsParaPreencher = (dados.freq_consultas || dados.freqConsultas || state.freqConsultas || state.aux?.freqConsultas || "Mensal").trim();' in ATTENDANCE_HTML
    assert 'const sintomasParaPreencher = (dados.sintomas_limitacao || dados.sintomasLimitacao || state.sintomasLimitacao || state.aux?.sintomasLimitacao || dados.desc_limitacao || "").trim();' in ATTENDANCE_HTML
    assert 'setVal("inicioTratamento", inicioTratParaPreencher);' in ATTENDANCE_HTML
    assert 'setVal("agilInicioTratamento", inicioTratParaPreencher);' in ATTENDANCE_HTML
    assert 'setVal("freqConsultas", freqConsParaPreencher);' in ATTENDANCE_HTML
    assert 'setVal("agilFreqConsultas", freqConsParaPreencher);' in ATTENDANCE_HTML
    assert 'setVal("sintomasLimitacao", sintomasParaPreencher);' in ATTENDANCE_HTML
    assert 'setVal("agilSintomasLimitacao", sintomasParaPreencher);' in ATTENDANCE_HTML

