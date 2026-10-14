"""
Testes automatizados para validação da Fase 2: Potencialização da Extensão e-SISLA & UX Frontend.
Valida:
1. Cliente de Streaming em tempo real no api.js (justificativaStream).
2. Integração do Streaming SSE e efeitos visuais na tela de avaliação pericial.
3. Extensão e-SISLA: Scraper de Agenda e HUD de Verificação Pericial (Checklist).
4. Endpoint de importação direta de agendamentos (/api/esisla/importar-agenda).
"""
from pathlib import Path
import pytest
from app import app

ROOT = Path(__file__).resolve().parents[1]
API_JS = (ROOT / "api.js").read_text(encoding="utf-8")
ATTENDANCE = (ROOT / "ambiental_avaliacao_medica_lts_cid_assistente.html").read_text(encoding="utf-8")
CONTENT_ESISLA = (ROOT / "extensao_esisla" / "content_esisla.js").read_text(encoding="utf-8")
CONTENT_ESISLA_CSS = (ROOT / "extensao_esisla" / "content_esisla.css").read_text(encoding="utf-8")
BACKGROUND_JS = (ROOT / "extensao_esisla" / "background.js").read_text(encoding="utf-8")
CONTENT_AMBIENTAL = (ROOT / "extensao_esisla" / "content_ambiental.js").read_text(encoding="utf-8")


def test_api_js_streaming_and_agenda_client():
    # 1. justificativaStream no namespace ai
    assert "justificativaStream:" in API_JS
    assert "/api/ai/justificativa/stream" in API_JS
    assert "text/event-stream" in API_JS
    assert "getReader()" in API_JS

    # 2. importarAgenda no namespace esisla
    assert "importarAgenda:" in API_JS
    assert "/api/esisla/importar-agenda" in API_JS


def test_attendance_html_streaming_ux():
    # 1. Chamada de streaming no apiAI
    assert "justificativaStream" in ATTENDANCE
    assert "TRANSMISSÃO EM TEMPO REAL" in ATTENDANCE
    assert 'id="aiStreamingOutput"' in ATTENDANCE

    # 2. Animações e Estilos de digitação em tempo real
    assert ".streaming-text" in ATTENDANCE
    assert ".cursor-blink" in ATTENDANCE
    assert "blink-ai" in ATTENDANCE


def test_extension_hud_checklist_and_agenda_scraper():
    # 1. Checklist / HUD de Verificação Pericial
    assert "function verificarChecklistLaudoEsisla" in CONTENT_ESISLA
    assert "function abrirModalChecklistSeguranca" in CONTENT_ESISLA
    assert "Identificação do Periciado" in CONTENT_ESISLA
    assert "Queixa e Duração" in CONTENT_ESISLA
    assert "Exame Físico Geral" in CONTENT_ESISLA
    assert "Parecer Médico" in CONTENT_ESISLA
    assert "Dias Concedidos" in CONTENT_ESISLA
    assert "CID-10 Principal" in CONTENT_ESISLA
    assert "Justificativa Pericial DPME" in CONTENT_ESISLA
    assert "ambientalWidgetBtnCheck" in CONTENT_ESISLA

    # 2. Scraper de Agenda e-SISLA 1-Clique
    assert "function extrairAgendaEsislaDaTela" in CONTENT_ESISLA
    assert "function importarAgendaEsisla" in CONTENT_ESISLA
    assert "ambientalWidgetBtnAgenda" in CONTENT_ESISLA
    assert "AGENDA_ESISLA_CAPTURADA" in CONTENT_ESISLA

    # 3. Estilos CSS da Extensão
    assert ".ambiental-widget-btn-check" in CONTENT_ESISLA_CSS
    assert ".ambiental-widget-btn-agenda" in CONTENT_ESISLA_CSS
    assert ".ambiental-checklist-item" in CONTENT_ESISLA_CSS

    # 4. Background e Bridge do Sistema Ambiental
    assert "AGENDA_ESISLA_CAPTURADA" in BACKGROUND_JS
    assert "AGENDA_ESISLA_DISPONIVEL" in BACKGROUND_JS
    assert "AGENDA_ESISLA_DISPONIVEL" in CONTENT_AMBIENTAL
    assert "exibirPromptImportarAgenda" in CONTENT_AMBIENTAL


def test_backend_agenda_import_endpoint():
    rules = [str(r) for r in app.url_map.iter_rules()]
    assert any("/api/esisla/importar-agenda" in r for r in rules)

    client = app.test_client()
    resp = client.post("/api/esisla/importar-agenda", json={"itens": []})
    assert resp.status_code == 401
    data = resp.get_json()
    assert data["error"]["code"] == "AUTH_ERROR"
