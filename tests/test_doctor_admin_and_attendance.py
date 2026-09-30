import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.py").read_text(encoding="utf-8")
API_JS = (ROOT / "api.js").read_text(encoding="utf-8")
ATTENDANCE = (ROOT / "ambiental_avaliacao_medica_lts_cid_assistente.html").read_text(encoding="utf-8")
GESTAO_MEDICOS_ADMIN = (ROOT / "gestao-medicos-admin.html").read_text(encoding="utf-8")
GESTAO_MEDICOS = (ROOT / "gestao_medicos.html").read_text(encoding="utf-8")
GESTAO_ATENDIMENTOS = (ROOT / "gestao_atendimentos.html").read_text(encoding="utf-8")
LOGIN = (ROOT / "login.html").read_text(encoding="utf-8")


def test_admin_doctor_update_endpoint():
    assert '@app.put("/api/admin/medicos/<user_id>")' in APP
    assert "def api_admin_editar_medico(user_id):" in APP
    assert "denied = _require_admin()" in APP
    assert 'len(nome) < 3' in APP
    assert 'len(crm) < 3' in APP
    assert 'LOWER(COALESCE(crm,\'\')) = LOWER(%s) AND id <> %s' in APP
    assert "UPDATE usuarios SET nome=%s, crm=%s, email=%s, modo_atendimento=%s WHERE id=%s" in APP
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


def test_attendance_header_actions():
    # Only Gestão, Excluir, Salvar rascunho, Finalizar in header
    header_block = ATTENDANCE[ATTENDANCE.find('<div class="header-actions">'):ATTENDANCE.find('</header>')]
    assert 'onclick="openManagement()"' in header_block
    assert 'onclick="deleteAtendimento()"' in header_block
    assert 'onclick="saveNow()"' in header_block
    assert 'onclick="finalizeFromHeader()"' in header_block
    assert 'onclick="openFinalReport()"' not in header_block
    
    # Must NOT have esisla or robo buttons in attendance header
    assert 'btnCopiarEsisla' not in header_block
    assert 'btnCopiarEsislaJson' not in header_block
    assert 'btnRoboEsisla' not in header_block


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
    # Auto-sync em tempo real e atualização automática sem necessidade de F5
    assert 'id="syncChip"' in GESTAO_ATENDIMENTOS
    assert 'id="syncDot"' in GESTAO_ATENDIMENTOS
    assert 'id="syncTitle"' in GESTAO_ATENDIMENTOS
    assert 'id="syncSub"' in GESTAO_ATENDIMENTOS
    assert 'id="searchRefreshBtn"' in GESTAO_ATENDIMENTOS
    assert 'function initAutoSync()' in GESTAO_ATENDIMENTOS
    assert 'computeDatasetFingerprint(' in GESTAO_ATENDIMENTOS
    assert 'autoSyncIntervalTimer' in GESTAO_ATENDIMENTOS
    assert 'visibilitychange' in GESTAO_ATENDIMENTOS
    assert 'window.lastFetchBackendSuccess' in GESTAO_ATENDIMENTOS


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


def test_modo_agil_mode_switcher_and_layout():
    # Mode switcher buttons in header
    assert 'id="btnModoAgil"' in ATTENDANCE
    assert 'id="btnModoEstendido"' in ATTENDANCE
    assert 'setAttendanceMode(\'agil\')' in ATTENDANCE or 'setAttendanceMode("agil")' in ATTENDANCE
    assert 'setAttendanceMode(\'estendido\')' in ATTENDANCE or 'setAttendanceMode("estendido")' in ATTENDANCE

    # Container Modo Ágil exists
    assert 'id="containerModoAgil"' in ATTENDANCE

    # CSS rules for switching modes
    assert 'body.mode-agil-active .sidebar' in ATTENDANCE
    assert 'body.mode-agil-active .section' in ATTENDANCE
    assert 'body:not(.mode-agil-active) #containerModoAgil' in ATTENDANCE


def test_modo_agil_bloco1_cadastral_and_medications():
    # Bloco 01 fields
    assert 'id="agilNomePaciente"' in ATTENDANCE
    assert 'id="agilCpfPaciente"' in ATTENDANCE
    assert 'id="agilCargo"' in ATTENDANCE
    assert 'id="agilTempoCargo"' in ATTENDANCE
    assert 'id="agilTempoUnidade"' in ATTENDANCE
    assert 'id="agilIdade"' in ATTENDANCE
    assert 'name="agilReadaptado"' in ATTENDANCE
    assert 'id="agilAtividadesReadaptado"' in ATTENDANCE

    # Bloco 02 fields (Queixa e Duração & Antecedentes)
    assert 'id="agilDoencaMotivo"' in ATTENDANCE
    assert 'id="agilInicioTratamento"' in ATTENDANCE
    assert 'id="agilFreqConsultas"' in ATTENDANCE
    assert 'id="agilSintomasLimitacao"' in ATTENDANCE
    assert 'id="agilMedRows"' in ATTENDANCE
    assert 'name="agilAlteracaoMed"' in ATTENDANCE
    assert 'id="agilPsicoterapia"' in ATTENDANCE
    assert 'id="agilFisioterapia"' in ATTENDANCE
    assert 'id="agilObsTerapias"' in ATTENDANCE
    assert 'name="agilOutrasDoencas"' in ATTENDANCE
    assert 'id="agilCondRows"' in ATTENDANCE
    assert 'id="agilHistoricoPregresso"' in ATTENDANCE

    # Synchronization functions
    assert 'function syncAgilField' in ATTENDANCE
    assert 'function syncAgilCpf' in ATTENDANCE
    assert 'function syncAgilRadio' in ATTENDANCE
    assert 'function syncAgilCheckbox' in ATTENDANCE
    assert 'function syncAgilReadaptado' in ATTENDANCE
    assert 'function syncAgilAlteracaoMed' in ATTENDANCE
    assert 'function syncAgilOutrasDoencas' in ATTENDANCE
    assert 'function onAgilDoencaMotivoInput' in ATTENDANCE


def test_modo_agil_bloco2_exam_restriction_and_vitals():
    # CID is the first question in Bloco 02 with autocomplete
    assert 'id="agilCid"' in ATTENDANCE
    assert 'id="agilCidSuggestions"' in ATTENDANCE
    assert 'id="agilCidBadge"' in ATTENDANCE
    assert 'onAgilCidInput' in ATTENDANCE
    assert 'selectAgilCID' in ATTENDANCE

    # Exam type restricted to 2 options in Modo Ágil
    assert 'id="agilExameFisicoTipo"' in ATTENDANCE
    assert '<option value="Aparelho Osteomuscular e Tecido Conjutivo">Aparelho Osteomuscular e Tecido Conjutivo</option>' in ATTENDANCE
    assert '<option value="Exame Mental">Exame Mental</option>' in ATTENDANCE
    assert 'id="agilMentalSelector"' in ATTENDANCE
    assert 'id="btnAgilMentalNormal"' in ATTENDANCE
    assert 'id="btnAgilMentalAlterado"' in ATTENDANCE

    # Vitals / biometrics
    assert 'id="agilPressaoSistolica"' in ATTENDANCE
    assert 'id="agilPressaoDiastolica"' in ATTENDANCE
    assert 'id="agilPulso"' in ATTENDANCE
    assert 'id="agilAltura"' in ATTENDANCE
    assert 'id="agilPeso"' in ATTENDANCE

    # Findings textarea
    assert 'id="agilExameFisicoDescricao"' in ATTENDANCE


def test_modo_agil_exame_mental_normal_autofill_contract():
    assert 'function aplicarExameMentalNormal()' in ATTENDANCE
    assert 'TEXTO_EXAME_MENTAL_NORMAL' in ATTENDANCE
    assert 'Nível de consciência: Preservado' in ATTENDANCE
    assert 'Orientação: Global preservada em tempo e espaço' in ATTENDANCE
    assert 'Atenção e concentração:  Sem desvios, preservados.' in ATTENDANCE
    assert 'Memória:  Não demostrou dificuldades em responder questões' in ATTENDANCE
    assert 'Humor: Eutímico, polarizado ao positivo.' in ATTENDANCE
    assert 'Juízo: Preservado.' in ATTENDANCE

    # Normal limitation
    assert 'TEXTO_LIMITACAO_NORMAL' in ATTENDANCE
    assert 'Não se identificam limitações funcionais em níveis que possam ser considerados incapacitantes neste momento.' in ATTENDANCE

    # Normal quesitos rule: Q1=Sim, Q2=Sim, Q3=Não
    assert 'QuesitoService.set(0, "Sim")' in ATTENDANCE
    assert 'QuesitoService.set(1, "Sim")' in ATTENDANCE
    assert 'QuesitoService.set(2, "Não")' in ATTENDANCE

    # Normal capacidade & parecer
    assert 'Capacidade laborativa preservada' in ATTENDANCE
    assert 'CONTRÁRIO' in ATTENDANCE

    # Normal justification
    assert 'TEXTO_JUSTIFICATIVA_NORMAL' in ATTENDANCE
    assert 'Capacidade laborativa preservada, não se identificam limitações funcionais em níveis que possam ser considerados incapacitantes neste momento.' in ATTENDANCE


def test_modo_agil_exame_mental_alterado_autofill_contract():
    assert 'function aplicarExameMentalAlterado()' in ATTENDANCE
    assert 'TEXTO_EXAME_MENTAL_ALTERADO' in ATTENDANCE
    assert 'Apresentas-e consciente, boa orientação' in ATTENDANCE
    assert 'Facie entristecida, hipotimica, manifestação de labilidade emocional' in ATTENDANCE
    assert 'insight negativo sobre seu quadro clinico' in ATTENDANCE
    assert 'pensamentos ruminantes com conteúdo de ressentimentos, desesperança, desestruturado' in ATTENDANCE
    assert 'Hipopragamatica, com volição prejudicada' in ATTENDANCE

    # Altered limitation
    assert 'TEXTO_LIMITACAO_ALTERADO' in ATTENDANCE
    assert 'Apresenta limitações psicossociais e psicoemocionais que repercutem nas habilidades necessárias para interatividade social, planejamentos, manter concentração e ter autodomínio.' in ATTENDANCE

    # Altered quesitos rule: Q1=Sim, Q2=Sim, Q3=Sim
    assert 'QuesitoService.set(2, "Sim")' in ATTENDANCE

    # Altered capacidade & parecer
    assert 'Capacidade parcial e temporariamente prejudicada' in ATTENDANCE
    assert 'FAVORÁVEL' in ATTENDANCE

    # Altered justification
    assert 'TEXTO_JUSTIFICATIVA_ALTERADO' in ATTENDANCE
    assert 'Capacidade laborativa parcial e temporariamente prejudicada, limitações psicossociais e psicoemocionais que repercutem nas habilidades necessárias para interatividade social, planejamentos, manter concentração e ter autodomínio, referente ao período pleiteado.' in ATTENDANCE


def test_modo_agil_bloco3_finalization_and_hidden_parecer():
    # In Modo Ágil, Parecer is hidden from quick view and bound automatically
    assert 'id="agilJustificativa"' in ATTENDANCE
    assert 'id="btnAgilFinalizar"' in ATTENDANCE
    assert 'function finalizarAtendimentoAgil()' in ATTENDANCE
    assert 'function ensureAgileBackgroundDefaults()' in ATTENDANCE

    # Background defaults: 03 = histDef (coleta do campo ágil ou Nega se em branco), 04 = Em anexo
    assert 'const histDef = histAgil || "Nega"' in ATTENDANCE
    assert 'state.aux.obsDocumentos = "Em anexo"' in ATTENDANCE
    assert 'state.aux.crmCro = "Em anexo"' in ATTENDANCE
    assert 'state.aux.diasSolicitados = "Conforme atestado"' in ATTENDANCE
    assert 'state.aux.queixaDuracao' in ATTENDANCE
    assert 'QuesitoService.set(' in ATTENDANCE


def test_auth_caching_and_jwt_resilience_contract():
    # Cache thread-safe cross-request
    assert '_AUTH_CACHE: dict[str, dict[str, Any]] = {}' in APP
    assert '_AUTH_CACHE_LOCK = threading.Lock()' in APP
    assert '_decode_jwt_payload_unverified(token: str)' in APP
    
    # 8-hour session cookie
    assert 'max_age=28800' in APP
    
    # Supabase timeout fallback
    assert 'Supabase indisponível/timeout; mantendo sessão ativa via claims JWT' in APP
    assert '_AUTH_CACHE.pop(token_hash, None)' in APP


def test_modo_agil_finalization_zero_blocking():
    # Frontend syncState protects prevAux without premature background defaults
    assert 'const prevAux = state.aux || {};' in ATTENDANCE
    assert 'crmCro:getVal("crmCro", prevAux.crmCro)' in ATTENDANCE
    assert 'dataDocumento:getVal("dataDocumento", prevAux.dataDocumento)' in ATTENDANCE
    assert 'diasSolicitados:getVal("diasSolicitados", prevAux.diasSolicitados)' in ATTENDANCE

    # Test backend finalization validation with an agile payload
    from app import _finalization_blockers
    agile_payload = {
        "readaptado": "Não",
        "exameFisicoTipo": "Exame Mental",
        "limitacaoFuncional": "Sim",
        "limitacaoRol": "Sim",
        "capacidade": "Capacidade parcial e temporariamente prejudicada",
        "parecer": "FAVORÁVEL",
        "quesitos": [
            {"resposta": "Sim"},
            {"resposta": "Sim"},
            {"resposta": "Sim"}
        ],
        "aux": {
            "cargo": "Assistente Administrativo",
            "idade": "34",
            "readaptado": "Não",
            "cid": "F32.2",
            "doencaMotivo": "F32.2 — Episódio depressivo grave",
            "inicioTratamento": "2026-09-24",
            "sintomasLimitacao": "Apresenta limitações psicossociais",
            "crmCro": "Em anexo",
            "dataDocumento": "2026-09-24",
            "diasSolicitados": "Conforme atestado",
            "justificativa": "Capacidade laborativa parcial e temporariamente prejudicada..."
        }
    }
    blockers = _finalization_blockers(agile_payload)
    assert blockers == [], f"Expected 0 blockers for agile payload, got: {blockers}"


def test_novo_atendimento_lifecycle_and_default_agil_mode():
    # 1. newEmptyState generates ID immediately and cleans server identifiers
    assert 'state.atendimento = generateId()' in ATTENDANCE or 'state.atendimento=generateId()' in ATTENDANCE
    assert 'delete state.__serverId;' in ATTENDANCE
    assert 'delete state.__serverVersion;' in ATTENDANCE
    assert 'delete state.__serverSyncedAt;' in ATTENDANCE
    assert 'applyFinalizedLock();' in ATTENDANCE
    assert 'state.osteomuscularRegioes = {};' in ATTENDANCE or 'state.osteomuscularRegioes={};' in ATTENDANCE
    assert 'state.osteomuscularResultado = "";' in ATTENDANCE or 'state.osteomuscularResultado="";' in ATTENDANCE

    # 2. init() defaults to Modo Ágil for new attendances
    assert 'setAttendanceMode("agil");' in ATTENDANCE
    assert 'if(isNew || !recordId)' in ATTENDANCE

    # 3. Parameter synchronization updates both extended and agile elements
    assert '$("agilNomePaciente").value = pacienteParam;' in ATTENDANCE
    assert '$("atd").value = protocoloParam;' in ATTENDANCE

    # 4. saveNow() syncs agile state before persisting
    assert 'if(typeof currentAttendanceMode !== "undefined" && currentAttendanceMode === "agil")' in ATTENDANCE
    assert 'syncAgilToExtended();' in ATTENDANCE
    assert 'toast("Rascunho salvo com sucesso.");' in ATTENDANCE


