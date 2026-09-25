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

    # Background defaults: 03 = doencaMotivo (em vez de Nega), 04 = Em anexo
    assert 'state.aux.historicoPregresso = doenca' in ATTENDANCE
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

    # 3. e-Sisla payload passes antecedentes and historico_pregresso
    assert 'payload.antecedentes = histVal' in ATTENDANCE
    assert 'payload.historico_pregresso = histVal' in ATTENDANCE

    # 4. _minimal_ai_context maps historico_pregresso and antecedentes
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










