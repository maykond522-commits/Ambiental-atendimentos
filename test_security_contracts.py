from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def source():
    return (ROOT / "app.py").read_text(encoding="utf-8")


def test_authorization_requires_usuarios_row():
    text = source()
    assert 'if not row or not bool(row["ativo"]):' in text
    assert 'role = app_metadata.get("role")' not in text
    assert 'in ADMIN_EMAILS' not in text


def test_update_and_workflow_use_row_locking():
    text = source()
    assert text.count('SELECT * FROM atendimentos WHERE id=%s OR numero=%s FOR UPDATE') >= 2


def test_history_has_single_owner_lookup():
    text = source()
    block_start = text.index('def api_history')
    block_end = text.index('@app.get("/api/medico/atendimentos")')
    block = text[block_start:block_end]
    assert block.count('SELECT usuario_id FROM atendimentos WHERE id=%s') == 1


def test_security_headers_include_request_id():
    text = source()
    assert 'X-Request-ID' in text
    assert 'Content-Security-Policy' in text
    assert 'Strict-Transport-Security' in text