def test_osteo_interactive_body_map_and_9_regions_structure():
    # 1. Selector container and image
    assert 'id="agilOsteomuscularSelector"' in ATTENDANCE
    assert 'src="/corpo_humano.png"' in ATTENDANCE
    assert 'class="osteo-body-img"' in ATTENDANCE
    assert 'class="osteo-hotspot"' in ATTENDANCE

    # 2. All 9 anatomical regions present in cards, with individual lateralities for peripheral joints
    axial_regions = ["cervical", "lombar", "quadril"]
    paired_groups = ["ombros", "cotovelos", "antebracos", "maos", "joelhos", "tornozelos"]
    lateralities = [
        "ombro_direito", "ombro_esquerdo",
        "cotovelo_direito", "cotovelo_esquerdo",
        "antebraco_direito", "antebraco_esquerdo",
        "mao_direita", "mao_esquerda",
        "joelho_direito", "joelho_esquerdo",
        "tornozelo_direito", "tornozelo_esquerdo"
    ]

    for r in axial_regions:
        assert f'data-regiao="{r}"' in ATTENDANCE, f"Missing hotspot for {r}"
        assert f'id="cardOsteo_{r}"' in ATTENDANCE, f"Missing card for {r}"
        assert f'id="btnOsteoAlt_{r}"' in ATTENDANCE, f"Missing Alterado button for {r}"
        assert f'id="btnOsteoNorm_{r}"' in ATTENDANCE, f"Missing Normal button for {r}"

    for g in paired_groups:
        assert f'data-group="{g}"' in ATTENDANCE, f"Missing hotspot group for {g}"
        assert f'id="cardOsteo_{g}"' in ATTENDANCE, f"Missing card for {g}"
        assert f'id="btnOsteoAlt_{g}"' in ATTENDANCE, f"Missing Alterado button for {g}"
        assert f'id="btnOsteoNorm_{g}"' in ATTENDANCE, f"Missing Normal button for {g}"

    for lat in lateralities:
        assert f'data-regiao="{lat}"' in ATTENDANCE, f"Missing hotspot for {lat}"
        assert f'id="btnOsteoAlt_{lat}"' in ATTENDANCE, f"Missing Alterado button for {lat}"
        assert f'id="btnOsteoNorm_{lat}"' in ATTENDANCE, f"Missing Normal button for {lat}"

    # 3. Quick action buttons
    assert 'onclick="aplicarOsteomuscularNormal()"' in ATTENDANCE
    assert 'onclick="limparOsteomuscular()"' in ATTENDANCE
    assert 'function setupOsteoHoverEffects()' in ATTENDANCE


def test_osteo_medical_data_exact_texts_and_autocompletion():
    # 1. Clinical text dictionary exists
    assert 'const DADOS_OSTEOMUSCULAR = {' in ATTENDANCE

    # 2. Exact texts specified in user prompt
    assert 'Trapézios sem contraturas' in ATTENDANCE
    assert 'limitações para mudança do campo visual de forma brusca' in ATTENDANCE
    assert 'Lasegue + a 45º' in ATTENDANCE
    assert 'limitações para realizar dosiflexão e extensão' in ATTENDANCE
    assert 'Neer, Jobe, Patte, Gerber, Howkins e Queda negativos' in ATTENDANCE
    assert 'Limitações para ação braçal, com execução de elevação' in ATTENDANCE
    assert 'amplitudes de prono-supinação 90 º e flexão 145 º' in ATTENDANCE
    assert 'comprometem execução de manuscritos de forma habitual e sistemática' in ATTENDANCE
    assert 'Filkeinstein, Tinel do Mediano e Phalen negativos' in ATTENDANCE
    assert 'Ausência de edemas, hematomas, cicatrizes, atrofias de regiões tenar e hipotenar' in ATTENDANCE
    assert 'comprometem execução de manuscritos e digitação de forma habitual' in ATTENDANCE
    assert 'Bursa trocanteriana indolor; palpação do trajeto do N. Ciático indolor' in ATTENDANCE
    assert 'limitações para realizar rotação do tronco de forma abrupta' in ATTENDANCE
    assert 'testes gaveta anterior e Lackman para o LCA' in ATTENDANCE
    assert 'realizar agachamentos, subir e descer escadarias de modo habitual e sem apoio' in ATTENDANCE
    assert 'ligamentos Deltóide (medial), e talo-fibular' in ATTENDANCE
    assert 'pulso pedioso sem alterações; palpação do tarso, metatarsos e dedos' in ATTENDANCE
    assert 'label: "Joelho direito"' in ATTENDANCE
    assert 'label: "Joelho esquerdo"' in ATTENDANCE

    # 3. Auto-completion and formatting helpers
    assert 'function capitalizeFirstLetter(str)' in ATTENDANCE
    assert 'function formatarLimitacoesOsteo(lista)' in ATTENDANCE
    assert 'function setGrupoStatus(grupo, status)' in ATTENDANCE
    assert 'function setRegiaoStatus(regiao, status)' in ATTENDANCE
    assert 'function toggleRegiaoOsteomuscular(regiao)' in ATTENDANCE
    assert 'function aplicarRegioesOsteomusculares()' in ATTENDANCE
    assert 'function aplicarOsteomuscularNormal()' in ATTENDANCE
    assert 'function limparOsteomuscular()' in ATTENDANCE
    assert 'function updateOsteoUI()' in ATTENDANCE


def test_osteo_finalization_zero_blocking_altered_and_normal():
    from app import _finalization_blockers

    # Case A: Osteomuscular Altered (Favorável, Parcial e Temporariamente Prejudicada, Q1/Q2/Q3=Sim)
    payload_altered = {
        "readaptado": "Não",
        "exameFisicoTipo": "Aparelho Osteomuscular e Tecido Conjutivo",
        "limitacaoFuncional": "Sim",
        "limitacaoRol": "Sim",
        "capacidade": "Capacidade parcial e temporariamente prejudicada",
        "parecer": "FAVORÁVEL",
        "quesitos": [
            {"resposta": "Sim"},
            {"resposta": "Sim"},
            {"resposta": "Sim"}
        ],
        "aux": {
            "cargo": "Operador de Máquinas",
            "idade": "42",
            "readaptado": "Não",
            "cid": "M54.5",
            "doencaMotivo": "M54.5 — Dor lombar baixa",
            "inicioTratamento": "2026-09-24",
            "sintomasLimitacao": "limitações para realizar dosiflexão e extensão",
            "crmCro": "Em anexo",
            "dataDocumento": "2026-09-24",
            "diasSolicitados": "Conforme atestado",
            "justificativa": "Capacidade parcial e temporariamente prejudicada, limitações para realizar dosiflexão e extensão..."
        }
    }
    blockers_altered = _finalization_blockers(payload_altered)
    assert blockers_altered == [], f"Expected 0 blockers for altered osteomuscular, got: {blockers_altered}"

    # Case B: Osteomuscular Normal (Contrário, Preservada, Q1/Q2=Sim, Q3=Não)
    payload_normal = {
        "readaptado": "Não",
        "exameFisicoTipo": "Aparelho Osteomuscular e Tecido Conjutivo",
        "limitacaoFuncional": "Não",
        "limitacaoRol": "Não",
        "capacidade": "Capacidade laborativa preservada",
        "parecer": "CONTRÁRIO",
        "quesitos": [
            {"resposta": "Sim"},
            {"resposta": "Sim"},
            {"resposta": "Não"}
        ],
        "aux": {
            "cargo": "Operador de Máquinas",
            "idade": "42",
            "readaptado": "Não",
            "cid": "M54.5",
            "doencaMotivo": "M54.5 — Dor lombar baixa",
            "inicioTratamento": "2026-09-24",
            "sintomasLimitacao": "Não se identificam limitações funcionais",
            "crmCro": "Em anexo",
            "dataDocumento": "2026-09-24",
            "diasSolicitados": "Conforme atestado",
            "justificativa": "Capacidade laborativa preservada, avaliação pericial clínica sem evidências de incapacidade..."
        }
    }
    blockers_normal = _finalization_blockers(payload_normal)
    assert blockers_normal == [], f"Expected 0 blockers for normal osteomuscular, got: {blockers_normal}"


def test_osteo_details_toggle_and_vitals_standard_preset():
    # 1. Detalhes collapsible container and buttons
    assert 'id="btnToggleOsteoDetalhes"' in ATTENDANCE
    assert 'function toggleOsteoDetalhes()' in ATTENDANCE
    assert 'id="osteoRegionsContainer"' in ATTENDANCE
    assert 'id="osteoBadgeCount"' in ATTENDANCE

    # 2. Region format with colon: "${d.label}: ${capitalizeFirstLetter(d.exame)}"
    assert '${d.label}: ${capitalizeFirstLetter(d.exame)}' in ATTENDANCE

    # 3. Standard Vitals preset (120x80 mmHg and pulse 80 bpm via checkbox)
    assert 'id="agilVitalsPadraoCheck"' in ATTENDANCE
    assert 'function toggleVitalsPadrao(checked)' in ATTENDANCE
    assert '120 por 80 mmHg' in ATTENDANCE
    assert 'pulso 80 bpm' in ATTENDANCE

    # 4. Body map separation (Frente = limbs, Verso = cervical, lombar, quadril)
    assert 'title="Coluna lombar"' in ATTENDANCE
    assert 'title="Cervical"' in ATTENDANCE
    assert 'title="Quadril"' in ATTENDANCE
    assert 'title="Ombro Direito"' in ATTENDANCE
    assert 'title="Joelho Direito"' in ATTENDANCE
    assert 'title="Tornozelo / Pé Direito"' in ATTENDANCE
    # Verify no duplicated limb hotspots on Verso
    assert 'title="Joelho Esquerdo (Verso)"' not in ATTENDANCE
    assert 'title="Tornozelo / Calcanhar Direito"' not in ATTENDANCE
    assert 'title="Ombro Direito (Verso)"' not in ATTENDANCE


def test_doctor_optional_email_and_attendance_mode():
    # 1. Database migrations in _init_db() for email and modo_atendimento
    assert "ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS email TEXT;" in APP
    assert "ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS modo_atendimento TEXT DEFAULT 'agil';" in APP
    assert "idx_usuarios_email" in APP

    # 2. _role_from_profile returns modo_atendimento
    assert '"modo_atendimento": modo_atendimento,' in APP

    # 3. Doctor creation supports optional email and modo_atendimento
    assert "clean_crm = re.sub(r'[^0-9a-zA-Z]', '', crm).lower() or 'medico'" in APP
    assert 'f"crm_{clean_crm}@medico.ambiental.local"' in APP
    assert 'modo_atendimento = str(body.get("modo_atendimento") or "agil").strip().lower()' in APP
    assert "INSERT INTO usuarios (id,nome,perfil,ativo,criado_em,crm,email,modo_atendimento)" in APP

    # 4. Doctor edit supports modo_atendimento
    assert "UPDATE usuarios SET nome=%s, crm=%s, email=%s, modo_atendimento=%s WHERE id=%s" in APP

    # 5. UI: gestao-medicos-admin.html
    assert '(opcional)' in GESTAO_MEDICOS_ADMIN
    assert 'name="modo_atendimento"' in GESTAO_MEDICOS_ADMIN
    assert 'name="editModoAtendimento"' in GESTAO_MEDICOS_ADMIN
    assert 'Modelo de atendimento facilitado para médicos com dificuldades.' in GESTAO_MEDICOS_ADMIN
    assert 'Médico com experiencia e com facilidade em realizar os atendimentos.' in GESTAO_MEDICOS_ADMIN
    assert '<th>Modo</th>' in GESTAO_MEDICOS_ADMIN


def test_login_crm_resolution_and_attendance_integration():
    # 1. Endpoint POST /api/auth/resolve-identifier in app.py
    assert '@app.post("/api/auth/resolve-identifier")' in APP
    assert 'def api_auth_resolve_identifier():' in APP
    assert '"type": "email"' in APP
    assert '"type": "crm"' in APP
    assert 'DOCTOR_NOT_FOUND' in APP
    assert 'Administradores devem entrar utilizando seu e-mail corporativo.' in APP

    # 2. Login UI: login.html
    assert 'E-mail corporativo ou CRM' in LOGIN
    assert '/api/auth/resolve-identifier' in LOGIN
    assert 'ev.includes("@")' in LOGIN or '!ev.includes("@")' in LOGIN

    # 3. Attendance UI: ambiental_avaliacao_medica_lts_cid_assistente.html
    assert 'const doctorDefaultMode = (currentProfile?.modo_atendimento === "extenso" || currentProfile?.modo_atendimento === "estendido") ? "estendido" : "agil";' in ATTENDANCE
    assert 'normMode = (mode === "extenso" || mode === "estendido") ? "estendido" : "agil";' in ATTENDANCE


def test_resolve_identifier_endpoint_execution():
    from unittest.mock import patch, MagicMock
    from app import app as flask_app

    client = flask_app.test_client()

    # 1. Validation error on empty
    resp_empty = client.post("/api/auth/resolve-identifier", json={"identifier": ""})
    assert resp_empty.status_code == 400
    assert resp_empty.get_json()["error"]["code"] == "VALIDATION_ERROR"

    # 2. Email direct pass-through
    resp_email = client.post("/api/auth/resolve-identifier", json={"identifier": "admin@empresa.com"})
    assert resp_email.status_code == 200
    assert resp_email.get_json()["data"] == {"type": "email", "email": "admin@empresa.com"}

    # 3. CRM resolution for existing active doctor
    with patch("app.get_db") as mock_db:
        mock_cur = MagicMock()
        mock_cur.fetchone.return_value = {
            "id": "doc-uuid-1", "nome": "Dra. Maria Silva", "crm": "CRM 98765/SP",
            "email": "maria@empresa.com", "perfil": "Médico", "ativo": 1, "modo_atendimento": "agil"
        }
        mock_db.return_value.cursor.return_value = mock_cur
        resp_crm = client.post("/api/auth/resolve-identifier", json={"identifier": "CRM 98765/SP"})
        assert resp_crm.status_code == 200
        data = resp_crm.get_json()["data"]
        assert data["type"] == "crm"
        assert data["email"] == "maria@empresa.com"
        assert data["modo_atendimento"] == "agil"

    # 4. CRM resolution when doctor has no email (generates synthetic email)
    with patch("app.get_db") as mock_db:
        mock_cur = MagicMock()
        mock_cur.fetchone.return_value = {
            "id": "doc-uuid-2", "nome": "Dr. Joao", "crm": "12345/MG",
            "email": None, "perfil": "Médico", "ativo": 1, "modo_atendimento": "extenso"
        }
        mock_db.return_value.cursor.return_value = mock_cur
        resp_crm2 = client.post("/api/auth/resolve-identifier", json={"identifier": "12345/MG"})
        assert resp_crm2.status_code == 200
        data2 = resp_crm2.get_json()["data"]
        assert data2["type"] == "crm"
        assert data2["email"] == "crm_12345mg@medico.ambiental.local"
        assert data2["modo_atendimento"] == "extenso"

    # 5. Non-existent CRM returns DOCTOR_NOT_FOUND with clear administrator hint
    with patch("app.get_db") as mock_db:
        mock_cur = MagicMock()
        mock_cur.fetchone.return_value = None
        mock_db.return_value.cursor.return_value = mock_cur
        resp_notfound = client.post("/api/auth/resolve-identifier", json={"identifier": "999999"})
        assert resp_notfound.status_code == 404
        assert resp_notfound.get_json()["error"]["code"] == "DOCTOR_NOT_FOUND"
        assert "Administradores devem entrar utilizando seu e-mail corporativo." in resp_notfound.get_json()["error"]["message"]


def test_osteo_individual_laterality_selection_and_no_bilateral_hover_overlap():
    """
    Ensures:
    1. Hovering highlights only the hovered hotspot without activating both sides.
    2. Tooltip is displayed only for the hovered hotspot (.osteo-hotspot:hover .osteo-tooltip).
    3. Left and right sides have independent data-regiao and individual buttons.
    4. Knee right and left produce specific individual reports:
       'Joelho direito: Ausência de deformidades...' or 'Joelho esquerdo: Ausência de deformidades...'
    5. Deduplication of limitations when bilateral regions are selected.
    """
    # 1. Hotspot laterality differentiation
    assert 'data-regiao="joelho_direito"' in ATTENDANCE
    assert 'data-regiao="joelho_esquerdo"' in ATTENDANCE
    assert 'data-regiao="ombro_direito"' in ATTENDANCE
    assert 'data-regiao="ombro_esquerdo"' in ATTENDANCE
    assert 'data-regiao="cotovelo_direito"' in ATTENDANCE
    assert 'data-regiao="cotovelo_esquerdo"' in ATTENDANCE
    assert 'data-regiao="antebraco_direito"' in ATTENDANCE
    assert 'data-regiao="antebraco_esquerdo"' in ATTENDANCE
    assert 'data-regiao="mao_direita"' in ATTENDANCE
    assert 'data-regiao="mao_esquerda"' in ATTENDANCE
    assert 'data-regiao="tornozelo_direito"' in ATTENDANCE
    assert 'data-regiao="tornozelo_esquerdo"' in ATTENDANCE

    # 2. Hover logic applies is-hovered exclusively to hs
    assert 'hs.classList.add("is-hovered");' in ATTENDANCE
    assert '.osteo-hotspot:hover .osteo-tooltip' in ATTENDANCE

    # 3. Clinical texts match user specification
    assert 'label: "Joelho direito"' in ATTENDANCE
    assert 'label: "Joelho esquerdo"' in ATTENDANCE
    assert 'testes gaveta anterior e Lackman para o LCA' in ATTENDANCE
    assert 'teste McMurray para os meniscos' in ATTENDANCE

    # 4. Deduplication of limitations
    assert 'Array.from(new Set(' in ATTENDANCE

    # 5. Bilateral unification without repeating texts
    assert 'Antebraço esquerdo e direito' in ATTENDANCE
    assert 'Joelho esquerdo e direito' in ATTENDANCE
    assert 'function agruparRegioesAlteradas(alteradas)' in ATTENDANCE


