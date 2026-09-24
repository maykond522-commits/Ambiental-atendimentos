from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.py").read_text(encoding="utf-8")
API_JS = (ROOT / "api.js").read_text(encoding="utf-8")
ATTENDANCE = (ROOT / "ambiental_avaliacao_medica_lts_cid_assistente.html").read_text(encoding="utf-8")
GESTAO_MEDICOS_ADMIN = (ROOT / "gestao-medicos-admin.html").read_text(encoding="utf-8")
GESTAO_MEDICOS = (ROOT / "gestao_medicos.html").read_text(encoding="utf-8")
GESTAO_ATENDIMENTOS = (ROOT / "gestao_atendimentos.html").read_text(encoding="utf-8")


def test_admin_doctor_update_endpoint():
    assert '@app.put("/api/admin/medicos/<user_id>")' in APP
    assert "def api_admin_editar_medico(user_id):" in APP
    assert "denied = _require_admin()" in APP
    assert 'len(nome) < 3' in APP
    assert 'len(crm) < 3' in APP
    assert 'LOWER(COALESCE(crm,\'\')) = LOWER(%s) AND id <> %s' in APP
    assert "UPDATE usuarios SET nome=%s, crm=%s WHERE id=%s" in APP
    assert "_supabase_admin_request(\"PUT\", f\"/auth/v1/admin/users/" in APP


def test_admin_doctor_status_toggle_endpoint():
    assert '@app.patch("/api/admin/medicos/<user_id>/status")' in APP
    assert "def api_admin_toggle_status_medico(user_id):" in APP
    assert 'novo_status = 0 if int(row.get("ativo") or 0) == 1 else 1' in APP
    assert "UPDATE usuarios SET ativo=%s WHERE id=%s" in APP


def test_admin_doctor_reset_password_endpoint():
    assert '@app.post("/api/admin/medicos/<user_id>/senha")' in APP
    assert "def api_admin_reset_senha_medico(user_id):" in APP
    assert 'len(senha) < 8' in APP
    assert '"password": senha' in APP


def test_api_js_admin_and_esisla_contract():
    assert "admin: {" in API_JS
    assert "medicos:" in API_JS
    assert "createMedico:" in API_JS
    assert "updateMedico:" in API_JS
    assert "toggleStatus:" in API_JS
    assert "resetSenha:" in API_JS
    assert "deleteMedico:" in API_JS
    assert "esisla: (payload) =>" in API_JS


def test_attendance_esisla_restricted_to_admins_only():
    # Button must be hidden by default
    assert 'id="btnCopiarEsisla"' in ATTENDANCE
    assert 'style="display:none;"' in ATTENDANCE
    
    # Must explicitly verify administrative role before displaying
    assert '["Administrador", "Coordenador", "Revisor", "Gestor"].includes(profile?.perfil)' in ATTENDANCE
    
    # Must copy to clipboard
    assert 'navigator.clipboard.writeText' in ATTENDANCE
    assert 'copiarFichaEsislaRapida' in ATTENDANCE


def test_attendance_optimizations_and_safety():
    # Inline 50KB base64 logo replaced with clean static path
    assert 'const LOGO_DATA = "/logo.png"' in ATTENDANCE
    assert "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgA" not in ATTENDANCE
    
    # AI Justification undo feature
    assert "_justificativa_anterior" in ATTENDANCE
    assert "undoJustificativa" in ATTENDANCE
    
    # Debounced keystroke autosave (1500ms)
    assert "_inputDebounceTimer" in ATTENDANCE
    assert "1500" in ATTENDANCE


def test_gestao_medicos_admin_modals_and_actions():
    # Modals for editing doctor and resetting password
    assert 'id="editModal"' in GESTAO_MEDICOS_ADMIN
    assert 'id="pwdModal"' in GESTAO_MEDICOS_ADMIN
    assert 'openEditDoctor' in GESTAO_MEDICOS_ADMIN
    assert 'openPwdDoctor' in GESTAO_MEDICOS_ADMIN
    assert 'toggleDoctorStatus' in GESTAO_MEDICOS_ADMIN
    assert 'AmbientalAPI.admin.updateMedico' in GESTAO_MEDICOS_ADMIN
    assert 'AmbientalAPI.admin.toggleStatus' in GESTAO_MEDICOS_ADMIN
    assert 'AmbientalAPI.admin.resetSenha' in GESTAO_MEDICOS_ADMIN


