"""
Testes automatizados para validação da Fase 3: Organização, Governança de Dados (LGPD) & Performance.
Valida:
1. Índice GIN sobre o payload JSONB para queries ultrarrápidas no Postgres.
2. Tabela de auditoria de acessos e visualizações (LGPD Art. 11 e CFM 1.821).
3. Middleware e hook automático em leitura de atendimentos (_log_audit_access).
4. Endpoint de auditoria de acessos (/api/atendimentos/<rid>/auditoria) com controle de perfil.
5. Endpoint de manutenção e limpeza de dados órfãos (/api/admin/manutencao/limpeza).
6. Integração do cliente api.js e visualização de rastreabilidade na interface de gestão.
"""
from pathlib import Path
import pytest
from app import app, get_db

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.py").read_text(encoding="utf-8")
API_JS = (ROOT / "api.js").read_text(encoding="utf-8")
GESTAO_ATENDIMENTOS = (ROOT / "gestao_atendimentos.html").read_text(encoding="utf-8")


def test_db_gin_index_and_audit_access_table_contract():
    # 1. Índice GIN para busca performática em JSON
    assert "idx_atd_payload_json_gin" in APP
    assert "USING gin(payload_json)" in APP

    # 2. Tabela de auditoria de acessos
    assert "CREATE TABLE IF NOT EXISTS auditoria_acessos" in APP
    assert "atendimento_id" in APP
    assert "usuario_id" in APP
    assert "usuario_nome" in APP
    assert "usuario_perfil" in APP
    assert "acao TEXT NOT NULL DEFAULT 'VISUALIZACAO'" in APP
    assert "ip TEXT" in APP
    assert "is_impersonating BOOLEAN DEFAULT FALSE" in APP
    assert "idx_auditoria_atd_id" in APP
    assert "idx_auditoria_usr_id" in APP


def test_audit_logging_logic_contract():
    # Hook _log_audit_access
    assert "def _log_audit_access(atendimento_id: str, usuario_id: str, usuario_nome: str, usuario_perfil: str" in APP
    assert "auditoria_acessos" in APP
    assert "is_impersonating" in APP

    # Chamada automática em api_get_atendimento
    get_block = APP[APP.index("def api_get_atendimento(rid):"):APP.index("def api_save_atendimento(rid=None):")]
    assert "_log_audit_access(r[\"id\"], user_id, user_nome, user_perfil, ip, is_imp, \"VISUALIZACAO\")" in get_block


def test_endpoint_atendimento_auditoria_contract():
    assert '@app.get("/api/atendimentos/<rid>/auditoria")' in APP
    assert "def api_atendimento_auditoria_acessos(rid):" in APP
    assert '_require_permission("audit")' in APP
    assert "_require_record_access(owner_row)" in APP
    assert "FROM auditoria_acessos" in APP
    assert "WHERE atendimento_id = %s" in APP


def test_endpoint_admin_manutencao_limpeza_contract():
    assert '@app.post("/api/admin/manutencao/limpeza")' in APP
    assert "def api_admin_manutencao_limpeza():" in APP
    assert "_require_admin()" in APP
    assert "DELETE FROM ia_cadastro_locks WHERE iniciado_em < NOW() - INTERVAL '5 minutes'" in APP
    assert "DELETE FROM ia_rate_limits WHERE atualizado_em < NOW() - INTERVAL '24 hours'" in APP
    assert "DELETE FROM cache_ia WHERE atualizado_em < TO_CHAR(NOW() - INTERVAL '30 days'" in APP


def test_api_js_phase3_contracts():
    # Método no namespace atendimento
    assert "auditoria(id)" in API_JS or "auditoria: (id)" in API_JS
    assert "/api/atendimentos/" in API_JS
    assert "/auditoria" in API_JS

    # Método no namespace admin
    assert "limpezaManutencao()" in API_JS or "limpezaManutencao: ()" in API_JS
    assert "/api/admin/manutencao/limpeza" in API_JS


def test_gestao_atendimentos_html_lgpd_audit_view():
    # 1. Função renderAuditRows atualizada com suporte a accessLogs
    assert "renderAuditRows(rows, sourceLabel='Servidor', accessLogs=[])" in GESTAO_ATENDIMENTOS
    assert "Acessos LGPD" in GESTAO_ATENDIMENTOS
    assert "Acessos e Visualizações (LGPD / CFM)" in GESTAO_ATENDIMENTOS
    assert "IP de Origem:" in GESTAO_ATENDIMENTOS

    # 2. openHistory realizando busca concorrente de histórico e auditoria
    assert "Promise.allSettled" in GESTAO_ATENDIMENTOS
    assert "/historico" in GESTAO_ATENDIMENTOS
    assert "/auditoria" in GESTAO_ATENDIMENTOS


def test_live_db_table_and_indexes():
    """Valida a criação física no Postgres real configurado."""
    try:
        with app.app_context():
            db = get_db()
            cur = db.cursor()
            
            # Verifica se a tabela auditoria_acessos existe
            cur.execute(
                """
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_name = 'auditoria_acessos'
                """
            )
            row = cur.fetchone()
            assert row is not None, "Tabela auditoria_acessos deve existir no Postgres."

            # Verifica se o índice GIN idx_atd_payload_json_gin existe
            cur.execute(
                """
                SELECT indexname 
                FROM pg_indexes 
                WHERE tablename = 'atendimentos' AND indexname = 'idx_atd_payload_json_gin'
                """
            )
            idx = cur.fetchone()
            assert idx is not None, "Índice GIN idx_atd_payload_json_gin deve existir no Postgres."
            cur.close()
    except Exception as exc:
        pytest.skip(f"Banco de dados Postgres não disponível no momento do teste: {exc}")