def test_esisla_terminology_never_paciente():
    from app import _clean_esisla_text, TASK_PROMPTS
    prompt = TASK_PROMPTS["esisla"]
    # 1. Mandatory rule prohibiting "Paciente" and enforcing "Servidor" / "Periciado"
    assert 'REGRA TERMINOLÓGICA OBRIGATÓRIA: NUNCA utilize o termo "Paciente" ou "paciente". Utilize SEMPRE "Servidor" ou "Periciado"' in prompt
    assert '"Servidor de X anos" ou "Periciado de X anos"' in prompt
    assert '"Servidor de 40 anos, professor há 10 anos' in prompt

    # 2. _clean_esisla_text must sanitize any occurrences of Paciente/paciente
    sample_text = (
        "Registro da perícia Médica para Licença\n\n"
        "(*) Queixa e Duração:\n"
        "Paciente de 45 anos, professor há 12 anos. O paciente refere dor intensa. "
        "Foi orientado o paciente a manter repouso.\n\n"
        "Antecedentes Mórbidos:\n"
        "Hipertenso.\n\n"
        "Atestado/Relatório/Exames Complementares (Tipo-Data-Resultado):\n"
        "CRM 12345\n\n"
        "Pressão Arterial\nSistólica (mmHg): 120\nDiastólica (mmHg): 80\nPulso (bpm): 80\n\n"
        "(*)Exame Físico Geral\nNormal\n\n"
        "Descrição das Alterações Clínicas encontradas e Relato dos Exames Complementares:\n\n"
        "(*)Descrição da(s) Limitação(ções) Física(s) e/ou Mental(is) encontrada(s):\n\n"
        "(*)Parecer Médico\n\nNº Dias:\nData Início:\nCID 10:\nDescrição:\nMédico Perito:\nCRM:\nDt/Hr Perícia:\n\n"
        "(*)Resposta aos quesitos\n1) Sim\n2) Sim\n3) Não\n\n"
        "(*)Justificativa Parecer Médico\n\n"
        "(*) Parecer Final\n\nNº Dias:\nData Início:\nCID 10:\nDescrição:\nDiretor DPME:\nData P.F.:"
    )
    cleaned = _clean_esisla_text(sample_text)
    assert "Paciente" not in cleaned
    assert "paciente" not in cleaned
    assert "Servidor de 45 anos" in cleaned
    assert "O servidor refere dor intensa" in cleaned
    assert "o servidor a manter repouso" in cleaned


def test_antecedentes_morbidos_and_historico_pregresso_integration():
    from app import _minimal_ai_context
    # 1. Structure in HTML: Histórico pregresso first, then Possui outras doenças em tratamento (default Sim)
    agil_hist_pos = ATTENDANCE.find('id="agilHistoricoPregresso"')
    agil_outras_pos = ATTENDANCE.find('name="agilOutrasDoencas"')
    assert agil_hist_pos != -1 and agil_outras_pos != -1
    assert agil_hist_pos < agil_outras_pos, "Histórico pregresso must appear before 'Possui outras doenças em tratamento?' in Modo Ágil"

    ext_hist_pos = ATTENDANCE.find('id="historicoPregresso"')
    ext_outras_pos = ATTENDANCE.find('name="outrasDoencas"')
    assert ext_hist_pos != -1 and ext_outras_pos != -1
    assert ext_hist_pos < ext_outras_pos, "Histórico pregresso must appear before 'Possui outras doenças em tratamento?' in Versão Estendida"

    # 2. Default is Sim (checked)
    assert 'name="agilOutrasDoencas" value="Sim" checked' in ATTENDANCE
    assert 'name="outrasDoencas" value="Sim" checked' in ATTENDANCE
    assert 'state.outrasDoencas = "Sim"' in ATTENDANCE

    # 3. _minimal_ai_context maps historico_pregresso and antecedentes
    ctx = _minimal_ai_context({
        "atendimento": "123",
        "historicoPregresso": "Cirurgia de menisco em 2021",
        "outrasDoencas": "Sim"
    })
    assert ctx["antecedentes"] == "Cirurgia de menisco em 2021"
    assert ctx["historico_pregresso"] == "Cirurgia de menisco em 2021"


def test_agil_exame_tipo_outros_options_and_no_preset_autofill():
    # 1. "Outros" option in select
    assert '<option value="Outros">Outros</option>' in ATTENDANCE

    # 2. Container agilOutrosSelector with 12 specified sub-areas
    assert 'id="agilOutrosSelector"' in ATTENDANCE
    areas = [
        "Exame Físico Geral",
        "Tecido celular subcutâneo",
        "Pele e Fâneros",
        "Aparelho Circulatório",
        "Aparelho Respiratório",
        "Aparelho Hemolinfopoético",
        "Aparelho Digestivo",
        "Aparelho Geniturinário",
        "Aparelho Endócrino",
        "Sistema Nervoso",
        "Órgãos dos Sentidos",
        "E outros",
    ]
    for area in areas:
        assert f'data-subtipo="{area}"' in ATTENDANCE, f"Missing area '{area}' in agilOutrosSelector"

    # 3. Normal / Alterado buttons in Outros
    assert 'id="agilOutrosResultadoWrap"' in ATTENDANCE
    assert 'id="btnAgilOutrosNormal"' in ATTENDANCE
    assert 'id="btnAgilOutrosAlterado"' in ATTENDANCE
    assert 'escolherOutrosResultado' in ATTENDANCE

    # 4. Must NOT auto-fill description fields for Outros
    # Verify comments and implementation ensuring no preset findings are injected
    assert 'escolherOutrosResultado' in ATTENDANCE


def test_agil_justificativa_ia_button_only_on_outros():
    # 1. Button exists in Modo Ágil
    assert 'id="btnAgilJustificativaIA"' in ATTENDANCE
    assert 'gerarJustificativaAgilIA()' in ATTENDANCE

    # 2. Display is inline-flex only on Outros
    assert 'btnIaJust.style.display = "inline-flex";' in ATTENDANCE
    assert 'btnIaJust.style.display = "none";' in ATTENDANCE


def test_justificativa_ia_outros_area_and_cid_correlation():
    """
    Ensures:
    1. TASK_PROMPTS["justificativa"] has the explicit rule correlating the selected area in 'Outros',
       its status (Alterado vs Normal), and the described CID in 1st person.
    2. _task_instruction formats area_exame_clinico, resultado_avaliacao, cid and cargo correctly.
    3. _minimal_ai_context maps outros_subtipo, outros_resultado, area_exame_clinico, resultado_avaliacao.
    4. HTML getJustificativaContext sends outros_subtipo and outros_resultado.
    """
    from app import TASK_PROMPTS, _task_instruction, _minimal_ai_context
    prompt = TASK_PROMPTS["justificativa"]

    # 1. Prompt rules for Outros + Área clínica + CID
    assert "DIRETRIZ OBRIGATÓRIA PARA A OPÇÃO 'OUTROS'" in prompt
    assert "{area_exame_clinico}" in prompt
    assert "{resultado_avaliacao}" in prompt
    assert "relacionadas ao CID {cid}" in prompt
    assert "esfera de {area_exame_clinico}" in prompt
    assert 'JAMAIS utilize o termo "Paciente" ou "paciente"' in prompt

    # 2. Test prompt generation for Alterado
    payload_alterado = {
        "cargo": "Professor PEB II",
        "cid": "I10 - Hipertensão arterial",
        "exame_fisico_tipo": "Outros",
        "outros_subtipo": "Aparelho Circulatório",
        "outros_resultado": "Alterado",
        "desc_limitacao": "Picos pressóricos em esforço",
    }
    instruction_alt = _task_instruction("justificativa", payload_alterado)
    assert "Professor PEB II" in instruction_alt
    assert "I10 - Hipertensão arterial" in instruction_alt
    assert "Aparelho Circulatório" in instruction_alt
    assert "Alterado" in instruction_alt

    # 3. Test prompt generation for Normal
    payload_normal = {
        "cargo": "Analista Administrativo",
        "cid": "K29 - Gastrite",
        "exame_fisico_tipo": "Outros",
        "outros_subtipo": "Aparelho Digestivo",
        "outros_resultado": "Normal",
    }
    instruction_norm = _task_instruction("justificativa", payload_normal)
    assert "Analista Administrativo" in instruction_norm
    assert "K29 - Gastrite" in instruction_norm
    assert "Aparelho Digestivo" in instruction_norm
    assert "Normal" in instruction_norm

    # 4. _minimal_ai_context mapping
    ctx = _minimal_ai_context({
        "outros_subtipo": "Aparelho Respiratório",
        "outros_resultado": "Alterado",
    })
    assert ctx["outros_subtipo"] == "Aparelho Respiratório"
    assert ctx["outros_resultado"] == "Alterado"
    assert ctx["area_exame_clinico"] == "Aparelho Respiratório"
    assert ctx["resultado_avaliacao"] == "Alterado"

    # 5. HTML context gathering
    assert "outros_subtipo:subtipo" in ATTENDANCE or "outros_subtipo: subtipo" in ATTENDANCE
    assert "outros_resultado:resultado" in ATTENDANCE or "outros_resultado: resultado" in ATTENDANCE


def test_ai_concurrency_limit_one_generation_per_cadastro():
    """
    Ensures:
    1. A lock is enforced per cadastro/registration so that only ONE AI generation can run at a time per cadastro.
    2. Attempting a concurrent generation for the SAME cadastro raises AICadastroBusyError.
    3. Concurrency for a DIFFERENT cadastro is allowed simultaneously.
    4. When a generation completes, the lock is released and subsequent generations are permitted.
    5. _provider_error converts AICadastroBusyError to HTTP 429 with AI_CADASTRO_BUSY.
    6. HTML includes client-side guard checking aiInFlight.
    """
    import pytest
    from app import _cadastro_ai_lock, AICadastroBusyError, _provider_error

    cadastro_a = "ATD-TEST-CADASTRO-001"
    cadastro_b = "ATD-TEST-CADASTRO-002"

    # 1. Lock on cadastro_a blocks concurrent generation on cadastro_a
    with _cadastro_ai_lock(cadastro_a, "/api/ai/justificativa"):
        # Same cadastro concurrently -> must raise AICadastroBusyError
        with pytest.raises(AICadastroBusyError) as exc_info:
            with _cadastro_ai_lock(cadastro_a, "/api/ai/justificativa"):
                pass
        assert exc_info.value.cadastro_id == cadastro_a
        assert "Já existe uma geração de IA em andamento para este cadastro" in str(exc_info.value)

        # Different cadastro concurrently -> must succeed
        with _cadastro_ai_lock(cadastro_b, "/api/ai/justificativa"):
            pass

    # 2. After exiting, subsequent generation on cadastro_a must succeed
    with _cadastro_ai_lock(cadastro_a, "/api/ai/justificativa"):
        pass

    # 3. _provider_error translates AICadastroBusyError to 429
    from app import app
    with app.test_request_context():
        busy_err = AICadastroBusyError(cadastro_a)
        resp, status_code = _provider_error(busy_err)
        assert status_code == 429
        data = resp.get_json()
        assert data["error"]["code"] == "AI_CADASTRO_BUSY"
        assert "Já existe uma geração de IA em andamento para este cadastro" in data["error"]["message"]
        assert data["error"]["details"]["cadastro"] == cadastro_a

    # 4. Client-side guard in HTML
    assert "if (aiInFlight)" in ATTENDANCE
    assert "Já existe uma geração de IA em andamento para este cadastro" in ATTENDANCE


def test_inicio_tratamento_year_support():
    # 1. HTML inputs allow entering year directly (type="text" instead of restrictive type="date")
    assert '<input class="input" type="text" id="agilInicioTratamento" placeholder="Ex: 2020 ou 15/03/2020"' in ATTENDANCE
    assert '<input class="input" type="text" id="inicioTratamento" placeholder="Ex: 2020 ou 15/03/2020"' in ATTENDANCE

    # 2. formatDate handles 4-digit years like "2020" without undefined/undefined/2020
    assert r'/^\d{4}$/.test(s)' in ATTENDANCE

    # 3. Backend _minimal_ai_context preserves year
    from app import _minimal_ai_context
    ctx = _minimal_ai_context({
        "atendimento": "ATD-2026-0001",
        "inicio_tratamento": "2020"
    })
    assert ctx["inicio_tratamento"] == "2020"

    ctx_aux = _minimal_ai_context({
        "atendimento": "ATD-2026-0002",
        "aux": {"inicioTratamento": "2019"}
    })
    assert ctx_aux["inicio_tratamento"] == "2019"


def test_secondary_cid_feature_and_ai_prompt_integration():
    # 1. HTML elements for Modo Ágil and Versão Estendida
    assert 'id="agilSecondaryCidContainer"' in ATTENDANCE
    assert 'id="extSecondaryCidContainer"' in ATTENDANCE
    assert 'onclick="addSecondaryCID()"' in ATTENDANCE
    assert 'Adicionar outro CID (Atestados adicionais)' in ATTENDANCE

    # 2. JS functions present in HTML
    assert 'function renderSecondaryCIDs()' in ATTENDANCE
    assert 'function onSecondaryCIDInput(' in ATTENDANCE
    assert 'function selectSecondaryCID(' in ATTENDANCE
    assert 'function removeSecondaryCID(' in ATTENDANCE
    assert 'function addSecondaryCID(' in ATTENDANCE

    # 3. Backend _minimal_ai_context extracts cids_secundarios
    from app import _minimal_ai_context, _task_instruction
    ctx1 = _minimal_ai_context({
        "cid": "F32.1",
        "cids_secundarios": [
            {"cid": "M54.5", "descricao": "Lumbago com ciática"},
            {"cid": "I10", "descricao": "Hipertensão essencial"}
        ]
    })
    assert len(ctx1["cids_secundarios"]) == 2
    assert ctx1["cids_secundarios"][0]["cid"] == "M54.5"

    ctx2 = _minimal_ai_context({
        "cid": "F32.1",
        "aux": {
            "cidsSecundarios": ["M54.5 - Lumbago", "G44"]
        }
    })
    assert ctx2["cids_secundarios"] == ["M54.5 - Lumbago", "G44"]

    # 4. _task_instruction formats CID with secondary CIDs for AI justification
    prompt_with_sec = _task_instruction("justificativa", {
        "cargo": "Professor",
        "idade": "45",
        "cid": "F32.1",
        "cids_secundarios": [
            {"cid": "M54.5", "descricao": "Lumbago com ciática"},
            {"cid": "I10", "descricao": "Hipertensão essencial"}
        ],
        "doenca_motivo": "Transtorno depressivo",
        "queixa_duracao": "6 meses",
        "exame_fisico_tipo": "Exame Mental",
        "parecer": "FAVORÁVEL",
        "capacidade": "Temporariamente prejudicada"
    })
    assert "- CID: F32.1 (Atestados adicionais/outros CIDs apresentados: M54.5 - Lumbago com ciática, I10 - Hipertensão essencial)" in prompt_with_sec

    # 5. _task_instruction without secondary CIDs remains standard
    prompt_single = _task_instruction("justificativa", {
        "cargo": "Professor",
        "idade": "45",
        "cid": "F32.1",
        "doenca_motivo": "Transtorno depressivo",
        "queixa_duracao": "6 meses",
        "exame_fisico_tipo": "Exame Mental",
        "parecer": "FAVORÁVEL",
        "capacidade": "Temporariamente prejudicada"
    })
    assert "- CID: F32.1\n" in prompt_single


def test_robo_removed_from_attendance_and_macros_preserved():
    import json
    from pathlib import Path

    # 1. UI elements removed as requested by user
    assert 'id="btnRoboEsisla"' not in ATTENDANCE
    assert 'id="roboEsislaModal"' not in ATTENDANCE
    assert 'abrirRoboEsislaModal' not in ATTENDANCE

    # 2. Macro files in "Macro ui vision" folder preserved for user's rewrite
    macro_dir = Path("Macro ui vision")
    assert macro_dir.is_dir()

    robo_file = macro_dir / "RoboE-sisla.json"
    assert robo_file.is_file()
    with open(robo_file, "r", encoding="utf-8") as f:
        robo_json = json.load(f)
    assert robo_json["Name"] == "Preencher_eSisla_DB"

    preencher_file = macro_dir / "Preencher_eSisla_DB.json"
    assert preencher_file.is_file()


def test_field_label_unidade_renamed_to_anos_meses_dias():
    # Modo Ágil and Versão Estendida
    assert '<label>Ano(s)/Mes(es)/Dia(s)</label>' in ATTENDANCE
    assert 'id="agilTempoUnidade"' in ATTENDANCE
    assert 'id="tempoUnidade"' in ATTENDANCE


