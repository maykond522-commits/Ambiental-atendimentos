from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.py").read_text(encoding="utf-8")
ENV = (ROOT / ".env.example").read_text(encoding="utf-8")
E2E = (ROOT / "scripts" / "e2e_staging.py").read_text(encoding="utf-8")
RLS_FILE = ROOT / "RLS_PRODUCAO.sql"
if not RLS_FILE.exists():
    RLS_FILE = ROOT / "tests" / "sql" / "RLS_PRODUCAO.sql"
RLS = RLS_FILE.read_text(encoding="utf-8")


def test_example_env_contains_no_real_secrets():
    assert "GEMINI_API_KEY=AQ." not in ENV
    assert "postgresql://postgres." not in ENV
    assert "ADMIN_EMAILS=" not in ENV
    assert "SUPABASE_URL=https://SEU-PROJETO.supabase.co" in ENV


def test_server_authorization_has_single_source_of_truth():
    block = APP[APP.index("def _role_from_profile"):APP.index("def _authenticate_request")]
    assert 'SELECT id, nome, perfil, ativo, crm FROM usuarios WHERE id=%s' in block
    assert "app_metadata.get(\"role\")" not in APP
    assert "ADMIN_EMAILS" not in APP
    assert "X-User-Role" not in APP


def test_doctor_ownership_is_server_side():
    assert 'if role == "Médico":' in APP
    assert 'clauses.append("usuario_id = %s")' in APP or 'usuario_id=%s' in APP
    assert 'payload.get("usuario_id")' not in APP


def test_workflow_and_save_have_row_lock_and_version_guard():
    assert APP.count("FOR UPDATE") >= 3
    assert APP.count("VERSION_CONFLICT") >= 3
    assert "WHERE id=%s AND versao=%s" in APP


def test_auth_session_cookie_is_httponly_and_lax():
    assert "httponly=True" in APP
    assert 'samesite="Lax"' in APP


def test_security_headers_and_origin_guard_exist():
    assert 'X-Content-Type-Options' in APP
    assert 'Content-Security-Policy' in APP
    assert 'request_origin_guard' in APP
    assert 'CSRF_ORIGIN_DENIED' in APP


def test_e2e_script_checks_cross_doctor_isolation():
    assert "E2E_MEDICO_A_TOKEN" in E2E
    assert "E2E_MEDICO_B_TOKEN" in E2E
    assert "E2E_ATENDIMENTO_A_ID" in E2E
    assert "403, 404" in E2E


def test_rls_defense_in_depth_covers_sensitive_tables():
    for table in [
        "usuarios", "atendimentos", "historico_atendimento", "logs_ia",
        "relatorios", "configuracoes", "cache_ia", "documentos", "quesitos", "ia_rate_limits",
    ]:
        assert f"alter table if exists public.{table} enable row level security;" in RLS