def test_gestao_medicos_portal_pagination_and_quick_view():
    # Quick View modal
    assert 'id="quickViewModal"' in GESTAO_MEDICOS
    assert 'openQuickView' in GESTAO_MEDICOS
    assert 'printQuickView' in GESTAO_MEDICOS
    
    # Pagination
    assert 'currentPage' in GESTAO_MEDICOS
    assert 'pageSize' in GESTAO_MEDICOS
    assert 'prevPageBtn' in GESTAO_MEDICOS
    assert 'nextPageBtn' in GESTAO_MEDICOS
    assert 'pageInfo' in GESTAO_MEDICOS
    
    # Single primary hero action and visual elements
    assert 'id="newBtn"' in GESTAO_MEDICOS
    assert 'id="iaBtn"' not in GESTAO_MEDICOS
    assert '<link rel="stylesheet" href="/global.css">' in GESTAO_MEDICOS
    assert 'kpi-today' in GESTAO_MEDICOS

    # Sync animation and screen liberation
    assert 'sync-progress-track' in GESTAO_MEDICOS
    assert 'updateSyncLoader' in GESTAO_MEDICOS
    assert 'top-sync-bar' in GESTAO_MEDICOS
    assert 'fade-out' in GESTAO_MEDICOS




def test_attendance_cid_support_and_autocomplete():
    # Database loading and categories
    assert 'await loadCIDs()' in ATTENDANCE
    assert 'CID_CATEGORIES' in ATTENDANCE
    assert '"F32": { n: "Episódios depressivos"' in ATTENDANCE
    assert '"M54": { n: "Dorsalgia"' in ATTENDANCE
    
    # CID Search and assist
    assert 'function findCID(code)' in ATTENDANCE
    assert 'function renderCIDSuggestions(value)' in ATTENDANCE
    assert 'function renderCIDAssist(entry)' in ATTENDANCE
    
    # Passing support to fields
    assert 'function selectCID(code)' in ATTENDANCE
    assert '$("doencaMotivo").value = rotulo;' in ATTENDANCE
    assert 'insertCIDText(\'doenca\'' in ATTENDANCE
    assert 'insertCIDText(\'observacoes\'' in ATTENDANCE
    assert 'insertCIDText(\'sintomas\'' in ATTENDANCE
    assert 'insertCIDText(\'limitacoes\'' in ATTENDANCE
    assert 'insertCIDText(\'justificativa\'' in ATTENDANCE
    assert 'Roteiro inserido nas observações do atestado' in ATTENDANCE
    assert 'Roteiro inserido em Sintomas / Queixa' in ATTENDANCE


def test_gestao_admin_refresh_and_esisla_view():
    # ↻ (Atualizar) icon buttons and refresh animation
    assert 'id="refreshBtn"' in GESTAO_ATENDIMENTOS
    assert 'id="adminRefreshBtn"' in GESTAO_ATENDIMENTOS
    assert 'triggerRefresh()' in GESTAO_ATENDIMENTOS
    assert 'top-sync-bar' in GESTAO_ATENDIMENTOS
    
    # e-Sisla modal view and generating animation
    assert 'id="esislaModal"' in GESTAO_ATENDIMENTOS
    assert 'esisla-dialog-window' in GESTAO_ATENDIMENTOS
    assert 'esisla-compliance-banner' in GESTAO_ATENDIMENTOS
    assert 'updateEsislaStats' in GESTAO_ATENDIMENTOS
    assert 'id="esislaStatsChip"' in GESTAO_ATENDIMENTOS
    assert 'id="downloadEsislaBtn"' in GESTAO_ATENDIMENTOS
    assert 'id="copyEsislaBtn"' in GESTAO_ATENDIMENTOS
    assert 'id="esislaGenerating"' in GESTAO_ATENDIMENTOS
    assert 'esisla-spinner-box' in GESTAO_ATENDIMENTOS