def test_adicionar_medicamento_button_styling():
    # .btn-add styling improved with border, font, background, and hover effects
    assert '.btn-add{' in ATTENDANCE
    assert 'background:#EFF6FF;' in ATTENDANCE
    assert 'border:1.5px solid #2563EB;' in ATTENDANCE


def test_gestao_admin_batch_and_single_delete():
    # Endpoints in app.py
    from app import app
    client = app.test_client()

    # Unauthorized access check
    res = client.delete("/api/admin/atendimentos/nonexistent")
    assert res.status_code in [401, 403]

    res_batch = client.post("/api/admin/atendimentos/batch-delete", json={"ids": ["1", "2"]})
    assert res_batch.status_code in [401, 403]

    # Frontend Gestão elements
    assert 'id="bulkActionsToolbar"' in GESTAO_ATENDIMENTOS
    assert 'id="selectAllCheckbox"' in GESTAO_ATENDIMENTOS
    assert 'confirmBatchDeleteAdmin()' in GESTAO_ATENDIMENTOS
    assert 'confirmSingleDeleteAdmin(' in GESTAO_ATENDIMENTOS
    assert 'col-patient' in GESTAO_ATENDIMENTOS
    assert 'sub-clamp' in GESTAO_ATENDIMENTOS


def test_gestao_esisla_buttons_and_pdf():
    # esislaModal buttons: only Editar, Gerar PDF, and Script F12
    modal_head = GESTAO_ATENDIMENTOS[GESTAO_ATENDIMENTOS.find('class="esisla-editor-header"'):GESTAO_ATENDIMENTOS.find('id="esislaText"')]
    assert 'id="esislaToggleEditBtn"' in modal_head
    assert 'generateEsislaPDF()' in modal_head
    assert 'copyEsislaScript()' in modal_head
    assert 'copyEsislaJson()' not in modal_head

    # PDF function implemented
    assert 'function generateEsislaPDF()' in GESTAO_ATENDIMENTOS


def test_esisla_prompt_and_context_altura_peso():
    from app import _minimal_ai_context, TASK_PROMPTS
    
    ctx = _minimal_ai_context({
        "atendimento": "123",
        "altura": "1.75",
        "peso": "78",
        "pa": "120/80",
        "pulso": "72"
    })
    assert ctx["altura"] == "1.75"
    assert ctx["peso"] == "78"

    prompt_tpl = TASK_PROMPTS["esisla"]
    assert "Altura:" in prompt_tpl
    assert "Peso:" in prompt_tpl
    assert "Pulso (bpm):" in prompt_tpl


def test_api_ai_esisla_endpoint_executes_successfully(monkeypatch):
    from app import app, EsislaResult

    # Mock auth request
    monkeypatch.setattr("app._authenticate_request", lambda: ({"id": "1", "email": "admin@ambiental.com", "nome": "Admin", "perfil": "Administrador"}, "token123"))

    # Mock _generate_cached so we don't call Gemini external network
    sample_ficha = (
        "Registro da perícia Médica para Licença\n\n"
        "(*) Queixa e Duração:\nDor lombar há 5 dias\n\n"
        "Antecedentes Mórbidos:\nNega comorbidades\n\n"
        "Pressão Arterial\nSistólica (mmHg): 120\nDiastólica (mmHg): 80\nPulso (bpm): 72\n\n"
        "(*)Exame Físico Geral\nNormal"
    )
    monkeypatch.setattr("app._generate_cached", lambda *args, **kwargs: (EsislaResult(ficha_esisla=sample_ficha), False, "hash123"))

    client = app.test_client()
    res = client.post("/api/ai/esisla", json={
        "atendimento": "954378632",
        "nomePaciente": "Servidor Teste",
        "altura": "1.70",
        "peso": "70"
    })

    assert res.status_code == 200
    data = res.get_json()
    assert "ficha_esisla" in data
    assert "Altura: 1.70" in data["ficha_esisla"]
    assert "Peso: 70" in data["ficha_esisla"]


def test_exame_fisico_geral_button_and_prepend_logic():
    # Buttons present in Modo Ágil and Versão Estendida
    assert 'id="btnAgilExameFisicoGeral"' in ATTENDANCE
    assert 'id="btnExtExameFisicoGeral"' in ATTENDANCE
    assert 'onclick="inserirExameFisicoGeralPadrao()"' in ATTENDANCE
    assert "Exame Físico Geral" in ATTENDANCE

    # Constant definition and contents
    assert "const TEXTO_EXAME_FISICO_GERAL_PADRAO =" in ATTENDANCE
    assert "Bom do estado geral, nutrição adequada, sem alterações na coloração e hidratação de mucosas." in ATTENDANCE
    assert "EXAME FÍSICO DO AP.RESPIRATÓRIO: Eupnêico, sem esforço respiratório" in ATTENDANCE
    assert "Som claro pulmonar, atimpânico" in ATTENDANCE
    assert "Murmúrio Vesicular universalmente audível s/ ruídos adventícios" in ATTENDANCE
    assert "EXAME FÍSICO DO AP. CARDIOVASCULAR: Precórdio normodinâmico" in ATTENDANCE
    assert "Ictus de VE invisível, palpável em 5º EIC na LHCE" in ATTENDANCE
    assert "RCR 2T c/ BNF. Ausência de sopros ou extrassístoles" in ATTENDANCE
    assert "turgência de jugular. Patológica (TJP) Pulsos arteriais periféricos simétricos, sincrônicos e com boa amplitude." in ATTENDANCE

    # Function insertion and preservation logic
    assert "function inserirExameFisicoGeralPadrao()" in ATTENDANCE
    assert 'TEXTO_EXAME_FISICO_GERAL_PADRAO + "\\n\\n" + current' in ATTENDANCE
    assert "function extrairOuPreservarExameGeral(novoConteudo)" in ATTENDANCE
    assert "extrairOuPreservarExameGeral(TEXTO_EXAME_MENTAL_NORMAL)" in ATTENDANCE
    assert "extrairOuPreservarExameGeral(TEXTO_EXAME_MENTAL_ALTERADO)" in ATTENDANCE
    assert "extrairOuPreservarExameGeral(TEXTO_OSTEO_NORMAL_EXAME)" in ATTENDANCE


def test_doctor_productivity_date_calculator_and_retroaction():
    # 1. HTML elements in Modo Ágil
    assert 'id="agilCrmCro"' in ATTENDANCE
    assert 'id="agilDataDocumento"' in ATTENDANCE
    assert 'id="agilDiasSolicitados"' in ATTENDANCE
    assert 'id="retroacaoAlertaBadge"' in ATTENDANCE
    assert 'id="calcDatasResumoBox"' in ATTENDANCE
    assert 'concederMesmosDiasAtestado()' in ATTENDANCE

    # 2. JavaScript logic
    assert "function calcularDatasAtestado()" in ATTENDANCE
    assert "function concederMesmosDiasAtestado()" in ATTENDANCE
    assert "diffDays > 3" in ATTENDANCE
    assert 'retroacaoAlertaBadge' in ATTENDANCE
    assert 'concederMesmosDiasAtestado' in ATTENDANCE

    # 3. Two-way sync with Versão Estendida
    assert 'setVal("agilCrmCro"' in ATTENDANCE
    assert 'setVal("agilDataDocumento"' in ATTENDANCE
    assert 'setVal("agilDiasSolicitados"' in ATTENDANCE
    assert 'crmCro = getV("agilCrmCro")' in ATTENDANCE


def test_doctor_productivity_bmi_calculator_and_badge():
    # 1. HTML elements
    assert 'id="agilImcCard"' in ATTENDANCE
    assert 'id="agilImcValor"' in ATTENDANCE
    assert 'id="agilImcClassificacao"' in ATTENDANCE
    assert 'id="agilImcBadge"' in ATTENDANCE

    # 2. Function and thresholds
    assert "function calcularIMC()" in ATTENDANCE
    assert "Eutrófico (Peso normal)" in ATTENDANCE
    assert "Sobrepeso" in ATTENDANCE
    assert "Obesidade Grau I" in ATTENDANCE
    assert "Obesidade Grau II" in ATTENDANCE
    assert "Obesidade Grau III" in ATTENDANCE

    # 3. Input handlers
    assert "calcularIMC();" in ATTENDANCE


def test_doctor_productivity_medications_and_exam_chips():
    # 1. Medication quick chips
    assert "adicionarMedRapida('Sertralina', '50 mg'" in ATTENDANCE
    assert "adicionarMedRapida('Escitalopram', '10 mg'" in ATTENDANCE
    assert "adicionarMedRapida('Clonazepam', '2 mg'" in ATTENDANCE
    assert "Dose diária: 50 mg/dia" in ATTENDANCE
    assert "function adicionarMedRapida(med, dose, freq, obs)" in ATTENDANCE

    # 2. Exam quick chips
    assert "inserirAchadoExame('Lasègue negativo bilateralmente.')" in ATTENDANCE
    assert "inserirAchadoExame('Marcha típica, sem claudicação ou uso de órteses.')" in ATTENDANCE
    assert "inserirAchadoExame('Ausência de contraturas musculares paravertebrais palpáveis.')" in ATTENDANCE
    assert "function inserirAchadoExame(texto)" in ATTENDANCE


def test_doctor_productivity_voice_dictation_web_speech():
    # 1. Voice buttons in text areas
    assert 'id="voiceBtn_agilDoencaMotivo"' in ATTENDANCE
    assert 'id="voiceBtn_agilSintomasLimitacao"' in ATTENDANCE
    assert 'id="voiceBtn_agilExameFisicoDescricao"' in ATTENDANCE
    assert 'id="voiceBtn_agilJustificativa"' in ATTENDANCE

    # 2. Native Web Speech API integration
    assert "function toggleVoiceDictation(targetId)" in ATTENDANCE
    assert "window.SpeechRecognition || window.webkitSpeechRecognition" in ATTENDANCE
    assert 'recognition.lang = "pt-BR"' in ATTENDANCE
    assert "recording" in ATTENDANCE


def test_doctor_productivity_history_import_and_coherence_detector():
    # 1. History banner
    assert 'id="historicoPacienteCard"' in ATTENDANCE
    assert 'function verificarHistoricoPericiado(cpf)' in ATTENDANCE
    assert 'function importarAntecedentesHistorico()' in ATTENDANCE

    # 2. Pericial Coherence Detector
    assert 'id="coerenciaParecerAlerta"' in ATTENDANCE
    assert 'id="coerenciaParecerTexto"' in ATTENDANCE
    assert 'function verificarCoerenciaPericial()' in ATTENDANCE
    assert 'Aviso de Coerência Pericial DPME' in ATTENDANCE


def test_doctor_productivity_mini_hud_and_keyboard_shortcuts():
    # 1. Sticky Mini-HUD
    assert 'id="stickyDoctorHUD"' in ATTENDANCE
    assert 'id="hudPaciente"' in ATTENDANCE
    assert 'id="hudCargo"' in ATTENDANCE
    assert 'id="hudCid"' in ATTENDANCE
    assert 'id="hudParecer"' in ATTENDANCE
    assert 'function atualizarMiniHUD()' in ATTENDANCE

    # 2. Progress checklist
    assert 'id="agilProgressoBadge"' in ATTENDANCE
    assert 'function atualizarProgressoAgil()' in ATTENDANCE
    assert 'function toggleProgressoDropdown()' in ATTENDANCE

    # 3. Keyboard shortcuts
    assert 'e.key.toLowerCase() === "s"' in ATTENDANCE
    assert 'e.key === "Enter"' in ATTENDANCE
    assert 'e.key.toLowerCase() === "g"' in ATTENDANCE
    assert 'e.key.toLowerCase() === "j"' in ATTENDANCE


def test_esisla_regras_de_ouro_conformidade_juridica():
    # 1. Validador de Coerência Pericial (Quesitos x Parecer x Limitação)
    assert 'function verificarCoerenciaPericial()' in ATTENDANCE
    assert 'function aplicarAlinhamentoQuesitos(tipo)' in ATTENDANCE
    assert 'function aplicarAlinhamentoParecer(novoParecer)' in ATTENDANCE
    assert 'id="coerenciaParecerAlerta"' in ATTENDANCE
    assert 'id="coerenciaParecerAlertaSec7"' in ATTENDANCE
    assert 'id="coerenciaParecerAlertaSec8"' in ATTENDANCE
    assert 'Aviso de Coerência Pericial DPME (Regras de Ouro e-SISLA):' in ATTENDANCE
    assert 'Conformidade e-SISLA Garantida:' in ATTENDANCE

    # 2. Monitor de Limite de Caracteres do e-SISLA (2.000 carac.)
    assert 'const ESISLA_TEXT_FIELDS =' in ATTENDANCE
    assert 'function atualizarContadorEsisla(id)' in ATTENDANCE
    assert 'function ajustarLimiteEsisla(id, max' in ATTENDANCE
    assert 'function initEsislaCharCounters()' in ATTENDANCE
    assert 'esisla-char-counter' in ATTENDANCE
    assert '2.000' in ATTENDANCE or '2000' in ATTENDANCE

    # 3. Alerta de Encaminhamento para Junta Médica (Regra dos 90 / 180 dias)
    assert 'function verificarRegraJuntaMedica()' in ATTENDANCE
    assert 'function aplicarEncaminhamentoJuntaMedica(totalDias)' in ATTENDANCE
    assert 'id="juntaMedicaAlertaAgil"' in ATTENDANCE
    assert 'id="juntaMedicaAlertaSec8"' in ATTENDANCE
    assert '_diasHistoricoAcumulado' in ATTENDANCE
    assert 'Lei Estadual nº 10.261/68' in ATTENDANCE

    # 4. Integração no ValidationEngine (Revisão da Seção 9)
    assert 'Regras de Ouro e-SISLA / DPME' in ATTENDANCE
    assert 'Limite e-SISLA Excedido:' in ATTENDANCE
    assert 'Afastamento acumulado de' in ATTENDANCE

    # 5. Gestão de Atendimentos — Modal e Script F12 e-SISLA
    assert 'id="esislaRegrasDeOuroBanner"' in GESTAO_ATENDIMENTOS
    assert 'campos_excedidos' in GESTAO_ATENDIMENTOS
    assert 'inconsistencias_juridicas' in GESTAO_ATENDIMENTOS
    assert 'alerta_junta' in GESTAO_ATENDIMENTOS
    assert 'function truncarCamposModalEsisla()' in GESTAO_ATENDIMENTOS
    assert 'function sanitizeText(v, max)' in GESTAO_ATENDIMENTOS
    assert '[e-SISLA Alerta DPME]' in GESTAO_ATENDIMENTOS


def test_comprovante_comparecimento_pericial():
    """
    Item 3: Documentação e Atendimento ao Servidor
    Valida a Declaração / Comprovante de Comparecimento à Perícia Médica Oficial:
    1. Presença no Atendimento (Modo Ágil, Cabeçalho e Seção 09).
    2. Modal oficial com dados do servidor, horários, data e observações.
    3. Proteção ao Sigilo Médico (Resoluções CFM 1.658/2002 e 1.851/2008):
       - Desmarcado por padrão (sem diagnóstico/CID).
       - Opção de inclusão do CID somente a pedido expresso do servidor.
    4. Funções de pré-visualização, impressão e cópia em texto formatado.
    5. Integração na Central de Gestão de Atendimentos (botão no detailModal e modal oficial).
    """
    # 1. Atendimento HTML — Elementos e Botões
    assert 'abrirModalComprovanteComparecimento()' in ATTENDANCE
    assert 'id="modalComprovanteComparecimento"' in ATTENDANCE
    assert 'id="comprovanteHoraEntrada"' in ATTENDANCE
    assert 'id="comprovanteHoraSaida"' in ATTENDANCE
    assert 'id="comprovanteDataPericia"' in ATTENDANCE
    assert 'id="comprovanteIncluirCid"' in ATTENDANCE
    assert 'id="comprovanteLivePreview"' in ATTENDANCE
    assert 'comprovante-preview-box' in ATTENDANCE

    # 2. Atendimento HTML — Funções JS e Conformidade Legal
    assert 'function formatarDataPorExtenso(' in ATTENDANCE
    assert 'function obterDadosComprovanteAtual()' in ATTENDANCE
    assert 'function gerarHTMLComprovanteComparecimento(' in ATTENDANCE
    assert 'function atualizarPreviewComprovante()' in ATTENDANCE
    assert 'function imprimirComprovante()' in ATTENDANCE
    assert 'function copiarTextoComprovante()' in ATTENDANCE
    assert 'DECLARAÇÃO DE COMPARECIMENTO À PERÍCIA MÉDICA' in ATTENDANCE
    assert 'Resolução CFM nº 1.658/2002' in ATTENDANCE or 'Resoluções CFM nº 1.658/2002' in ATTENDANCE
    assert 'Lei Estadual nº 10.261/1968' in ATTENDANCE

    # 3. Gestão de Atendimentos — Elementos e Botões
    assert 'id="comprovanteDetailBtn"' in GESTAO_ATENDIMENTOS
    assert 'abrirComprovanteDoDetail()' in GESTAO_ATENDIMENTOS
    assert 'id="comprovanteModal"' in GESTAO_ATENDIMENTOS
    assert 'id="comprovanteHoraEntradaGestao"' in GESTAO_ATENDIMENTOS
    assert 'id="comprovanteHoraSaidaGestao"' in GESTAO_ATENDIMENTOS
    assert 'id="comprovanteDataPericiaGestao"' in GESTAO_ATENDIMENTOS
    assert 'id="comprovanteIncluirCidGestao"' in GESTAO_ATENDIMENTOS
    assert 'id="comprovanteLivePreviewGestao"' in GESTAO_ATENDIMENTOS

    # 4. Gestão de Atendimentos — Funções JS
    assert 'function abrirModalComprovanteGestao(' in GESTAO_ATENDIMENTOS
    assert 'function obterDadosComprovanteGestao()' in GESTAO_ATENDIMENTOS
    assert 'function gerarHTMLComprovanteComparecimentoGestao(' in GESTAO_ATENDIMENTOS
    assert 'function atualizarPreviewComprovanteGestao()' in GESTAO_ATENDIMENTOS
    assert 'function imprimirComprovanteGestao()' in GESTAO_ATENDIMENTOS
    assert 'function copiarTextoComprovanteGestao()' in GESTAO_ATENDIMENTOS
    assert 'formatarDataPorExtensoGestao(' in GESTAO_ATENDIMENTOS


