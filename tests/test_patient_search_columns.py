from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.py").read_text(encoding="utf-8")
SERVICE = (ROOT / "services" / "atendimento_service.py").read_text(encoding="utf-8")
SQL_FILE = ROOT / "migrations_paciente_busca.sql"
if not SQL_FILE.exists():
    SQL_FILE = ROOT / "tests" / "sql" / "migrations_paciente_busca.sql"
SQL = SQL_FILE.read_text(encoding="utf-8")
HTML = (ROOT / "gestao_atendimentos.html").read_text(encoding="utf-8")

def test_patient_columns_and_indexes_present():
    assert "ADD COLUMN IF NOT EXISTS paciente_nome TEXT" in APP
    assert "ADD COLUMN IF NOT EXISTS paciente_cpf TEXT" in APP
    assert "idx_atd_paciente_nome_lower" in APP
    assert "idx_atd_paciente_cpf" in APP

def test_save_materializes_patient_fields():
    assert "paciente_nome_db, paciente_cpf_db = _patient_fields(payload)" in APP
    assert "paciente_nome=%s, paciente_cpf=%s" in APP
    assert "paciente_nome, paciente_cpf" in APP

def test_search_uses_materialized_patient_columns():
    assert "lower(paciente_nome) LIKE %s" in SERVICE
    assert "paciente_cpf LIKE %s" in SERVICE

def test_migration_is_idempotent_and_backfills_payload():
    assert "ADD COLUMN IF NOT EXISTS paciente_nome" in SQL
    assert "ADD COLUMN IF NOT EXISTS paciente_cpf" in SQL
    assert "payload_json->'aux'->>'nomePaciente'" in SQL
    assert "payload_json->'aux'->>'cpfPaciente'" in SQL

def test_management_fallback_accepts_materialized_fields():
    assert "r.paciente_nome" in HTML
    assert "r.paciente_cpf" in HTML
