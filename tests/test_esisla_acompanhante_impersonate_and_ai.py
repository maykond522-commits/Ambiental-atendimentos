import re
from pathlib import Path
import pytest
from app import parse_esisla_text, app

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.py").read_text(encoding="utf-8")
API_JS = (ROOT / "api.js").read_text(encoding="utf-8")
ATTENDANCE = (ROOT / "ambiental_avaliacao_medica_lts_cid_assistente.html").read_text(encoding="utf-8")
GESTAO_ATENDIMENTOS = (ROOT / "gestao_atendimentos.html").read_text(encoding="utf-8")
GESTAO_MEDICOS = (ROOT / "gestao_medicos.html").read_text(encoding="utf-8")
GESTAO_MEDICOS_ADMIN = (ROOT / "gestao-medicos-admin.html").read_text(encoding="utf-8")


def test_acompanhante_parsing_and_contract_app():
    # 1. Teste funcional com texto real do PDF anexado pelo usuário
    sample_text = """
    Consulta Perícia Licença
    Protocolo: 2026.01.12345
    Pessoa: FILHOS (FELIPE ZANIN SILVA)
    CID: M54.5
    Data de emissão do atestado: 01/10/2026
    Dias solicitados: 5
    Nome do Servidor: MARIA SILVA
    CPF: 123.456.789-00
    """
    parsed = parse_esisla_text(sample_text)
    assert parsed.get("is_acompanhante") is True
    assert parsed.get("tipo_atendimento_pericia") == "ACOMPANHANTE"
    assert parsed.get("cid") == "Z763"
    assert parsed.get("cid_descricao") == "Pessoa em boa saúde acompanhando pessoa doente"
    assert "FELIPE ZANIN SILVA" in parsed.get("nome_dependente", "")
    assert "art. 199 da Lei Estadual nº 10.261/68" in parsed.get("doenca_motivo", "")
    assert parsed.get("cid_original") == "M54.5"
    assert any(c.get("cid") == "M54.5" for c in parsed.get("cids_secundarios", []))


def test_clinical_fields_not_prefilled_on_esisla_create():
    # Os campos clínicos e justificativa do médico NÃO devem ser preenchidos pelo PDF do e-SISLA
    block = APP[APP.index('def api_esisla_criar_atendimento():'):APP.index('@app.get("/api/atendimentos/<rid>")')]
    assert '"exameFisicoTipo": ""' in block
    assert '"exameFisicoDescricao": ""' in block
    assert '"exameMentalResultado": ""' in block
    assert '"parecer": ""' in block
    assert '"justificativa": ""' in block


def test_admin_doctor_impersonation_backend():
    # 1. _get_effective_user com verificação estrita de perfil Administrador
    assert 'def _get_effective_user():' in APP
    assert 'request.headers.get("X-Impersonate-Medico-Id")' in APP
    assert 'getattr(request, "user_role", None) == "Administrador"' in APP
    assert '"is_impersonating": True' in APP

    # 2. Endpoint exclusivo de lista para impersonate com trava 403
    assert '@app.get("/api/admin/medicos/lista-impersonate")' in APP
    assert 'def api_admin_medicos_lista_impersonate():' in APP
    assert 'denied = _require_admin()' in APP
    assert '_require_admin()' in APP


def test_senior_ai_refinement_endpoint_and_guard():
    # 1. Endpoint /api/ai/refinar-ficha-esisla
    assert '@app.post("/api/ai/refinar-ficha-esisla")' in APP
    assert 'def api_ai_refinar_ficha_esisla():' in APP
    assert '"/api/ai/refinar-ficha-esisla"' in APP

    # 2. Prompt com padrão e-SISLA / DPME e correção gramatical/duplicatas
    assert 'médico perito sênior do DPME/SP' in APP or 'médico perito sênior' in APP
    assert 'erros gramaticais' in APP or 'ortografia' in APP
    assert 'duplic' in APP


def test_api_js_client_support_for_impersonate_and_ai():
    # 1. Header X-Impersonate-Medico-Id injetado automaticamente
    assert "sessionStorage.getItem('ambiental.impersonate_medico_id')" in API_JS
    assert "X-Impersonate-Medico-Id" in API_JS

    # 2. Métodos da API JS
    assert "medicosListaImpersonate:" in API_JS
    assert "refinarFichaEsisla:" in API_JS
    assert "impersonate: {" in API_JS