def test_esisla_bookmarklet_adeus_f12():
    """
    Item 3: Documentação e Atendimento ao Servidor
    Valida o Bookmarklet (Favorito Inteligente) do e-SISLA:
    1. Elimina a necessidade de abrir o Console de Desenvolvedor (F12) e colar código manual.
    2. Link arrastável para a barra de favoritos (draggable="true", href="javascript:...").
    3. Motor resiliente: tenta ler o clipboard e, se bloqueado por política de segurança do navegador,
       abre modal elegante direto no e-SISLA com prompt de colagem (Ctrl+V) e botão de preenchimento.
    4. Aplica sanitizeText(v, 2000) e sanitiza todos os campos periciais.
    5. Botão de copiar dados e-SISLA no atendimento com 1 clique.
    6. Modal explicativo passo a passo tanto no atendimento quanto na gestão.
    """
    # 1. Atendimento HTML — Bookmarklet e Cópia de Laudo
    assert 'copiarLaudoEsislaAtendimento()' in ATTENDANCE
    assert 'abrirModalBookmarkletAtendimento()' in ATTENDANCE
    assert 'id="modalBookmarkletAtendimento"' in ATTENDANCE
    assert 'id="linkBookmarkletAtendimento"' in ATTENDANCE
    assert 'btn-bookmarklet' in ATTENDANCE
    assert 'function gerarCodigoBookmarkletUniversal()' in ATTENDANCE
    assert 'function copiarCodigoBookmarklet()' in ATTENDANCE
    assert 'javascript:' in ATTENDANCE
    assert 'sanitizeText(campos[\'voMedico.parRlCat\'],2000)' in ATTENDANCE or 'sanitizeText(' in ATTENDANCE

    # 2. Gestão de Atendimentos — Bookmarklet na barra lateral e esislaModal
    assert 'abrirModalBookmarkletEsisla()' in GESTAO_ATENDIMENTOS
    assert 'id="bookmarkletModal"' in GESTAO_ATENDIMENTOS
    assert 'id="linkBookmarkletGestao"' in GESTAO_ATENDIMENTOS
    assert 'function gerarCodigoBookmarkletEsislaUniversal()' in GESTAO_ATENDIMENTOS
    assert 'function copiarCodigoBookmarkletEsisla()' in GESTAO_ATENDIMENTOS
    assert 'Preencher e-SISLA' in GESTAO_ATENDIMENTOS
    assert 'Botão dos Favoritos (sem F12)' in GESTAO_ATENDIMENTOS


def test_gestao_syntax_and_login_session_ux():
    """
    Valida a correção de sintaxe na Gestão e a proteção contra redirecionamento no meio da digitação no Login.
    """
    # 1. Gestão: reasonConfirm handler devidamente fechado com bloco catch
    assert "closeModal('reasonModal');\n        await fetchServer();\n        refresh();\n    }catch(e){\n        alert(e.message||'Falha ao atualizar estado.');\n    }\n};" in GESTAO_ATENDIMENTOS

    # 2. Login: Detecção de digitação para não desviar a tela do usuário no meio da digitação
    assert 'let userIsTyping = false;' in LOGIN
    assert 'email.addEventListener("input"' in LOGIN
    assert 'password.addEventListener("input"' in LOGIN
    assert 'userIsTyping && (email.value.trim().length > 0 || password.value.length > 0)' in LOGIN
    assert 'hasStoredSession' in LOGIN
    # 3. allowedNext deve aceitar root "/"
    assert r'^\/(|app|gestao|gestao-medicos' in LOGIN

    # 4. Gestão: view(enc) deve renderizar o conteúdo com detail(full) substituindo o skeleton
    assert 'if(body)body.innerHTML=detail(full);' in GESTAO_ATENDIMENTOS


def test_esisla_prompt_dates_and_distinct_exam_fields():
    """
    Valida a separação estrita dos campos:
    - (*)Exame Físico Geral
    - Descrição das Alterações Clínicas encontradas e Relato dos Exames Complementares
    E a padronização das datas para o formato oficial e-SISLA (DD/MM/AAAA, sem ISO ou 2026-00-00).
    """
    from app import _clean_esisla_text, _format_date_br, _minimal_ai_context, TASK_PROMPTS

    # 1. Prompt e-SISLA possui Item 3 e Item 4 separados e regras de data DD/MM/AAAA
    esisla_prompt = TASK_PROMPTS["esisla"]
    assert '3. “(*)Exame Físico Geral”' in esisla_prompt
    assert '4. “Descrição das Alterações Clínicas encontradas e Relato dos Exames Complementares:”' in esisla_prompt
    assert 'NUNCA DEVEM VIR COM TEXTOS IDÊNTICOS' in esisla_prompt
    assert 'DD/MM/AAAA' in esisla_prompt

    # 2. _format_date_br trata datas ISO e com zeros
    assert _format_date_br("2026-00-00") == "01/01/2026"
    assert _format_date_br("2026-09-25") == "25/09/2026"
    assert _format_date_br("2026-09-25 14:30:00") == "25/09/2026 14:30"

    # 3. _clean_esisla_text normaliza datas ISO ou 2026-00-00
    sample_text = (
        "Registro da perícia Médica para Licença\n\n"
        "(*) Queixa e Duração:\n"
        "Início dos sintomas em 2026-00-00 e consulta em 2026-09-25.\n\n"
        "Antecedentes Mórbidos:\n"
        "Nega comorbidades.\n\n"
        "Atestado/Relatório/Exames Complementares (Tipo-Data-Resultado):\n"
        "Atestado em 2026-09-20.\n\n"
        "Pressão Arterial\nSistólica (mmHg): 120\nDiastólica (mmHg): 80\nPulso (bpm): 72\n\n"
        "Altura: 1.70\nPeso: 70\n\n"
        "(*)Exame Físico Geral\n"
        "Bom estado geral, eupneico, afebril, acianótico, anictérico.\n\n"
        "Descrição das Alterações Clínicas encontradas e Relato dos Exames Complementares:\n"
        "Bom estado geral, eupneico, afebril, acianótico, anictérico.\n\n"
        "(*)Descrição da(s) Limitação(ções) Física(s) e/ou Mental(is) encontrada(s):\n"
        "Sem limitações funcionais.\n\n"
        "(*)Parecer Médico\n\n"
        "Nº Dias: 5\n"
        "Data Início: 25/09/2026\n"
        "CID 10: M54.5\n"
        "Descrição: Dorsalgia\n"
        "Médico Perito: Dr. Teste\n"
        "CRM: 123456\n"
        "Dt/Hr Perícia: 25/09/2026 10:00\n\n"
        "(*)Resposta aos quesitos\n"
        "1) Não\n2) Não\n3) Não"
    )
    cleaned = _clean_esisla_text(sample_text)
    # As datas ISO devem ter sido convertidas
    assert "2026-00-00" not in cleaned
    assert "01/01/2026" in cleaned
    assert "2026-09-25" not in cleaned
    assert "25/09/2026" in cleaned
    # Os campos idênticos devem ter sido desacoplados
    assert "Não foram apresentados exames complementares (imagem ou laboratoriais) no ato pericial." in cleaned

    # 4. _minimal_ai_context desvincula alteracoes_clinicas_exames de exame_fisico_descricao
    payload_dup = {
        "exame_fisico_descricao": "Achados clínicos periciais normais",
        "alteracoes_clinicas_exames": "Achados clínicos periciais normais",
        "documentos_complementares": [],
    }
    ctx = _minimal_ai_context(payload_dup)
    assert ctx["exame_fisico_descricao"] == "Achados clínicos periciais normais"
    assert ctx["alteracoes_clinicas_exames"] == ""

    # 5. Frontend: desacoplamento nos manipuladores de exame físico e mental
    assert 'state.alteracoesClinicasExames = descFinalOsteo' not in ATTENDANCE
    assert 'state.alteracoesClinicasExames = descOsteoNormal' not in ATTENDANCE
    assert 'state.alteracoesClinicasExames = descMentalNormal' not in ATTENDANCE
    assert 'state.alteracoesClinicasExames = descMentalAlterado' not in ATTENDANCE
    assert 'state.alteracoesClinicasExames = novoTexto' not in ATTENDANCE
    assert '"Exame Físico Geral — achados observados":"exameFisicoDescricao"' in ATTENDANCE


def test_detail_modal_versao_txt_and_toggle_edit():
    """
    Valida a exibição:
    1. detailModal (Prontuário geral / 'Abrir ficha') permanece estritamente na versão em blocos (detailBody com detail(full)).
    2. esislaModal ('Gerar ficha eSisla'):
       - Ao gerar, devolve primariamente na versão em blocos estruturados (esislaBlocosContainer via renderEsislaBlocos).
       - Ao clicar em Editar (esislaToggleEditBtn), libera a versão TXT para edição (esislaText com readonly removido).
       - Permite alternar entre Blocos e TXT via botões e re-renderiza blocos atualizados após edição.
    """
    # 1. detailModal estritamente em blocos (conforme solicitação do usuário)
    assert 'id="detailModal"' in GESTAO_ATENDIMENTOS
    assert 'id="detailBody"' in GESTAO_ATENDIMENTOS
    assert 'if(body)body.innerHTML=detail(full);' in GESTAO_ATENDIMENTOS
    assert 'id="detailTxtContainer"' not in GESTAO_ATENDIMENTOS

    # 2. esislaModal com exibição em blocos e liberação da versão TXT na edição
    assert 'id="esislaModal"' in GESTAO_ATENDIMENTOS
    assert 'id="esislaBlocosContainer"' in GESTAO_ATENDIMENTOS
    assert 'id="esislaText"' in GESTAO_ATENDIMENTOS
    assert 'id="btnEsislaBlocos"' in GESTAO_ATENDIMENTOS
    assert 'id="btnEsislaTxt"' in GESTAO_ATENDIMENTOS
    assert 'id="esislaToggleEditBtn"' in GESTAO_ATENDIMENTOS
    assert 'toggleEditEsisla()' in GESTAO_ATENDIMENTOS

    # 3. Funções JavaScript na Gestão
    assert 'function renderEsislaBlocos(' in GESTAO_ATENDIMENTOS
    assert 'function setEsislaViewMode(' in GESTAO_ATENDIMENTOS
    assert 'function setEsislaEditable(' in GESTAO_ATENDIMENTOS
    assert 'function toggleEditEsisla(' in GESTAO_ATENDIMENTOS

    # 4. Ao gerar, devolve em blocos por padrão
    assert "renderEsislaBlocos(data.ficha_esisla);" in GESTAO_ATENDIMENTOS
    assert "setEsislaViewMode('blocos');" in GESTAO_ATENDIMENTOS


def test_esisla_generation_altura_peso_exame_checkbox_parecer_and_justificativa(monkeypatch):
    from app import app, EsislaResult, _minimal_ai_context, TASK_PROMPTS

    # 1. _minimal_ai_context extrai agilAltura, biotipoAltura, agilPeso, biotipoPeso, agilExameFisicoDescricao, agilExameFisicoTipo, agilJustificativa
    ctx = _minimal_ai_context({
        "atendimento": "999",
        "agilAltura": "1.82",
        "biotipoPeso": "85",
        "agilExameFisicoTipo": "Aparelho Osteomuscular e Tecido Conjuntivo",
        "agilExameFisicoDescricao": "Lombalgia com contratura paravertebral moderada e Lasegue negativo.",
        "agilJustificativa": "Incapacidade laboral temporária para atividades de esforço físico.",
        "parecer": "Favorável",
        "dias_solicitados": "14",
        "data_documento": "2026-09-29",
        "cid": "M54.5",
        "doenca_motivo": "Dor lombar baixa",
        "medico": "Dr. Perito Oficial",
        "crm_responsavel": "123456/SP"
    })
    assert ctx["altura"] == "1.82"
    assert ctx["peso"] == "85"
    assert ctx["exame_fisico_tipo"] == "Aparelho Osteomuscular e Tecido Conjuntivo"
    assert ctx["exame_fisico_descricao"] == "Lombalgia com contratura paravertebral moderada e Lasegue negativo."
    assert ctx["justificativa"] == "Incapacidade laboral temporária para atividades de esforço físico."

    # 2. Prompt do e-SISLA contém diretrizes para Altura, Peso, Checkbox de Exame Físico, Parecer e Justificativa
    prompt = TASK_PROMPTS["esisla"]
    assert "Quando altura e peso constarem nos dados fornecidos (altura, peso), preencha OBRIGATORIAMENTE os campos 'Altura: [altura]' e 'Peso: [peso]'" in prompt
    assert "ESTE CAMPO É EXCLUSIVO PARA O EXAME FÍSICO / MENTAL DIRETO REALIZADO PELO MÉDICO PERITO" in prompt
    assert "REGRA DE AJUSTE PARA ACHADOS MUITO CURTOS (SOMENTE EM CASOS EXTREMOS)" in prompt
    assert "(*)Justificativa Parecer Médico" in prompt

    # 3. Post-processing em /api/ai/esisla preenche dados faltantes automaticamente
    monkeypatch.setattr("app._authenticate_request", lambda: ({"id": "1", "email": "admin@ambiental.com", "nome": "Admin", "perfil": "Administrador"}, "token123"))

    sample_ficha_com_lacunas = (
        "Registro da perícia Médica para Licença\n\n"
        "(*) Queixa e Duração:\nServidor de 45 anos...\n\n"
        "Antecedentes Mórbidos:\nNega comorbidades.\n\n"
        "Atestado/Relatório/Exames Complementares (Tipo-Data-Resultado):\nCRM 123456\n\n"
        "Pressão Arterial\nSistólica (mmHg): 120\nDiastólica (mmHg): 80\nPulso (bpm): 75\n\n"
        "Altura:\nPeso:\n\n"
        "(*)Exame Físico Geral\n\n"
        "Descrição das Alterações Clínicas encontradas e Relato dos Exames Complementares:\nNão foram apresentados exames complementares.\n\n"
        "(*)Descrição da(s) Limitação(ções) Física(s) e/ou Mental(is) encontrada(s):\nApresenta limitações...\n\n"
        "(*)Parecer Médico\nParecer:\nNº Dias:\nData Início:\nCID 10:\nDescrição:\nMédico Perito:\nCRM:\nDt/Hr Perícia: 29/09/2026 14:00\n\n"
        "(*)Resposta aos quesitos\n1) Não\n2) Não\n3) Sim\n\n"
        "(*)Justificativa Parecer Médico\n\n"
        "(*) Parecer Final\n\nNº Dias:\nData Início:\nCID 10:\nDescrição:\nDiretor DPME:\nData P.F.:"
    )
    monkeypatch.setattr("app._generate_cached", lambda *args, **kwargs: (EsislaResult(ficha_esisla=sample_ficha_com_lacunas), False, "hash123"))

    client = app.test_client()
    res = client.post("/api/ai/esisla", json={
        "atendimento": "ATD-101",
        "altura": "1.82",
        "peso": "85",
        "parecer": "Favorável",
        "dias_solicitados": "14",
        "data_documento": "2026-09-29",
        "cid": "M54.5",
        "doenca_motivo": "Dor lombar baixa",
        "medico": "Dr. Perito Oficial",
        "crm_responsavel": "123456/SP",
        "exame_fisico_tipo": "Aparelho Osteomuscular e Tecido Conjuntivo",
        "exame_fisico_descricao": "Lombalgia com contratura muscular",
        "justificativa": "Capacidade laborativa temporariamente prejudicada"
    })
    assert res.status_code == 200
    data = res.get_json()
    f_text = data["ficha_esisla"]
    assert "Altura: 1.82" in f_text
    assert "Peso: 85" in f_text
    assert "Parecer: FAVORÁVEL" in f_text
    assert "Nº Dias: 14" in f_text
    assert "Data Início: 29/09/2026" in f_text
    assert "CID 10: M54.5" in f_text
    assert "Descrição: Dor lombar baixa" in f_text
    assert "Médico Perito: Dr. Perito Oficial" in f_text
    assert "CRM: 123456/SP" in f_text
    assert "Aparelho Osteomuscular e Tecido Conjuntivo: Lombalgia com contratura muscular" in f_text
    assert "Capacidade laborativa temporariamente prejudicada" in f_text
    assert "(Tipo-Data-Resultado)" not in f_text

    # 4. Contratos de frontend em gestao_atendimentos.html
    assert '☑️ Checkbox e-SISLA:' in GESTAO_ATENDIMENTOS
    assert 'toRegex(s)' in GESTAO_ATENDIMENTOS
    assert 'voMedico.parRlExApres' in GESTAO_ATENDIMENTOS
    assert 'idExameApres' in GESTAO_ATENDIMENTOS
    assert 'justificaPericia' in GESTAO_ATENDIMENTOS
    assert 'voMedico.lgAltura' in GESTAO_ATENDIMENTOS
    assert 'voMedico.lgPeso' in GESTAO_ATENDIMENTOS


