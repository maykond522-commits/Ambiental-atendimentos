import os
import io
import time
import uuid
import hashlib
from pathlib import Path
import pytest
from app import app, get_db, _AUTH_CACHE, _AUTH_CACHE_LOCK, _parse_agenda_pdf_content

SAMPLE_PDF_PATH = r"C:/Users/maykon.moraes/.gemini/antigravity/brain/489024fa-3d24-468a-adee-a576b3498293/.user_uploaded/media_1791371382756.pdf"

@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client

def test_parse_agenda_pdf_content_with_sample_file():
    if not os.path.exists(SAMPLE_PDF_PATH):
        pytest.skip("Sample PDF not found at path")
        
    with open(SAMPLE_PDF_PATH, "rb") as f:
        pdf_bytes = f.read()
        
    result = _parse_agenda_pdf_content(pdf_bytes)
    assert result["data_ymd"] == "2026-10-01"
    assert result["data_formatada"] == "01/10/2026"
    assert len(result["itens"]) == 23
    
    # Check acompanhantes (coluna Pessoa = X)
    acomps = [x for x in result["itens"] if x["is_acompanhante"]]
    assert len(acomps) == 2
    acomp_names = [x["nome_periciado"] for x in acomps]
    assert "JANAINA FEITOZA S PORTUGAL" in acomp_names
    assert "ROBSON DOS SANTOS NASCIMENTO" in acomp_names
    for a in acomps:
        assert a["pessoa"] == "Acompanhante"
        
    # Check readaptados (coluna Read = S)
    reads = [x for x in result["itens"] if x["readaptado"] == "Sim"]
    assert len(reads) >= 1
    assert any(x["nome_periciado"] == "RENATO DE SOUZA ABELHA" for x in reads)

def test_admin_parse_agenda_pdf_endpoint_requires_admin(client):
    res = client.post("/api/admin/agendas/parse-pdf", data={})
    assert res.status_code in [401, 403]

def test_admin_parse_and_save_agenda_endpoint(client):
    if not os.path.exists(SAMPLE_PDF_PATH):
        pytest.skip("Sample PDF not found at path")

    with open(SAMPLE_PDF_PATH, "rb") as f:
        pdf_bytes = f.read()

    admin_id = f"test-adm-{uuid.uuid4().hex[:8]}"
    medico_id = f"test-med-{uuid.uuid4().hex[:8]}"
    now_iso = "2026-10-01T08:00:00Z"

    with app.app_context():
        db = get_db()
        cur = db.cursor()
        cur.execute("INSERT INTO usuarios (id, nome, email, perfil, criado_em) VALUES (%s, %s, %s, %s, %s)",
                    (admin_id, "Admin Perícias", "admin.pericias@teste.com", "Administrador", now_iso))
        cur.execute("INSERT INTO usuarios (id, nome, email, perfil, crm, criado_em) VALUES (%s, %s, %s, %s, %s, %s)",
                    (medico_id, "Dr. Perito Oficial", "medico.oficial@teste.com", "Médico", "CRM 12345/SP", now_iso))
        db.commit()

    test_token = f"admin-token-{uuid.uuid4().hex}"
    token_hash = hashlib.sha256(test_token.encode("utf-8")).hexdigest()
    with _AUTH_CACHE_LOCK:
        _AUTH_CACHE[token_hash] = {
            "profile": {"id": admin_id, "nome": "Admin Perícias", "email": "admin.pericias@teste.com", "perfil": "Administrador"},
            "expires": time.time() + 3600
        }

    # 1. Parse PDF via endpoint
    resp = client.post(
        "/api/admin/agendas/parse-pdf",
        data={"file": (io.BytesIO(pdf_bytes), "agenda_pericias.pdf")},
        content_type="multipart/form-data",
        headers={"Authorization": f"Bearer {test_token}"}
    )
    assert resp.status_code == 200, f"Expected 200, got: {resp.data}"
    json_data = resp.get_json()["data"]
    assert json_data["success"] is True
    assert json_data["data"] == "2026-10-01"
    assert len(json_data["itens"]) == 23

    # 2. Save agendas with acompanhantes and readaptados
    save_payload = {
        "data": json_data["data"],
        "itens": json_data["itens"],
        "substituir": True
    }
    save_resp = client.post(
        f"/api/admin/medicos/{medico_id}/agendas",
        json=save_payload,
        headers={"Authorization": f"Bearer {test_token}"}
    )
    assert save_resp.status_code == 200, f"Expected 200, got: {save_resp.data}"
    assert save_resp.get_json()["data"]["count"] == 23

    # 3. List agendas and check pessoa and readaptado persisted
    list_resp = client.get(
        f"/api/admin/medicos/{medico_id}/agendas?data=2026-10-01",
        headers={"Authorization": f"Bearer {test_token}"}
    )
    assert list_resp.status_code == 200
    items = list_resp.get_json()["data"]["items"]
    assert len(items) == 23
    acomps = [x for x in items if x.get("pessoa") == "Acompanhante"]
    assert len(acomps) == 2
    assert any(x["nome_periciado"] == "JANAINA FEITOZA S PORTUGAL" for x in acomps)
    reads = [x for x in items if x.get("readaptado") == "Sim"]
    assert len(reads) >= 1
    assert any(x["nome_periciado"] == "RENATO DE SOUZA ABELHA" for x in reads)

def test_frontend_contracts():
    root = Path(__file__).resolve().parent.parent
    api_js = (root / "api.js").read_text(encoding="utf-8")
    gestao_medicos_html = (root / "gestao_medicos.html").read_text(encoding="utf-8")
    gestao_admin_html = (root / "gestao-medicos-admin.html").read_text(encoding="utf-8")

    # 1. api.js contains saveDoctorAgendas and parseAgendaPdf
    assert "saveDoctorAgendas:" in api_js
    assert "parseAgendaPdf:" in api_js
    assert "deleteDoctorAgendas:" in api_js

    # 2. gestao_medicos.html impersonate banner is blue and compact
    assert "id=\"impersonateWarningBanner\"" in gestao_medicos_html
    assert "linear-gradient(90deg, #0369A1 0%, #0284C7 100%)" in gestao_medicos_html
    assert "padding:6px 18px" in gestao_medicos_html

    # 3. gestao_medicos.html locks finalized appointments
    assert "🔒 Atendimento Concluído" in gestao_medicos_html
    assert "statusAtd === 'FINALIZADO'" in gestao_medicos_html
    assert "agenda-card-finalizado" in gestao_medicos_html

    # 4. gestao_medicos.html has no "Não compareceu" button
    assert "Não Compareceu" not in gestao_medicos_html
    assert "não compareceu" not in gestao_medicos_html.lower()

    # 5. gestao-medicos-admin.html has PDF dropzone and handles PDF uploads
    assert "id=\"agendaPdfDropZone\"" in gestao_admin_html
    assert "btnTriggerPdfFile" in gestao_admin_html
    assert "parseAgendaPdf" in gestao_admin_html
    assert "payload?.itens || res?.itens || res?.data?.itens" in gestao_admin_html