def test_gestao_atendimentos_impersonate_and_ai_buttons():
    # 1. Topbar de gestao_atendimentos.html limpa e sem poluição visual
    assert 'class="top-actions"' in GESTAO_ATENDIMENTOS
    assert 'class="top-impersonate-pill"' not in GESTAO_ATENDIMENTOS
    assert 'id="btnImportarEsislaGestao"' not in GESTAO_ATENDIMENTOS
    assert 'id="syncChip"' in GESTAO_ATENDIMENTOS
    assert 'id="sessionChip"' in GESTAO_ATENDIMENTOS
    assert "carregarMedicosParaImpersonate" in GESTAO_ATENDIMENTOS
    assert "entrarComoMedico" in GESTAO_ATENDIMENTOS

    # 2. Acesso Pericial centralizado na Gestão de Médicos (gestao-medicos-admin.html)
    assert 'class="impersonate-hero-card"' in GESTAO_MEDICOS_ADMIN
    assert 'id="selectImpersonateQuick"' in GESTAO_MEDICOS_ADMIN
    assert 'entrarComoMedico' in GESTAO_MEDICOS_ADMIN
    assert 'impersonate-btn' in GESTAO_MEDICOS_ADMIN

    # 3. Botão de Refinamento IA no modal e-SISLA
    assert "Otimizar Ficha com IA" in GESTAO_ATENDIMENTOS or "Otimizar e Reestruturar com IA" in GESTAO_ATENDIMENTOS
    assert "refinarFichaEsislaIA" in GESTAO_ATENDIMENTOS


def test_gestao_medicos_impersonate_banner_and_exit():
    # 1. Banner de aviso de modo administrativo
    assert 'id="impersonateWarningBanner"' in GESTAO_MEDICOS
    assert "MODO ADMINISTRATIVO" in GESTAO_MEDICOS
    assert "sairModoImpersonate()" in GESTAO_MEDICOS


def test_attendance_screen_acompanhante_and_clean_pdf_rules():
    # 1. Banner de acompanhante e acionador de modelos
    assert 'id="bannerAcompanhantePericia"' in ATTENDANCE
    assert "aplicarModeloTextoAcompanhante" in ATTENDANCE
    assert "atualizarBannerAcompanhante" in ATTENDANCE

    # 2. Garantia de que exame físico e parecer não são preenchidos na importação do PDF
    block = ATTENDANCE[ATTENDANCE.index("function aplicarDadosEsisla(dados)"):ATTENDANCE.index("window.aplicarDadosEsisla = aplicarDadosEsisla;")]
    assert 'state.exameFisicoTipo = "";' in block
    assert 'state.exameFisicoDescricao = "";' in block
    assert 'state.parecer = "";' in block
    assert 'state.justificativa = "";' in block


def test_admin_doctor_email_update_ui_and_contract():
    # 1. Campo de edição de e-mail presente no modal de edição
    assert 'id="editEmail"' in GESTAO_MEDICOS_ADMIN
    assert 'type="email"' in GESTAO_MEDICOS_ADMIN
    assert "$('editEmail').value" in GESTAO_MEDICOS_ADMIN
    assert "email: email" in GESTAO_MEDICOS_ADMIN

    # 2. Backend atualiza email e sincroniza com o Supabase Auth
    assert 'email = str(body.get("email") or "").strip().lower()' in APP
    assert 'LOWER(COALESCE(email,\'\')) = LOWER(%s) AND id <> %s' in APP
    assert '"email": email_final' in APP
    assert '"email_confirm": True' in APP


def test_impersonated_doctor_agenda_resolution():
    # 1. _get_effective_user resolve médico alvo quando Administrador impersona
    assert 'eff = _get_effective_user()' in APP
    assert 'medico_id = eff["id"]' in APP

    # 2. Portal médico exibe painel da agenda do dia e propaga medico_id
    assert 'id="dashboardAgendaPanel"' in GESTAO_MEDICOS
    assert 'loadDoctorDayAgenda' in GESTAO_MEDICOS
    assert 'sessionStorage.getItem(\'ambiental.impersonate_medico_id\')' in GESTAO_MEDICOS
    assert "params.medico_id = impId" in GESTAO_MEDICOS
    assert "p.set('medico_id', impId)" in GESTAO_MEDICOS


def test_impersonated_doctor_finalize_and_navigation():
    # 1. Attendance interface resolves impersonated doctor identity and banner
    assert 'sessionStorage.getItem(\'ambiental.impersonate_medico_id\')' in ATTENDANCE
    assert 'appImpersonateBanner' in ATTENDANCE
    assert 'gestao_medicos.html?impersonate_medico_id=' in ATTENDANCE

    # 2. openManagement and finalizeGoBack navigate back to doctor portal
    assert 'function openManagement()' in ATTENDANCE
    assert 'function finalizeGoBack()' in ATTENDANCE

    # 3. Backend persists doctor identity and links usuario_id on save and finalization
    assert 'if eff.get("is_impersonating") and eff.get("role") == "Médico":' in APP
    assert 'cur.execute("UPDATE atendimentos SET status=%s, payload_json=%s, medico=%s, usuario_id=%s' in APP