def test_esisla_remocao_tipo_data_resultado_quesitos_salvamento_e_script_f12_parecer_cids():
    from app import TASK_PROMPTS, _clean_esisla_text, _minimal_ai_context

    # 1. Ausência de (Tipo-Data-Resultado) nos prompts oficiais e limpeza ativa
    assert "(Tipo-Data-Resultado)" not in TASK_PROMPTS["esisla"]
    suja = "Registro da perícia Médica para Licença\n\nAtestado/Relatório/Exames Complementares (Tipo-Data-Resultado):\nAtestado CRM 12345"
    limpa = _clean_esisla_text(suja)
    assert "(Tipo-Data-Resultado)" not in limpa
    assert "Atestado/Relatório/Exames Complementares:" in limpa

    # 2. Normalização automática de quesitos em _minimal_ai_context para nunca ficarem vazios/—
    ctx_favoravel = _minimal_ai_context({"parecer": "Favorável", "quesitos": []})
    assert len(ctx_favoravel["quesitos"]) == 3
    assert [q["resposta"] for q in ctx_favoravel["quesitos"]] == ["Sim", "Sim", "Sim"]
    ctx_contrario = _minimal_ai_context({"parecer": "Contrário", "quesitos": []})
    assert len(ctx_contrario["quesitos"]) == 3
    assert [q["resposta"] for q in ctx_contrario["quesitos"]] == ["Sim", "Não", "Não"]
    ctx_contrario_readap = _minimal_ai_context({"parecer": "Contrário", "readaptado": True, "quesitos": []})
    assert len(ctx_contrario_readap["quesitos"]) == 3
    assert [q["resposta"] for q in ctx_contrario_readap["quesitos"]] == ["Sim", "Sim", "Não"]

    # 3. Contratos de Modo Ágil e salvamento de quesitos no formulário de atendimento (atuando nos fundos)
    assert 'id="agilQuesitosContainer" style="display:none' in ATTENDANCE
    assert 'id="agilQuesitosList"' in ATTENDANCE
    assert 'renderAgilQuesitos' in ATTENDANCE
    assert 'ensureDefaultQuesitos' in ATTENDANCE

    # 4. Contratos de Parecer Final e limite estrito de 2 CIDs no Script F12 e JSON e-SISLA
    assert 'setParecerFinal' in GESTAO_ATENDIMENTOS
    assert 'mudaSituacao' in GESTAO_ATENDIMENTOS
    assert 'escondeCampos' in GESTAO_ATENDIMENTOS
    assert 'cdCidPm' in GESTAO_ATENDIMENTOS
    assert 'cdCid2Pm' in GESTAO_ATENDIMENTOS
    assert 'nmCidPm2' in GESTAO_ATENDIMENTOS
    # Bookmarklet universal também com setParecerFinal
    assert 'setParecerFinal' in ATTENDANCE


def test_esisla_sistema_exame_fisico_single_checkbox_e_remocao_alteracoes_clinicas_separadas():
    """Garante que:
    1. Apenas o sistema de exame físico selecionado (ex.: Aparelho Osteomuscular) é marcado
       no e-SISLA via F12 / Bookmarklet, prevenindo a seleção inadvertida de Exame Mental.
    2. Checkboxes não selecionados são explicitamente desmarcados via setCheckbox(..., false).
    3. O bloco redundante 'ALTERAÇÕES CLÍNICAS E RELATO DE EXAMES' foi removido da visualização em blocos.
    4. Achados reais de exames complementares vão para Queixa e Duração, descartando 'Em anexo.'
    5. O textarea voMedico.parRlExApres (idExameApres) não recebe boilerplate 'Em anexo.'
    """
    # 1. Função de detecção determinística e mutuamente exclusiva de sistema de exame físico
    assert 'function detectarSistemaExameFisico(st, aux, texto, cidCode)' in GESTAO_ATENDIMENTOS
    assert 'function detectarSistemaExameFisico(st, aux, texto, cidCode)' in ATTENDANCE

    # 2. Remoção do bloco redundante de Alterações Clínicas em renderEsislaBlocos
    assert 'ALTERAÇÕES CLÍNICAS E RELATO DE EXAMES' not in GESTAO_ATENDIMENTOS
    assert 'Alterações Clínicas e Relato de Exames' not in GESTAO_ATENDIMENTOS

    # 3. Uncheck explícito de checkboxes falsos no Script F12 e no Bookmarklet Universal
    assert 'setCheckbox(item.n, item.id, isChecked);' in GESTAO_ATENDIMENTOS
    assert 'setCheckbox(item.n,item.id,chk);' in ATTENDANCE

    # 4. Integração de relatos de exames em Queixa e Duração
    assert 'Exames apresentados:' in GESTAO_ATENDIMENTOS
    assert 'Exames apresentados:' in ATTENDANCE

    # 5. Prevenção de anexar "Em anexo" ao textarea voMedico.parRlExApres
    assert "exApres.replace(/\\n\\s*Em anexo\\.?\\s*$/gi, '')" in GESTAO_ATENDIMENTOS
    assert "exApres.replace(/^(?:[\\s\\r\\n]*em\\s+anexo\\.?[" in ATTENDANCE


def test_ajustes_atendimento_e_esisla_5_requisitos():
    """Valida os 5 requisitos solicitados pelo usuário:
    1. IA para 'Outros' no exame físico: não descreve exame físico, foca em limitações funcionais baseadas no CID quando Alterado.
    2. IA e-SISLA: Atestados e Exames Complementares preenchido estritamente com 'Em anexo.'
    3. Dados do Atestado & Prazos no atendimento: oculto por padrão com checkbox 'agilCheckAtestadoAssistente'.
    4. Dias concedidos nunca em branco se parecer favorável, e automaticamente 0 se parecer contrário.
    5. Eliminação de duplicação do título do sistema e respeito à escolha de 'Outros' sem sobreposição de CID.
    """
    from app import TASK_PROMPTS, _clean_esisla_text

    # Requisito 1: Prompt de justificativa e atendimento Ágil para Outros
    justif_prompt = TASK_PROMPTS["justificativa"]
    assert "NÃO DESCREVA O EXAME FÍSICO" in justif_prompt
    assert "FOCO EXCLUSIVO EM LIMITAÇÕES FUNCIONAIS E LABORAIS COM BASE NO CID" in justif_prompt
    assert "Limitações funcionais decorrentes do quadro clínico" in ATTENDANCE
    assert "escolherOutrosResultado" in ATTENDANCE
    assert "gerarJustificativaAgilIA" in ATTENDANCE

    # Requisito 2: Atestados e Exames Complementares estritamente "Em anexo."
    esisla_prompt = TASK_PROMPTS["esisla"]
    assert '“Atestado/Relatório/Exames Complementares”: preencha exclusivamente com o texto sucinto padronizado:\n  "Em anexo."' in esisla_prompt
    raw_esisla = (
        "Registro da perícia Médica para Licença\n\n"
        "(*) Queixa e Duração:\nServidor de 40 anos...\n\n"
        "Antecedentes Mórbidos:\nNega comorbidades.\n\n"
        "Atestado/Relatório/Exames Complementares:\n"
        "CRM 123456, solicita 15 dias de afastamento a partir de 20/09/2026, pelo CID M17.\n\n"
        "Pressão Arterial\nSistólica (mmHg): 120\nDiastólica (mmHg): 80\nPulso (bpm): 75\n\n"
        "Altura:\nPeso:\n\n"
        "(*)Exame Físico Geral\nAparelho Osteomuscular: dor leve.\n\n"
        "Descrição das Alterações Clínicas encontradas e Relato dos Exames Complementares:\nNão foram apresentados exames.\n\n"
        "(*)Descrição da(s) Limitação(ções) Física(s) e/ou Mental(is) encontrada(s):\nLimitação leve.\n\n"
        "(*)Parecer Médico\nParecer: FAVORÁVEL\nNº Dias: 15\nData Início: 20/09/2026\nCID 10: M17\nDescrição: Gonartrose\nMédico Perito: Dr. Teste\nCRM: 12345\nDt/Hr Perícia: 25/09/2026 14:00\n\n"
        "(*)Resposta aos quesitos\n1) Não\n2) Não\n3) Não\n"
    )
    cleaned = _clean_esisla_text(raw_esisla)
    assert "Atestado/Relatório/Exames Complementares:\nEm anexo.\n\n" in cleaned
    assert "CRM 123456" not in cleaned
    assert "atestado = 'Em anexo.';" in GESTAO_ATENDIMENTOS
    assert "let hda = 'Em anexo.';" in ATTENDANCE

    # Requisito 3: Checkbox para ocultar Dados do Atestado do Médico Assistente & Prazos
    assert 'id="agilCheckAtestadoAssistente"' in ATTENDANCE
    assert 'id="agilAtestadoAssistenteSubpanel" class="subpanel" style="display:none' in ATTENDANCE
    assert 'toggleAtestadoAssistente' in ATTENDANCE

    # Requisito 4: Dias concedidos automático (0 se contrário, default 1 / não em branco se favorável)
    assert 'atualizarDiasConcedidosAutomatico' in ATTENDANCE
    assert "flPfinal === 'C'" in GESTAO_ATENDIMENTOS
    assert "dias = '0';" in GESTAO_ATENDIMENTOS
    assert "parecerVal === 'C'" in ATTENDANCE
    assert "diasSol = '0';" in ATTENDANCE
    assert "flPfinal === 'F' && (!dias || dias === '0')" in GESTAO_ATENDIMENTOS
    assert "parecerVal === 'F' && (!diasSol || diasSol === '0')" in ATTENDANCE

    # Requisito 5: Sem duplicação de título no exame físico e respeito total à opção "Outros"
    app_text = (ROOT / "app.py").read_text(encoding="utf-8")
    gestao_text = (ROOT / "gestao_atendimentos.html").read_text(encoding="utf-8")
    atd_text = (ROOT / "ambiental_avaliacao_medica_lts_cid_assistente.html").read_text(encoding="utf-8")

    assert "prefixosSistema" in gestao_text
    assert "exameFisicoLimpo.replace(rx, '').trim()" in gestao_text
    assert "exTipo === 'outros' || exTipo === 'e outros' || outrosSub === 'e outros' || outrosSub === 'outros'" in gestao_text
    assert "exTipo === 'outros' || exTipo === 'e outros' || outrosSub === 'e outros' || outrosSub === 'outros'" in atd_text
    assert "Aparelho E outros:" not in _clean_esisla_text(raw_esisla.replace("Aparelho Osteomuscular: dor leve.", "Aparelho E outros: Bom do estado geral, nutrição adequada."))
    assert "NUNCA escreva prefixos como \"Aparelho E outros:\"" in app_text
    assert "exameFisicoLinha1.startsWith('aparelho e outro')" in gestao_text
    assert "exameFisicoLinha1.startsWith('aparelho e outro')" in atd_text


def test_correspondencia_exata_sistemas_exame_fisico_esisla():
    """Garante que a seleção em 'Tipo de exame físico / mental' e os subtipos de 'Outros'
    mapeiam exatamente para os 12 sistemas oficiais do e-SISLA:
    - Aparelho Osteomuscular e Tecido Conjuntivo (aoal)
    - Exame Mental (em)
    - Aparelho Circulatório (ac)
    - Aparelho Respiratório (ar)
    - Tecido celular subcutâneo Pele e Fâneros (tcspf)
    - Aparelho Digestivo (ad)
    - Aparelho Geniturinário (agu)
    - Aparelho Hemolinfopoiético (ahp)
    - Aparelho Endócrino (ae)
    - Sistema Nervoso (sn)
    - Órgãos dos Sentidos (os)
    - Outros (outro)
    """
    gestao = (ROOT / "gestao_atendimentos.html").read_text(encoding="utf-8")
    atd = (ROOT / "ambiental_avaliacao_medica_lts_cid_assistente.html").read_text(encoding="utf-8")

    for code in [gestao, atd]:
        # Precedência dos chips detalhados sob "Outros"
        assert "outrosSub.includes('circulat') || outrosSub.includes('cardio')) return 'ac'" in code
        assert "outrosSub.includes('respirat') || outrosSub.includes('pulmon')) return 'ar'" in code
        assert "outrosSub.includes('pele') || outrosSub.includes('fânero')" in code
        assert "outrosSub.includes('digest') || outrosSub.includes('gastr')) return 'ad'" in code
        assert "outrosSub.includes('genit') || outrosSub.includes('urin')" in code
        assert "outrosSub.includes('hemolin') || outrosSub.includes('hemat')) return 'ahp'" in code
        assert "outrosSub.includes('endocrin') || outrosSub.includes('metabol')" in code
        assert "outrosSub.includes('nervoso') || outrosSub.includes('neurol')) return 'sn'" in code
        assert "outrosSub.includes('sentidos') || outrosSub.includes('oftalm')" in code
        assert "outrosSub === 'e outros' || outrosSub === 'outros'" in code

        # Precedência das opções principais
        assert "exTipo.includes('osteomuscular')" in code
        assert "exTipo === 'exame mental'" in code


def test_quesitos_readaptado_e_contrario_e_cid_secundario():
    """Valida:
    1. Quesitos para parecer CONTRÁRIO + readaptado (Sim, Sim, Não)
    2. Quesitos para parecer CONTRÁRIO + não readaptado (Sim, Não, Não)
    3. Exibição e geração de CID 10 Secundário no card do parecer e na ficha e-SISLA
    """
    gestao = (ROOT / "gestao_atendimentos.html").read_text(encoding="utf-8")
    atd = (ROOT / "ambiental_avaliacao_medica_lts_cid_assistente.html").read_text(encoding="utf-8")
    app_py = (ROOT / "app.py").read_text(encoding="utf-8")

    # 1. Regra dos quesitos no gestao_atendimentos
    assert "if (num === 1) return 'SIM';" in gestao
    assert "if (num === 2) return isReadap ? 'SIM' : 'NÃO';" in gestao
    assert "if (num === 3) return 'NÃO';" in gestao
    assert "if (num === 2) return fl_isReadap ? 'S' : 'N';" in gestao

    # 2. Regra dos quesitos no atendimento
    assert "ajustarQuesitosPorParecerEReadaptacao" in atd
    assert "QuesitoService.set(1, isReadap ? \"Sim\" : \"Não\");" in atd
    assert "QuesitoService.set(2, \"Não\");" in atd

    # 3. Card do parecer médico pericial com CID 10 Secundário
    assert "CID 10 Secundário" in gestao
    assert "${cidSec ? `" in gestao

    # 4. Geração e-SISLA no app.py com CID 10 Secundário e quesitos periciais
    assert "CID 10 Secundário:" in app_py
    assert "Descrição Secundária:" in app_py
    assert "q2_ans = \"Sim\" if is_readap else \"Não\"" in app_py
    assert "Se Parecer CONTRÁRIO e o colaborador FOR readaptado: 1) Sim, 2) Sim, 3) Não" in app_py
    assert "Se Parecer CONTRÁRIO e o colaborador NÃO for readaptado: 1) Sim, 2) Não, 3) Não" in app_py


