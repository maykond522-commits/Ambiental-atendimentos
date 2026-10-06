import io
import json
import uuid
import hashlib
import time
import pytest
from app import app, get_db, _AUTH_CACHE, _AUTH_CACHE_LOCK

@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client

def test_vincular_agenda_batch_endpoint_matching(client):
    medico_id = f"test-med-{uuid.uuid4().hex[:8]}"
    admin_id = f"test-adm-{uuid.uuid4().hex[:8]}"
    test_date = "2026-10-15"
    now_iso = "2026-10-15T08:00:00Z"
    agenda_id = None

    with app.app_context():
        db = get_db()
        cur = db.cursor()
        cur.execute("INSERT INTO usuarios (id, nome, email, perfil, crm, criado_em) VALUES (%s, %s, %s, %s, %s, %s)",
                    (medico_id, "Dr. Teste Lote", "medico.lote@teste.com", "Médico", "CRM 99999/SP", now_iso))
        cur.execute("INSERT INTO usuarios (id, nome, email, perfil, criado_em) VALUES (%s, %s, %s, %s, %s)",
                    (admin_id, "Admin Teste", "admin.lote@teste.com", "Administrador", now_iso))

        cur.execute("""
            INSERT INTO agendas (medico_id, data, hora, status, tipo, protocolo, ni, nome_periciado, criado_em, atualizado_em)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (medico_id, test_date, "08:30", "Agendado", "LICENC", "", "112233", "MARIA APARECIDA DA SILVA", now_iso, now_iso))
        agenda_id = cur.fetchone()["id"]
        db.commit()

    # PDF binário válido com campos e-SISLA
    pdf_bytes = b"""%PDF-1.4
1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj
2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj
3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >> endobj
4 0 obj << /Length 320 >> stream
BT
/F1 12 Tf
72 700 Td
(Consulta Pericia Licenca) Tj
0 -20 Td
(Protocolo: 20260155667) Tj
0 -20 Td
(Nome Completo: MARIA APARECIDA DA SILVA) Tj
0 -20 Td
(CPF: 12345678900) Tj
0 -20 Td
(RG: 445556667) Tj
0 -20 Td
(Data de Nascimento: 12/05/1985) Tj
0 -20 Td
(Cargo: PROFESSOR EDUCACAO BASICA II) Tj
0 -20 Td
(Orgao: SECRETARIA DA EDUCACAO) Tj
0 -20 Td
(UA: EE PROFESSOR TESTE) Tj
0 -20 Td
(CID 10: M54.5) Tj
0 -20 Td
(N Dias: 10) Tj
0 -20 Td
(Data de emissao do atestado: 14/10/2026) Tj
ET
endstream
endobj
5 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj
xref
0 6
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000244 00000 n 
0000000615 00000 n 
trailer << /Size 6 /Root 1 0 R >>
startxref
700
%%EOF
"""

    test_token = f"admin-token-{uuid.uuid4().hex}"
    token_hash = hashlib.sha256(test_token.encode("utf-8")).hexdigest()
    with _AUTH_CACHE_LOCK:
        _AUTH_CACHE[token_hash] = {
            "profile": {"id": admin_id, "nome": "Admin Teste", "email": "admin.lote@teste.com", "perfil": "Administrador"},
            "expires": time.time() + 3600
        }

    data = {
        "data": test_date,
        "medico_id": medico_id,
        "files": (io.BytesIO(pdf_bytes), "esisla_maria_silva.pdf")
    }

    resp = client.post(
        "/api/esisla/vincular-agenda-batch",
        data=data,
        content_type="multipart/form-data",
        headers={
            "Authorization": f"Bearer {test_token}"
        }
    )

    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.data}"
    res_data = resp.get_json()["data"]
    assert res_data["total_arquivos"] == 1
    assert res_data["total_vinculados"] == 1
    assert res_data["total_nao_encontrados"] == 0
    item = res_data["itens"][0]
    assert item["status"] == "vinculado"
    assert item["agenda_id"] == agenda_id
    assert item["periciado"] == "MARIA APARECIDA DA SILVA"
    assert "CPF" in item["campos_adiantados"]
    assert "CID M54.5" in item["campos_adiantados"]

    with app.app_context():
        db = get_db()
        cur = db.cursor()
        # Verificar que o agendamento no banco agora tem o atendimento_id vinculado
        cur.execute("SELECT atendimento_id, protocolo FROM agendas WHERE id = %s", (agenda_id,))
        ag_updated = cur.fetchone()
        assert ag_updated["atendimento_id"] is not None

        # Verificar que o atendimento criado tem os dados pré-preenchidos da ficha e-SISLA
        cur.execute("SELECT payload_json, status, paciente_cpf FROM atendimentos WHERE id = %s", (ag_updated["atendimento_id"],))
        atd_row = cur.fetchone()
        assert atd_row is not None
        assert atd_row["status"] == "RASCUNHO"
        assert atd_row["paciente_cpf"] == "123.456.789-00"
        raw_p = atd_row["payload_json"]
        payload = raw_p if isinstance(raw_p, dict) else json.loads(raw_p)
        assert payload["cid"] == "M54.5"
        assert payload["cargo"] == "PROFESSOR EDUCACAO BASICA II"
        assert payload["diasSolicitados"] == "10"
        assert payload["aux"]["protocolo"] == "20260155667"

        # Cleanup
        cur.execute("DELETE FROM agendas WHERE medico_id = %s", (medico_id,))
        cur.execute("DELETE FROM atendimentos WHERE usuario_id = %s", (medico_id,))
        cur.execute("DELETE FROM usuarios WHERE id IN (%s, %s)", (medico_id, admin_id))
        db.commit()
        cur.close()
