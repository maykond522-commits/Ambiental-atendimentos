from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.py").read_text(encoding="utf-8")


def test_stats_query_uses_sql_filter_aggregation():
    assert "COUNT(*) FILTER (WHERE status = 'RASCUNHO')" in APP
    assert "COUNT(*) FILTER (WHERE status = 'FINALIZADO')" in APP
    assert "SELECT status, medico, completude, alertas, inconsistencias, atualizado_em, payload_json FROM atendimentos" not in APP


def test_doctor_authorship_protected_for_admins():
    assert 'if request.user_role == "Médico":' in APP
    assert 'elif oldrow:' in APP
    assert 'preservado_medico' in APP
    assert 'preservado_crm' in APP


def test_init_db_decoupled_from_unconditional_import():
    assert 'RUN_DB_MIGRATIONS' in APP
    assert '\n_init_db()\n' not in APP
    assert '--init-db' in APP


def test_audit_records_include_user_id():
    assert 'INSERT INTO historico_atendimento(atendimento_id, usuario_id, usuario_nome' in APP
    assert 'INSERT INTO historico_atendimento(atendimento_id, usuario_nome' not in APP


def test_role_profile_uses_single_crm_query():
    assert 'SELECT id, nome, perfil, ativo, crm FROM usuarios WHERE id=%s' in APP
    assert 'SELECT crm FROM usuarios WHERE id=%s' not in APP