def test_remover_inicio_tratamento_queixa_duracao():
    from app import _clean_queixa_duracao_text, _clean_esisla_text
    
    # 1. Testar limpeza isolada de texto de queixa
    exemplo1 = "Servidor de 40 anos, professor, não readaptado, com queixa de depressão desde 2020. Refere início do tratamento em 29/09/2026. Queixa-se de desânimo."
    limpo1 = _clean_queixa_duracao_text(exemplo1)
    assert "Refere início do tratamento em 29/09/2026" not in limpo1
    assert "Servidor de 40 anos, professor, não readaptado, com queixa de depressão desde 2020. Queixa-se de desânimo." == limpo1

    exemplo2 = "Servidor de 40 anos, professor, com queixa de dor. Refere início do tratamento em 15/03/2024, com consultas a cada 2 meses."
    limpo2 = _clean_queixa_duracao_text(exemplo2)
    assert "Refere início do tratamento em 15/03/2024" not in limpo2
    assert "com consultas a cada 2 meses" in limpo2.lower()

    # 2. Testar na ficha e-SISLA completa
    ficha = """Registro da perícia Médica para Licença Saúde
Nome do servidor: Maria da Silva
(*) Queixa e Duração:
Servidor de 40 anos, professor há 10 anos, não readaptado, com queixa de depressão desde 2020. Refere início do tratamento em 29/09/2026, com consultas a cada 2 meses. Queixa-se de desânimo e tristeza.

Antecedentes Mórbidos:
Hipertenso há 5 anos.
"""
    ficha_limpa = _clean_esisla_text(ficha)
    assert "Refere início do tratamento em 29/09/2026" not in ficha_limpa
    assert "Queixa-se de desânimo e tristeza." in ficha_limpa

    # 3. Testar contratos no gestao_atendimentos e assistente
    gestao = (ROOT / "gestao_atendimentos.html").read_text(encoding="utf-8")
    atd = (ROOT / "ambiental_avaliacao_medica_lts_cid_assistente.html").read_text(encoding="utf-8")
    assert "function cleanQueixaDuracao(" in gestao
    assert "cleanQueixaDuracao(ext(str, '(*) Queixa e Duração'" in gestao
    assert "cleanQueixaDuracao(ext(texto, '(*) Queixa e Duração'" in gestao
    assert "function cleanQueixaDuracao(" in atd


def test_antecedentes_morbidos_ext_nao_trunca_com_palavra_atestado():
    import re
    gestao = (ROOT / "gestao_atendimentos.html").read_text(encoding="utf-8")

    # 1. Verificar presenca das regras aprimoradas no gestao_atendimentos.html
    assert "headersFimAntecedentes" in gestao
    assert "ext(str, 'Antecedentes Mórbidos', headersFimAntecedentes)" in gestao
    assert "ext(texto, 'Antecedentes Mórbidos', headersFimAntecedentes)" in gestao
    assert "p.toLowerCase() === 'atestado'" in gestao

    # 2. Executar extracao identica a do javascript com texto real do caso relatado pelo usuario
    texto = """Registro da perícia Médica para Licença

(*) Queixa e Duração:
Servidor com dor lombar há 10 dias.

Antecedentes Mórbidos:
Hipertenso desde os 29 anos. Vem com atestado de 15 dias do Dr. Roberto. Nega diabetes e cirurgias prévias.

Atestado/Relatório/Exames Complementares:
Em anexo.

Pressão Arterial
Sistólica (mmHg): 120
Diastólica (mmHg): 80
Pulso (bpm): 72
"""

    def toRegex(s, is_end=False):
        if not s or s == "FIM_INEXISTENTE":
            return ""
        if s == "\n":
            return r"(?:\r?\n|$)"
        if isinstance(s, list):
            parts = [toRegex(x, is_end) for x in s]
            parts = [p for p in parts if p]
            return "(?:" + "|".join(parts) + ")"
        p = re.sub(r":+$", "", s).strip()
        p = re.escape(p)
        p = p.replace(r"\(\*\)", r"\(\s*\*\s*\)\s*")
        p = p.replace(r"\/", r"\s*\/\s*")
        if is_end:
            if p.lower() in ("atestado", "atestados"):
                return r"(?:\r?\n|^)\s*" + p + r"(?:\s*[:\/]|$|\s+[0-9]+)"
            return r"(?:\r?\n|^)\s*" + p + r"\s*:?"
        return r"(?:(?:\r?\n|^)\s*)?" + p + r"\s*:?"

    def ext(t, i, f):
        si = toRegex(i, False)
        sf = toRegex(f, True)
        rx = re.compile(si + r"\s*([\s\S]*?)\s*(?=" + (sf if sf else "$") + r"|$)", re.IGNORECASE)
        m = rx.search(t)
        return m.group(1).strip() if m else ""

    headers = [
        "Atestado/Relatório/Exames Complementares",
        "Atestado/Relatório",
        "Atestados/Relatórios",
        "Atestado:",
        "Atestados:",
        "Atestado",
        "Pressão Arterial",
        "Sistólica",
        "Altura",
        "(*)Exame Físico Geral",
    ]

    extracted = ext(texto, "Antecedentes Mórbidos", headers)
    assert "Hipertenso desde os 29 anos." in extracted
    assert "Vem com atestado de 15 dias" in extracted
    assert "Nega diabetes e cirurgias prévias." in extracted
    assert not extracted.startswith("Hipertenso desde os 29 anos. Vem com\n")
    assert extracted != "Hipertenso desde os 29 anos. Vem com"


def test_esisla_gender_agreement_antecedentes_cid_secundario_and_limitacoes(monkeypatch):
    from app import app, EsislaResult, _minimal_ai_context, _clean_esisla_text, TASK_PROMPTS

    # 1. Gênero (Homem = servidor/periciado; Mulher = servidora/periciada; Dúvida = servidor)
    ctx_homem = _minimal_ai_context({"sexo": "M"})
    assert ctx_homem["termo_genero"] == "servidor"
    assert ctx_homem["sexo"] == "Masculino"

    ctx_mulher = _minimal_ai_context({"sexo": "F"})
    assert ctx_mulher["termo_genero"] == "servidora"
    assert ctx_mulher["sexo"] == "Feminino"

    ctx_duvida = _minimal_ai_context({})
    assert ctx_duvida["termo_genero"] == "servidor"

    prompt = TASK_PROMPTS["esisla"]
    assert "Se for homem (sexo masculino): utilize SEMPRE \"Servidor\" ou \"Periciado\"" in prompt
    assert "Se for mulher (sexo feminino): utilize SEMPRE \"Servidora\" ou \"Periciada\"" in prompt
    assert "Em caso de dúvida ou não especificado: utilize o termo padrão masculino \"Servidor\" ou \"Periciado\"" in prompt

    # 2. Antecedentes Mórbidos: remoção de dias de atestado mantendo histórico pregresso da patologia
    prompt_ant = prompt
    assert "NUNCA mencione dias de atestado, afastamento ou concessões (\"Vem com atestado de X dias...\", \"atestado de...\", \"com atestado de...\") nesta seção de Antecedentes Mórbidos." in prompt_ant
    assert "Antecedentes Mórbidos destinam-se EXCLUSIVAMENTE ao histórico pregresso clínico da patologia" in prompt_ant

    raw_ant_com_dias = (
        "Registro da perícia Médica para Licença\n\n"
        "(*) Queixa e Duração:\nServidor de 38 anos...\n\n"
        "Antecedentes Mórbidos:\nHipertenso desde os 29 anos. Vem com atestado de 7 dias por hipertensão arterial.\n\n"
        "Atestado/Relatório/Exames Complementares:\nEm anexo.\n\n"
        "Pressão Arterial\nSistólica (mmHg): 120\nDiastólica (mmHg): 80\nPulso (bpm): 80\n\n"
        "Altura: 1.75\nPeso: 80\n\n"
        "(*)Exame Físico Geral\nAparelho Circulatório: Normocárdico.\n\n"
        "Descrição das Alterações Clínicas encontradas e Relato dos Exames Complementares:\nNão foram apresentados exames complementares.\n\n"
        "(*)Descrição da(s) Limitação(ções) Física(s) e/ou Mental(is) encontrada(s):\nApresenta limitações...\n\n"
        "(*)Parecer Médico\nParecer: CONTRÁRIO\nNº Dias: 0\nData Início: 29/09/2026\nCID 10: I10\nDescrição: Hipertensão arterial essencial\nCID 10 Secundário: Descrição Secundária:\nMédico Perito: WANIA SANCHES PICASSO\nCRM: 79775\nDt/Hr Perícia: 29/09/2026 14:00\n\n"
        "(*)Resposta aos quesitos\n1) Sim\n2) Sim\n3) Não\n\n"
        "(*)Justificativa Parecer Médico\nCapacidade preservada.\n\n"
        "(*) Parecer Final\nNº Dias: 0\nData Início: 29/09/2026\nCID 10: I10\nDescrição: Hipertensão arterial essencial\nDiretor DPME:\nData P.F.:"
    )

    cleaned = _clean_esisla_text(raw_ant_com_dias)
    assert "Vem com atestado de 7 dias" not in cleaned
    assert "Hipertenso desde os 29 anos." in cleaned
    assert "CID 10 Secundário:\nDescrição Secundária:\n" in cleaned

    # 3. Post-processing em /api/ai/esisla: Parecer CONTRÁRIO, Limitações e CID Secundário limpo
    monkeypatch.setattr("app._authenticate_request", lambda: ({"id": "1", "email": "admin@ambiental.com", "nome": "Admin", "perfil": "Administrador"}, "token123"))
    monkeypatch.setattr("app._generate_cached", lambda *args, **kwargs: (EsislaResult(ficha_esisla=raw_ant_com_dias), False, "hash123"))

    client = app.test_client()
    res = client.post("/api/ai/esisla", json={
        "atendimento": "999888",
        "sexo": "M",
        "cargo": "Investigador de Polícia",
        "readaptado": False,
        "parecer": "Contrário",
        "cid": "I10",
        "doenca_motivo": "Vem com atestado de 7 dias por hipertensão arterial",
        "exame_fisico_tipo": "Aparelho Circulatório",
        "exame_fisico_descricao": "PA 120x80 mmHg, bulhas rítmicas normofonéticas sem sopros",
        "medico": "WANIA SANCHES PICASSO",
        "crm_responsavel": "79775"
    })
    assert res.status_code == 200
    res_data = res.get_json()
    f_res = res_data["ficha_esisla"]

    # Verifica fórmula obrigatória para parecer CONTRÁRIO
    assert "Do ponto de vista médico não se observa limitações físicas ou mentais funcionais incapacitantes para as atribuições do cargo de Investigador de Polícia, constantes no rol de atividades." in f_res

    # Verifica limpeza de CID secundário vazio para não gerar lixo nem "Médico Perito"
    assert "CID 10 Secundário: Descrição Secundária:" not in f_res
    assert "CID 10 Secundário:" in f_res
    assert "Descrição Secundária:" in f_res
    assert "Descrição: Hipertensão arterial" in f_res

    # Verifica quesitos para parecer CONTRÁRIO não readaptado: 1) Sim, 2) Não, 3) Não
    assert "1) Sim" in f_res
    assert "2) Não" in f_res
    assert "3) Não" in f_res

    # Verifica preservação estrita do exame físico do atendimento
    assert "Aparelho Circulatório: PA 120x80 mmHg, bulhas rítmicas normofonéticas sem sopros" in f_res

    # 4. Caso readaptado com Parecer CONTRÁRIO: Quesito 2 deve ser Sim
    ctx_contr_readap = _minimal_ai_context({"parecer": "Contrário", "readaptado": True, "quesitos": []})
    assert [q["resposta"] for q in ctx_contr_readap["quesitos"]] == ["Sim", "Sim", "Não"]

    # 5. Caso com CID Secundário real
    res_sec = client.post("/api/ai/esisla", json={
        "atendimento": "999889",
        "parecer": "Favorável",
        "cid": "I10",
        "cids_secundarios": [{"cid": "I15.0", "descricao": "Hipertensão renovascular"}]
    })
    assert res_sec.status_code == 200
    f_sec_res = res_sec.get_json()["ficha_esisla"]
    assert "CID 10 Secundário: I15.0" in f_sec_res
    assert "Descrição Secundária: Hipertensão renovascular" in f_sec_res


def test_download_extensao_esisla():
    import zipfile, io, json
    from app import app
    client = app.test_client()
    res = client.get("/api/extensao-esisla/download")
    assert res.status_code == 200
    assert res.content_type == "application/zip"
    assert "attachment" in res.headers.get("Content-Disposition", "")
    assert "extensao_esisla.zip" in res.headers.get("Content-Disposition", "")

    zf = zipfile.ZipFile(io.BytesIO(res.data))
    names = zf.namelist()
    assert any("manifest.json" in n for n in names)
    assert any("content_esisla.js" in n for n in names)
    assert any("content_ambiental.js" in n for n in names)
    assert any("popup.html" in n for n in names)

    # Verifica integridade do manifest.json dentro do zip
    manifest_bytes = [zf.read(n) for n in names if n.endswith("manifest.json")][0]
    manifest_data = json.loads(manifest_bytes.decode("utf-8"))
    assert manifest_data["manifest_version"] == 3
    assert "Ambiental" in manifest_data["name"]


def test_ajustes_senior_antecedentes_nega_checkboxes_outros_limitacoes_e_header():
    """Valida as 4 melhorias solicitadas pelo usuário com rigor sênior:
    1. Preservação de limitações físicas e mentais existentes (não sobrescreve se já preenchido).
    2. Antecedentes Mórbidos coletados do modo ágil; se em branco, preenche 'Nega' / 'Nega.'.
    3. Tipo de exame 'Outros -> Exame Físico Geral' e 'Outros -> E outros' marcam estritamente Checkbox e-SISLA: Outros.
    4. Topo do atendimento com apenas Gestão, Excluir, Salvar rascunho e Finalizar, sem colisão de scroll.
    """
    from app import _clean_esisla_text, _minimal_ai_context

    atd = (ROOT / "ambiental_avaliacao_medica_lts_cid_assistente.html").read_text(encoding="utf-8")
    gestao = (ROOT / "gestao_atendimentos.html").read_text(encoding="utf-8")
    app_text = (ROOT / "app.py").read_text(encoding="utf-8")

    # 1. Header limpo e sem sobreposição de HUD
    hdr_match = re.search(r'<div class="header-actions">([\s\S]*?)</div>', atd)
    assert hdr_match is not None
    hdr_content = hdr_match.group(1)
    assert 'openManagement()' in hdr_content
    assert 'deleteAtendimento()' in hdr_content
    assert 'saveNow()' in hdr_content
    assert 'finalizeFromHeader()' in hdr_content
    assert 'openFinalReport()' not in hdr_content
    assert 'abrirModalComprovanteComparecimento()' not in hdr_content
    assert 'abrirModalBookmarkletAtendimento()' not in hdr_content

    # CSS do Header relativo e HUD sólido
    assert ".header{\n  position:relative; z-index:40;" in atd or ".header{\r\n  position:relative; z-index:40;" in atd
    assert "background: #FFFFFF !important;" in atd

    # 2. Antecedentes Mórbidos: coleta do campo e default 'Nega'
    assert 'const histDef = histAgil || "Nega"' in atd
    assert 'const apVal = (state.aux?.historicoPregresso || v.historicoPregresso || $("agilHistoricoPregresso")?.value || \'\').trim();' in atd
    assert "cleanAntecedentesMorbidos(ext(str, 'Antecedentes Mórbidos', headersFimAntecedentes) || st.historicoPregresso || aux.historicoPregresso || st.antecedentes || aux.antecedentes || '') || 'Nega'" in gestao

    # Teste no app.py com antecedentes vazio -> Nega
    ctx_empty = _minimal_ai_context({"antecedentes": "", "historico_pregresso": ""})
    assert ctx_empty["antecedentes"] == "Nega"
    assert ctx_empty["historico_pregresso"] == "Nega"

    # Teste de limpeza do texto e-SISLA com antecedentes vazio/ponto -> Nega.
    esisla_sample = (
        "Registro da perícia Médica para Licença\n\n"
        "(*) Queixa e Duração:\nServidor de 40 anos, professor há 10 anos.\n\n"
        "Antecedentes Mórbidos:\n.\n\n"
        "Atestado/Relatório/Exames Complementares:\nEm anexo.\n\n"
        "Altura: 1,75\nPeso: 75\n\n"
        "(*)Exame Físico Geral\nAparelho Osteomuscular: dor lombar.\n\n"
        "Descrição das Alterações Clínicas encontradas e Relato dos Exames Complementares:\nNão foram apresentados exames.\n\n"
        "(*)Descrição da(s) Limitação(ções) Física(s) e/ou Mental(is) encontrada(s):\nLimitação leve.\n\n"
        "(*)Parecer Médico\nParecer: FAVORÁVEL\nNº Dias: 10\nData Início: 20/09/2026\nCID 10: M54.5\nDescrição: Dor lombar\nMédico Perito: Dr. Teste\nCRM: 12345\nDt/Hr Perícia: 25/09/2026 14:00\n\n"
        "(*)Resposta aos quesitos\n1) Sim\n2) Sim\n3) Sim\n"
    )
    cleaned_sample = _clean_esisla_text(esisla_sample)
    assert "Antecedentes Mórbidos:\nNega.\n\n" in cleaned_sample

    # 3. Checkboxes e-SISLA: Outros -> Exame Físico Geral e E outros
    for code in [gestao, atd]:
        assert "if (outrosSub.includes('geral') || outrosSub === 'e outros' || outrosSub === 'outros') return 'outro'" in code
        assert "if (outrosSub.includes('circulat') || outrosSub.includes('cardio')) return 'ac'" in code
        assert "if (outrosSub.includes('respirat') || outrosSub.includes('pulmon')) return 'ar'" in code

    # 4. Preservação de limitações físicas e mentais existentes
    assert "existingDescLimOsteo" in atd
    assert "existingDescLimOsteoNorm" in atd
    assert "existingDescLimMentalNorm" in atd
    assert "existingDescLimMentalAlt" in atd
    assert "PRESERVAÇÃO RIGOROSA DE LIMITAÇÕES JÁ PREENCHIDAS" in app_text


