"""
Script de Otimização e Limpeza da Tabela historico_atendimento
Remove dados inflados (aux e validation gerados por auto-save),
cria índices de alta performance e executa VACUUM ANALYZE.
"""
import os
import sys

# Garantir import do app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import app, get_db

def optimize_historico():
    with app.app_context():
        db = get_db()
        cur = db.cursor()

        print("=== DIAGNÓSTICO PRÉ-LIMPEZA ===")
        cur.execute("SELECT count(*) as total, pg_size_pretty(pg_total_relation_size('historico_atendimento')) as tam FROM historico_atendimento")
        before = cur.fetchone()
        print(f"Total de registros: {before['total']}")
        print(f"Tamanho total em disco: {before['tam']}")

        cur.execute("SELECT count(*) as junk FROM historico_atendimento WHERE campo IN ('aux', 'validation')")
        junk_count = cur.fetchone()['junk']
        print(f"Registros de lixo temporário (aux/validation): {junk_count}")

        if junk_count > 0:
            print("\nExecutando limpeza de registros inchados...")
            cur.execute("DELETE FROM historico_atendimento WHERE campo IN ('aux', 'validation')")
            deleted = cur.rowcount
            db.commit()
            print(f"[OK] {deleted} registros removidos com sucesso!")
        else:
            print("Nenhum registro de aux/validation encontrado.")

        print("\nCriando índices de alta performance...")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_historico_atd_id ON historico_atendimento(atendimento_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_historico_criado ON historico_atendimento(criado_em DESC)")
        db.commit()
        print("[OK] Índices idx_historico_atd_id e idx_historico_criado garantidos!")

        cur.close()

        # VACUUM ANALYZE necessita de autocommit fora de bloco de transação
        print("\nExecutando VACUUM ANALYZE para recuperar espaço em disco e atualizar estatísticas do planejador...")
        old_autocommit = db.autocommit
        db.autocommit = True
        try:
            raw_cur = db.cursor()
            raw_cur.execute("VACUUM ANALYZE historico_atendimento")
            raw_cur.close()
            print("[OK] VACUUM ANALYZE concluído com sucesso!")
        finally:
            db.autocommit = old_autocommit

        # Diagnóstico Pós-limpeza
        cur = db.cursor()
        print("\n=== DIAGNÓSTICO PÓS-LIMPEZA ===")
        cur.execute("SELECT count(*) as total, pg_size_pretty(pg_total_relation_size('historico_atendimento')) as tam FROM historico_atendimento")
        after = cur.fetchone()
        print(f"Total de registros final: {after['total']}")
        print(f"Novo tamanho total em disco: {after['tam']}")
        cur.close()

if __name__ == "__main__":
    optimize_historico()
