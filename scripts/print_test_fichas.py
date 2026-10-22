import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import app, get_db
import json

with app.app_context():
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT numero, paciente_nome, cid, payload_json FROM atendimentos WHERE numero LIKE 'TESTE-GLOSA%' ORDER BY numero")
    rows = cur.fetchall()
    for r in rows:
        pj = r['payload_json'] if isinstance(r['payload_json'], dict) else json.loads(r['payload_json'])
        print(f"=== CASO: {r['numero']} | {r['paciente_nome']} | {r['cid']} ===")
        print(pj.get('ficha_esisla', 'SEM FICHA'))
        print("\n" + "="*70 + "\n")
    cur.close()