def test_refinar_ficha_esisla_payload_and_fallback():
    # 1. Endpoint accepts ficha_esisla, texto_ficha and texto
    assert 'body.get("ficha_esisla") or body.get("texto_ficha") or body.get("texto")' in APP
    assert '_refinar_ficha_esisla_deterministica' in APP
    assert '"texto_otimizado": ficha_otimizada' in APP

    # 2. Gestão atendimentos sends compatible payload and parses response
    assert 'texto_ficha: texto' in GESTAO_ATENDIMENTOS
    assert 'ficha_esisla: texto' in GESTAO_ATENDIMENTOS


def test_sanitizacao_ortografica_e_desduplicacao_esisla():
    from app import _sanitizar_texto_portugues_esisla, _desduplicar_e_limpar_queixa_esisla

    # 1. Validação de remoção de mácrons e acentuação gráfica oficial
    raw_text = (
        "quadro clinico compativel com sindrome gripal com inicio em 30/09/2026. "
        "sintomas sistēmicos, comorbidades crōnicas sistēmicas prēvias. "
        "Ausēncia de exames complementares. Pericia medica, sendo imprescindivel o periodo de repouso "
        "para recuperacao da higidez fisica."
    )
    sanitized = _sanitizar_texto_portugues_esisla(raw_text)
    assert "clínico" in sanitized
    assert "compatível" in sanitized
    assert "síndrome" in sanitized
    assert "início" in sanitized
    assert "sistêmicos" in sanitized
    assert "crônicas" in sanitized
    assert "sistêmicas" in sanitized
    assert "prévias" in sanitized
    assert "Ausência" in sanitized
    assert "Perícia médica" in sanitized or "Perícia" in sanitized
    assert "imprescindível" in sanitized
    assert "período" in sanitized
    assert "física" in sanitized
    assert "ē" not in sanitized
    assert "ō" not in sanitized

    # 2. Validação de desduplicação e remoção de exames vazados para a queixa
    raw_sheet = (
        "Registro da perícia Médica para Licença\n\n"
        "(*) Queixa e Duração:\n"
        "Servidor de 30 anos relata sintomas gripais.\n\n"
        "Exames apresentados: Ausência de exames complementares (laboratoriais ou de imagem) apresentados no ato pericial.\n\n"
        "Antecedentes Mórbidos:\n"
        "Nega comorbidades crônicas.\n\n"
        "Descrição das Alterações Clínicas encontradas e Relato dos Exames Complementares:\n"
        "Ausência de exames complementares (laboratoriais ou de imagem) apresentados no ato pericial.\n\n"
        "(*)Descrição da(s) Limitação(ções) Física(s) e/ou Mental(is) encontrada(s):\n"
        "Limitação temporária.\n"
    )
    cleaned = _desduplicar_e_limpar_queixa_esisla(raw_sheet)
    queixa_part = cleaned.split("Antecedentes Mórbidos:")[0]
    assert "Exames apresentados:" not in queixa_part
    assert "Ausência de exames complementares" not in queixa_part
    assert "Descrição das Alterações Clínicas" in cleaned

    # 3. Validação das salvaguardas em HTML / JS
    app_py = (ROOT / "app.py").read_text(encoding="utf-8")
    gestao_html = (ROOT / "gestao_atendimentos.html").read_text(encoding="utf-8")
    att_html = (ROOT / "ambiental_avaliacao_medica_lts_cid_assistente.html").read_text(encoding="utf-8")

    assert "_sanitizar_texto_portugues_esisla" in app_py
    assert "_desduplicar_e_limpar_queixa_esisla" in app_py
    assert "sanitizePtBrEsisla" in gestao_html
    assert "aus[êeē]ncia" in gestao_html or "Aus[êeē]ncia" in gestao_html
    assert "aus[êeē]ncia" in att_html or "Aus[êeē]ncia" in att_html


def test_esisla_vincular_agenda_batch_contract():
    # 1. Endpoint no app.py
    assert '@app.post("/api/esisla/vincular-agenda-batch")' in APP
    assert 'def api_esisla_vincular_agenda_batch():' in APP
    assert 'IMPORTACAO_ESISLA_AGENDA_BATCH' in APP

    # 2. Wrapper no api.js
    assert 'vincularAgendaBatch:' in API_JS
    assert '/api/esisla/vincular-agenda-batch' in API_JS

    # 3. UI da Agenda Médica em gestao_medicos.html
    assert 'id="modalImportarEsislaAgenda"' in GESTAO_MEDICOS
    assert 'abrirModalImportarEsislaAgenda()' in GESTAO_MEDICOS
    assert 'fecharModalImportarEsislaAgenda()' in GESTAO_MEDICOS
    assert 'executarVinculacaoBatchEsisla()' in GESTAO_MEDICOS
    assert 'id="esislaDropzone"' in GESTAO_MEDICOS
    assert 'id="esislaResultsReport"' in GESTAO_MEDICOS
    assert 'Ficha Vinculada' in GESTAO_MEDICOS


