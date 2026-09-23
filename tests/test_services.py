from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from services.atendimento_service import build_where, list_filters, pagination


def test_doctor_filter_is_always_server_scoped():
    clauses, params = list_filters({}, role="Médico", user_id="doctor-123")
    assert "usuario_id = %s" in clauses
    assert "doctor-123" in params


def test_admin_filter_can_be_broad_without_owner_scope():
    clauses, params = list_filters({"status": "RASCUNHO"}, role="Administrador", user_id="doctor-123")
    assert "usuario_id = %s" not in clauses
    assert "status = %s" in clauses
    assert "RASCUNHO" in params


def test_pagination_is_bounded():
    page, size, offset = pagination({"page": "0", "page_size": "9999"})
    assert page == 1
    assert size == 100
    assert offset == 0


def test_where_builder_is_parameterized():
    where = build_where(["usuario_id = %s", "status = %s"])
    assert where == " WHERE usuario_id = %s AND status = %s"


def test_backend_has_no_legacy_role_emergency_fallback():
    source = (ROOT / "app.py").read_text(encoding="utf-8")
    assert 'role = "Administrador"\n        else:\n            role = "Médico"' not in source
    assert 'Liberando acesso via perfil provisório' not in source
    assert 'email.lower() == "maykon.moraes@ambientalqvt.com.br"' not in source


def test_backend_has_operational_observability():
    source = (ROOT / "app.py").read_text(encoding="utf-8")
    assert 'X-Request-ID' in source
    assert '@app.get("/ready")' in source
    assert '@app.get("/metrics")' in source


def test_backend_uses_global_ai_rate_limit_table():
    source = (ROOT / "app.py").read_text(encoding="utf-8")
    assert 'FROM ia_rate_limits' in source or 'INSERT INTO ia_rate_limits' in source
    assert '_rate_bucket' not in source


def test_doctor_scope_cannot_be_disabled_by_browser_filters():
    clauses, params = list_filters({"medico": "Outro Médico", "q": "ATD-999"}, role="Médico", user_id="doctor-123")
    assert clauses[0] == "usuario_id = %s"
    assert params[0] == "doctor-123"
    assert "medico" in " ".join(clauses)


def test_access_guard_requires_owner_for_doctors():
    source = (ROOT / "app.py").read_text(encoding="utf-8")
    block = source[source.index('def _require_record_access'):source.index('def _error', source.index('def _require_record_access'))]
    assert 'if owner and str(owner) == str(current_user):' in block
    assert 'Acesso restrito aos seus próprios atendimentos.' in block