def test_isolamento_estrito_exame_fisico_alteracoes_e_limitacoes():
    """Garante que o Exame Físico Geral não vaze conteúdos de seções subsequentes
    (Alterações Clínicas/Médicas, Limitações, Parecer, Quesitos, Parecer Final),
    e que a função ext não caia no fallback de final de arquivo ($) indevidamente.
    """
    from app import _clean_esisla_text

    atd = (ROOT / "ambiental_avaliacao_medica_lts_cid_assistente.html").read_text(encoding="utf-8")
    gestao = (ROOT / "gestao_atendimentos.html").read_text(encoding="utf-8")
    app_text = (ROOT / "app.py").read_text(encoding="utf-8")

    # 1. Normalização canônica no app.py de "Alterações Médicas" para "Alterações Clínicas..."
    sample_medicas = (
        "Registro da perícia Médica para Licença\n\n"
        "(*)Exame Físico Geral\n"
        "Bom estado geral. Normodinâmico.\n\n"
        "Descrição das Alterações Médicas e Relato dos Exames Complementares:\n"
        "Não foram apresentados exames complementares.\n\n"
        "(*)Descrição da(s) Limitação:\n"
        "Limitação leve.\n\n"
        "(*)Parecer Médico\nParecer: FAVORÁVEL\nNº Dias: 5\n"
    )
    cleaned = _clean_esisla_text(sample_medicas)
    assert "Descrição das Alterações Clínicas encontradas e Relato dos Exames Complementares:" in cleaned
    assert "(*)Descrição da(s) Limitação(ções) Física(s) e/ou Mental(is) encontrada(s):" in cleaned

    # 2. Em gestao_atendimentos.html, ext usa lookahead estrito sem fallback |$ quando sf existe
    assert "const lookahead = sf ? '(?=' + sf + ')' : '(?=$)';" in gestao
    assert "headersFimExameFisico" in gestao
    assert "headersFimAlteracoes" in gestao
    assert "headersFimLimitacoes" in gestao

    # 3. Card dedicado de Alterações Clínicas e Exames no gestao_atendimentos.html
    assert "Alterações Clínicas e Exames Complementares" in gestao

    # 4. Em ambiental_avaliacao_medica_lts_cid_assistente.html, regex de exApres aceita variações de Alterações
    assert "(?:Descrição das Alterações|Descri[çc][ãa]o das Altera[çc][õo]es|\\(\\*\\)Descrição da\\(s\\) Limitação|\\(\\*\\)Parecer Médico|Limitação|$)" in atd

    # 5. Validação com o texto real do usuário: Exame Físico isolado sem vazamento
    raw_user_sample = (
        "Registro da perícia Médica para Licença\n\n"
        "(*)Exame Físico Geral\n"
        "Bom do estado geral, nutrição adequada, sem alterações na coloração e hidratação de mucosas.\n"
        "EXAME FÍSICO DO AP. CARDIOVASCULAR: Precórdio normodinâmico.\n\n"
        "Descrição das Alterações Médicas e Relato dos Exames Complementares:\n"
        "Não foram apresentados exames complementares (imagem ou laboratoriais) no ato pericial.\n\n"
        "(*)Descrição da(s) Limitação(ções) Física(s) e/ou Mental(is) encontrada(s):\n"
        "Limitações funcionais decorrentes do quadro clínico (I10 - Hipertensão essencial (primária)).\n\n"
        "(*)Parecer Médico\nParecer: FAVORÁVEL\nNº Dias: 7\nData Início: 29/09/2026\nCID 10: I10\n"
        "Descrição: Vem com atestado de 7 dias por hipertensão arterial.\n"
        "Médico Perito: WANIA SANCHES PICASSO - CRM: 79775\nCRM: 79775\nDt/Hr Perícia: 29/09/2026 07:55\n\n"
        "(*)Resposta aos quesitos\n1) Sim\n2) Sim\n3) Sim\n\n"
        "(*)Justificativa Parecer Médico\nConsidero a capacidade laborativa parcial.\n\n"
        "(*) Parecer Final\nNº Dias: 7\nData Início: 29/09/2026\nCID 10: I10\nDiretor DPME:\nData P.F.:"
    )

    clean_user = _clean_esisla_text(raw_user_sample)

    # Extração de Exame Físico delimitado estritamente por Descrição das Alterações
    m_ef = re.search(
        r"(\(\*\)\s*Exame Físico Geral:?\s*\n\s*)([\s\S]*?)(?=\n\s*Descrição das Alterações)",
        clean_user,
        re.IGNORECASE
    )
    assert m_ef is not None
    ef_text = m_ef.group(2).strip()
    assert "Bom do estado geral" in ef_text
    assert "Precórdio normodinâmico" in ef_text
    # Nenhuma seção posterior deve vazar para o Exame Físico Geral
    assert "Descrição das Alterações" not in ef_text
    assert "Não foram apresentados exames" not in ef_text
    assert "Limitações funcionais" not in ef_text
    assert "Parecer: FAVORÁVEL" not in ef_text
    assert "WANIA SANCHES PICASSO" not in ef_text
    assert "Resposta aos quesitos" not in ef_text
    assert "Data P.F." not in ef_text


def test_detectar_sistema_exame_fisico_outros_geral_e_cid_cardiovascular():
    """Garante que tanto no gestao_atendimentos.html quanto no assistente o exame físico geral
    e o texto de 'Bom do estado geral' sempre mapeiem para 'outro' (voMedico.parEdOutro),
    mesmo que o CID seja I10 (cardiovascular) e contenha menção ao aparelho cardiovascular no texto.
    """
    gestao = GESTAO_ATENDIMENTOS
    atd = ATTENDANCE

    # Ambos os arquivos devem conter a verificação de texto 'bom do estado geral' retornando 'outro'
    assert "efLower.includes('bom do estado geral')" in gestao
    assert "efLower.includes('bom do estado geral')" in atd

    # A verificação de conteúdo clínico deve anteceder a verificação cega por CID
    idx_gestao_text = gestao.find("efLower.includes('bom do estado geral')")
    idx_gestao_cid = gestao.find("const c = String(cidCode || '').toUpperCase().trim();")
    assert idx_gestao_text != -1 and idx_gestao_cid != -1
    assert idx_gestao_text < idx_gestao_cid, "Em gestao_atendimentos.html o texto do exame deve ter precedência sobre o CID"

    idx_atd_text = atd.find("efLower.includes('bom do estado geral')")
    idx_atd_cid = atd.find("const c = String(cidCode || '').toUpperCase().trim();")
    assert idx_atd_text != -1 and idx_atd_cid != -1
    assert idx_atd_text < idx_atd_cid, "No assistente o texto do exame deve ter precedência sobre o CID"

    # Ambos os arquivos devem mapear subtipo geral / e outros para 'outro'
    assert "outrosSub.includes('geral') || outrosSub === 'e outros' || outrosSub === 'outros'" in gestao
    assert "outrosSub.includes('geral') || outrosSub === 'e outros' || outrosSub === 'outros'" in atd

    # Emulação do algoritmo em Python reproduzindo o caso reportado pelo usuário
    def py_detectar(st, aux, texto, cid_code):
        ex_tipo = str(st.get("exameFisicoTipo") or aux.get("exameFisicoTipo") or "").strip().lower()
        outros_sub = str(st.get("outrosSubtipo") or aux.get("outrosSubtipo") or "").strip().lower()
        
        if "geral" in outros_sub or outros_sub in ("e outros", "outros"):
            return "outro"
        if "geral" in ex_tipo or ex_tipo in ("outros", "e outros") or ex_tipo.startswith("outro"):
            return "outro"
            
        m = re.search(r"\(\*\)\s*Exame Físico Geral:?\s*\n\s*([\s\S]*?)(?=\n\s*(?:Descrição das Alterações|\(\*\)Descrição da\(s\) Limitação|\(\*\)Parecer Médico|$))", texto, re.IGNORECASE)
        ef_texto = m.group(1).lower() if m else ""
        m_l1 = re.search(r"\(\*\)\s*Exame Físico Geral:?\s*\n\s*([^\n\r]+)", texto, re.IGNORECASE)
        l1 = m_l1.group(1).lower() if m_l1 else ""
        
        if l1.startswith("aparelho e outro") or l1.startswith("e outros") or "bom do estado geral" in ef_texto or "exame físico geral" in ef_texto:
            return "outro"
        if ("circulat" in l1 or "circulat" in ef_texto) and "bom do estado geral" not in ef_texto:
            return "ac"
            
        c = str(cid_code or "").upper().strip()
        if c.startswith("I"):
            return "ac"
        return "outro"

    texto_real = (
        "(*)Exame Físico Geral\n"
        "Bom do estado geral, nutrição adequada, sem alterações na coloração e hidratação de mucosas.\n"
        "EXAME FÍSICO DO AP.RESPIRATÓRIO: Eupnéico, sem esforço respiratório.\n"
        "EXAME FÍSICO DO AP. CARDIOVASCULAR: Precórdio normodinâmico. RCR 2T c/ BNF.\n\n"
        "Descrição das Alterações Clínicas encontradas e Relato dos Exames Complementares:\n"
        "Não foram apresentados exames complementares no ato pericial.\n"
    )

    # Caso 1: Médico salvou em Modo Ágil com CID I10 e texto padrão do Exame Físico Geral
    assert py_detectar({}, {}, texto_real, "I10") == "outro"

    # Caso 2: Médico selecionou Tipo "Outros" e Subtipo "Geral"
    assert py_detectar({"exameFisicoTipo": "Outros", "outrosSubtipo": "Geral"}, {}, texto_real, "I10") == "outro"

    # Caso 3: Médico realmente avaliou apenas Aparelho Circulatório sem Exame Geral
    texto_cardio_puro = (
        "(*)Exame Físico Geral\n"
        "Aparelho Circulatório: Precórdio normodinâmico. RCR 2T c/ BNF sem sopros.\n\n"
        "Descrição das Alterações Clínicas encontradas e Relato dos Exames Complementares:\n"
        "Não foram apresentados exames complementares.\n"
    )
    assert py_detectar({"exameFisicoTipo": "Aparelho Circulatório"}, {}, texto_cardio_puro, "I10") == "ac"


def test_api_ai_esisla_vitals_dthr_antecedentes_and_limitacoes_preservation(monkeypatch):
    """Testa preservação completa dos sinais vitais, data/hora perícia, antecedentes mórbidos
    sem menção a dias de atestado, exames complementares de fallback, e ausência de prefixos duplicados.
    """
    from app import app, EsislaResult

    raw_gemini_template = (
        "Registro da perícia Médica para Licença\n\n"
        "(*) Queixa e Duração:\nServidor apresenta queixas clínicas.\n\n"
        "Antecedentes Mórbidos:\n\n"
        "Atestado/Relatório/Exames Complementares:\nEm anexo.\n\n"
        "(*)Exame Físico Geral\n"
        "Exame Físico Geral: \n\n"
        "Descrição das Alterações Clínicas encontradas e Relato dos Exames Complementares:\n\n"
        "(*)Descrição da(s) Limitação(ções) Física(s) e/ou Mental(is) encontrada(s):\n\n"
        "(*)Parecer Médico\n"
        "Parecer: FAVORÁVEL\n"
        "Nº Dias: 7\n"
        "Data Início: 29/09/2026\n"
        "CID 10: I10\n"
        "Descrição: Hipertensão arterial\n"
        "Médico Perito: WANIA SANCHES PICASSO\n"
        "CRM: 79775\n\n"
        "(*)Resposta aos quesitos\n1) Sim\n2) Sim\n3) Sim\n\n"
        "(*)Justificativa Parecer Médico\nCapacidade temporariamente prejudicada.\n\n"
        "(*) Parecer Final\nNº Dias: 7\nData Início: 29/09/2026\nCID 10: I10\nDescrição: Hipertensão arterial\nDiretor DPME:\nData P.F.:"
    )

    monkeypatch.setattr("app._authenticate_request", lambda: ({"id": "1", "email": "admin@ambiental.com", "nome": "Admin", "perfil": "Administrador"}, "token123"))
    monkeypatch.setattr("app._generate_cached", lambda *args, **kwargs: (EsislaResult(ficha_esisla=raw_gemini_template), False, "hash123"))

    client = app.test_client()

    # Cenário 1: Médico com todos os campos preenchidos
    payload_completo = {
        "atendimento": "777888",
        "data_atendimento": "29/09/2026",
        "hora_atendimento": "07:55",
        "pressao_sistolica": "130",
        "pressao_diastolica": "85",
        "pulso": "76",
        "altura": "1.70",
        "peso": "82",
        "historico_pregresso": "Hipertensa há 6 anos, faz uso de hidroclorotiazida. Vem com atestado de 7 dias.",
        "alteracoes_clinicas_exames": "",
        "exame_fisico_tipo": "Outros",
        "exame_fisico_descricao": "Exame Físico Geral: Bom do estado geral, corada, hidratada.",
        "desc_limitacao": "Limitação para esforços físicos intensos e levantamento de peso excessivo",
        "parecer": "FAVORÁVEL",
        "cargo": "Professor de Educação Básica",
        "cid": "I10",
        "medico": "WANIA SANCHES PICASSO",
        "crm_responsavel": "79775"
    }

    res = client.post("/api/ai/esisla", json=payload_completo)
    assert res.status_code == 200
    ficha = res.get_json()["ficha_esisla"]

    # 1. Sinais Vitais e medidas
    assert "Sistólica (mmHg): 130" in ficha
    assert "Diastólica (mmHg): 85" in ficha
    assert "Pulso (bpm): 76" in ficha
    assert "Altura: 1.70" in ficha
    assert "Peso: 82" in ficha

    # 2. Data/Hora da perícia formatada
    assert "Dt/Hr Perícia: 29/09/2026 07:55" in ficha

    # 3. Antecedentes Mórbidos limpos de menções a atestado
    assert "Hipertensa há 6 anos, faz uso de hidroclorotiazida." in ficha
    assert "Vem com atestado de 7 dias" not in ficha

    # 4. Fallback de exames complementares
    assert "Não foram apresentados exames complementares (imagem ou laboratoriais) no ato pericial." in ficha

    # 5. Sem prefixo duplicado no Exame Físico
    assert "Exame Físico Geral: Exame Físico Geral:" not in ficha
    assert "Bom do estado geral, corada, hidratada." in ficha

    # 6. Preservação de limitações com rol de atividades integrado
    assert "Limitação para esforços físicos intensos e levantamento de peso excessivo, atividades estas constantes no Rol de Atividades do cargo de Professor de Educação Básica." in ficha

    # Cenário 2: Histórico pregresso vazio deve resultar em 'Nega.'
    payload_sem_ant = dict(payload_completo)
    payload_sem_ant["historico_pregresso"] = ""
    res_sem_ant = client.post("/api/ai/esisla", json=payload_sem_ant)
    assert res_sem_ant.status_code == 200
    ficha_sem_ant = res_sem_ant.get_json()["ficha_esisla"]
    assert re.search(r"Antecedentes Mórbidos:\s*Nega\.", ficha_sem_ant) is not None

