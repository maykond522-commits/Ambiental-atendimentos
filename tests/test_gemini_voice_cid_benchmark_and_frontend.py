from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]


def test_gemini_model_configuration():
    app_py = (ROOT / "app.py").read_text(encoding="utf-8")
    assert 'GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")' in app_py
    assert "gemini-3.5-flash-lite" in app_py
    assert "gemini-3.6-flash" in app_py
    assert "gemini-3.5-flash" in app_py


def test_voice_transcription_endpoint_contract():
    app_py = (ROOT / "app.py").read_text(encoding="utf-8")
    assert '@app.post("/api/ai/transcrever-atendimento")' in app_py
    assert "def api_ai_transcrever_atendimento():" in app_py
    assert "_authenticate_request()" in app_py
    assert "audio_base64" in app_py
    assert "audio_bytes" in app_py
    assert "mime_type" in app_py
    assert "transcricao" in app_py
    assert "dados_extraidos" in app_py


def test_cid_benchmark_endpoint_contract():
    app_py = (ROOT / "app.py").read_text(encoding="utf-8")
    assert '@app.route("/api/ai/benchmark-cid", methods=["GET", "POST"])' in app_py
    assert '@app.route("/api/ai/benchmark-cid/<cid_code>", methods=["GET"])' in app_py
    assert "def api_ai_benchmark_cid" in app_py
    assert "limite_junta_medica" in app_py
    assert "dias_medio" in app_py
    assert "faixa_usual" in app_py
    assert "regras_dpme" in app_py


def test_static_assets_http_caching():
    app_py = (ROOT / "app.py").read_text(encoding="utf-8")
    assert "max-age=86400" in app_py
    assert "public, max-age=86400" in app_py


def test_esisla_core_module_and_exports():
    esisla_core_js = (ROOT / "esisla_core.js").read_text(encoding="utf-8")
    assert (ROOT / "esisla_core.js").exists()
    assert "MAPA_NOMES_ESISLA" in esisla_core_js
    assert "detectarSistemaExameFisico" in esisla_core_js
    assert "sanitizarTexto" in esisla_core_js
    assert "validarConformidadeEsisla" in esisla_core_js
    assert "window.EsislaCore" in esisla_core_js


def test_api_js_client_methods():
    api_js = (ROOT / "api.js").read_text(encoding="utf-8")
    assert "transcreverAtendimento" in api_js
    assert "benchmarkCid" in api_js
    assert "/api/ai/transcrever-atendimento" in api_js
    assert "/api/ai/benchmark-cid" in api_js


def test_attendance_html_voice_and_benchmark():
    attendance = (ROOT / "ambiental_avaliacao_medica_lts_cid_assistente.html").read_text(encoding="utf-8")
    assert 'src="/esisla_core.js"' in attendance
    assert 'id="btnGravarVozIA"' in attendance
    assert 'id="modalGravadorVozIA"' in attendance
    assert 'id="btnBenchmarkCID"' in attendance
    assert 'id="cidBenchmarkBox"' in attendance
    assert "abrirModalGravadorVozIA" in attendance
    assert "fecharModalGravadorVozIA" in attendance
    assert "alternarGravacaoVozIA" in attendance
    assert "processarAudioGravadoIA" in attendance
    assert "consultarBenchmarkCID" in attendance
    assert "aplicarBenchmarkJustificativa" in attendance


def test_gestao_html_voice_and_benchmark():
    gestao = (ROOT / "gestao_atendimentos.html").read_text(encoding="utf-8")
    assert 'src="/esisla_core.js"' in gestao
    assert 'id="btnBenchmarkDetail"' in gestao
    assert 'id="modalBenchmarkGestao"' in gestao
    assert 'id="btnDitadoGestao"' in gestao
    assert "consultarBenchmarkDetail" in gestao
    assert "iniciarDitadoParaAtendimento" in gestao


def test_live_benchmark_endpoint():
    from app import app
    client = app.test_client()

    resp = client.get("/api/ai/benchmark-cid/F32.1")
    assert resp.status_code == 200
    body = json.loads(resp.data.decode("utf-8"))
    assert body.get("success") is True or body.get("sucesso") is True
    item = body.get("data", body)
    assert item["cid"] == "F32.1"
    assert item["dias_medio"] > 0
    assert "faixa_usual" in item
    assert "limite_junta_medica" in item
    assert "Psiquiatria" in item["especialidade"] or "Mental" in item["grupo"]