def test_agenda_backend_and_database_contract():
    # Database schema
    assert "CREATE TABLE IF NOT EXISTS agendas (" in APP
    assert "idx_agendas_medico_data_hora" in APP
    assert "idx_agendas_protocolo" in APP

    # Admin endpoints
    assert '@app.get("/api/admin/medicos/<user_id>/agendas")' in APP
    assert "def api_admin_listar_agendas_medico(user_id):" in APP
    assert '@app.post("/api/admin/medicos/<user_id>/agendas")' in APP
    assert "def api_admin_gravar_agendas_medico(user_id):" in APP
    assert '@app.delete("/api/admin/medicos/<user_id>/agendas")' in APP
    assert "def api_admin_limpar_agendas_data(user_id):" in APP
    assert '@app.delete("/api/admin/agendas/<int:agenda_id>")' in APP
    assert "def api_admin_excluir_agenda_item(agenda_id):" in APP

    # Doctor endpoints
    assert '@app.get("/api/medico/agenda")' in APP
    assert "def api_medico_agenda():" in APP
    assert '@app.patch("/api/medico/agenda/<int:agenda_id>/status")' in APP
    assert "def api_medico_atualizar_status_agenda(agenda_id):" in APP

    # API JS bindings
    assert "agenda: (params = {})" in API_JS
    assert "updateAgendaStatus:" in API_JS
    assert "getAgendas:" in API_JS
    assert "saveAgendas:" in API_JS
    assert "deleteAgenda:" in API_JS
    assert "clearAgendas:" in API_JS


def test_agenda_admin_frontend_contract():
    # Tab navigation in edit modal
    assert 'id="tabBtnEditDados"' in GESTAO_MEDICOS_ADMIN
    assert 'id="tabBtnEditAgenda"' in GESTAO_MEDICOS_ADMIN
    assert 'id="tabContentEditAgenda"' in GESTAO_MEDICOS_ADMIN
    assert 'switchEditModalTab' in GESTAO_MEDICOS_ADMIN

    # Spreadsheet import and paste
    assert 'id="agendaPasteInput"' in GESTAO_MEDICOS_ADMIN
    assert 'id="agendaFileInput"' in GESTAO_MEDICOS_ADMIN
    assert 'id="btnProcessarPlanilha"' in GESTAO_MEDICOS_ADMIN
    assert 'parseAgendaCsvText' in GESTAO_MEDICOS_ADMIN

    # Preview and save
    assert 'id="agendaPreviewArea"' in GESTAO_MEDICOS_ADMIN
    assert 'id="agendaPreviewTbody"' in GESTAO_MEDICOS_ADMIN
    assert 'id="btnSalvarAgenda"' in GESTAO_MEDICOS_ADMIN
    assert 'checkSubstituirAgenda' in GESTAO_MEDICOS_ADMIN

    # Day management
    assert 'id="agendaDataInput"' in GESTAO_MEDICOS_ADMIN
    assert 'id="btnLimparAgendaDia"' in GESTAO_MEDICOS_ADMIN
    assert 'deleteIndividualAgenda' in GESTAO_MEDICOS_ADMIN
    assert 'data-agenda' in GESTAO_MEDICOS_ADMIN


def test_agenda_doctor_frontend_contract():
    # Ver agenda do dia buttons
    assert 'id="heroAgendaDiaBtn"' in GESTAO_MEDICOS
    assert 'id="quickAgendaDia"' in GESTAO_MEDICOS
    assert 'id="btnAgendaHojeTop"' in GESTAO_MEDICOS
    assert 'Ver agenda do dia' in GESTAO_MEDICOS

    # Day agenda view in chronological order
    assert 'id="agendaDaySection"' in GESTAO_MEDICOS
    assert 'id="doctorAgendaList"' in GESTAO_MEDICOS
    assert 'agenda-item-card' in GESTAO_MEDICOS
    assert 'agenda-time-box' in GESTAO_MEDICOS

    # Actions and Attendance integration
    assert 'iniciarAtendimentoAgenda' in GESTAO_MEDICOS
    assert 'toggleComparecimentoAgenda' in GESTAO_MEDICOS
    assert 'id="modalAgendaDoDia"' in GESTAO_MEDICOS
    assert 'openAgendaDoDiaModal' in GESTAO_MEDICOS


def test_attendance_agenda_query_params_prefill():
    # Pre-fills patient, protocol, time and NI from schedule
    assert 'const pacienteParam = params.get("paciente");' in ATTENDANCE
    assert 'const protocoloParam = params.get("protocolo") || params.get("agenda_protocolo");' in ATTENDANCE
    assert 'const horaParam = params.get("hora");' in ATTENDANCE
    assert 'const niParam = params.get("ni");' in ATTENDANCE
    assert 'state.aux.nomePaciente = pacienteParam;' in ATTENDANCE
    assert 'state.atendimento = protocoloParam;' in ATTENDANCE
    assert 'state.aux.horaAtd = horaParam;' in ATTENDANCE
    assert 'state.aux.ni = niParam;' in ATTENDANCE


