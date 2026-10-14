"""
Testes automatizados para validação da Fase 1: Arquitetura & Robustez do Motor de IA.
Valida:
1. Modularização via Blueprints (atendimentos, ai, agendas, admin, esisla).
2. Modelos e Schemas Pydantic estritos para o motor Gemini.
3. Rota de streaming (/api/ai/justificativa/stream) com SSE.
"""
from pathlib import Path
import pytest
from pydantic import ValidationError

from app import app
from blueprints import (
    bp_atendimentos,
    bp_ai,
    bp_agendas,
    bp_admin,
    bp_esisla,
    RefinarFichaEsislaResult,
    AudioTranscricaoAtendimentoResult,
    DadosExtraidosAudio,
    JustificationResult,
    EsislaResult,
    FillSuggestionResult,
    generate_justificativa_stream,
)


def test_blueprints_existence_and_registration():
    # 1. Verifica integridade dos 5 blueprints
    assert bp_atendimentos.name == "bp_atendimentos"
    assert bp_ai.name == "bp_ai"
    assert bp_agendas.name == "bp_agendas"
    assert bp_admin.name == "bp_admin"
    assert bp_esisla.name == "bp_esisla"

    # 2. Verifica se estão devidamente registrados na aplicação Flask principal
    registered_blueprints = app.blueprints
    assert "bp_atendimentos" in registered_blueprints
    assert "bp_ai" in registered_blueprints
    assert "bp_agendas" in registered_blueprints
    assert "bp_admin" in registered_blueprints
    assert "bp_esisla" in registered_blueprints


def test_blueprint_files_structure():
    root = Path(__file__).resolve().parents[1]
    bp_dir = root / "blueprints"
    assert bp_dir.is_dir()
    assert (bp_dir / "__init__.py").is_file()
    assert (bp_dir / "atendimentos.py").is_file()
    assert (bp_dir / "ai.py").is_file()
    assert (bp_dir / "agendas.py").is_file()
    assert (bp_dir / "admin.py").is_file()
    assert (bp_dir / "esisla.py").is_file()


def test_pydantic_schemas_strict_validation():
    # 1. RefinarFichaEsislaResult
    valid_ficha = RefinarFichaEsislaResult(ficha_otimizada="Ficha pericial e-SISLA técnica.")
    assert valid_ficha.ficha_otimizada == "Ficha pericial e-SISLA técnica."
    with pytest.raises(ValidationError):
        RefinarFichaEsislaResult()

    # 2. AudioTranscricaoAtendimentoResult
    dados_audio = DadosExtraidosAudio(
        queixa_duracao="Dor lombar há 3 semanas",
        antecedentes="Hipertensão controlada",
        exame_fisico="Lasegue negativo bilateralmente",
        parecer="FAVORÁVEL",
        dias=15,
        cid="M54.5"
    )
    res_audio = AudioTranscricaoAtendimentoResult(
        transcricao="Ditado pericial realizado com sucesso...",
        dados_extraidos=dados_audio
    )
    assert res_audio.transcricao.startswith("Ditado")
    assert res_audio.dados_extraidos.dias == 15
    assert res_audio.dados_extraidos.cid == "M54.5"

    # 3. JustificationResult
    valid_just = JustificationResult(justificativa="Considero a capacidade laborativa parcial e temporariamente prejudicada.")
    assert "prejudicada" in valid_just.justificativa
    with pytest.raises(ValidationError):
        JustificationResult()

    # 4. EsislaResult
    valid_esisla = EsislaResult(ficha_esisla="Registro da perícia Médica para Licença...")
    assert "Registro" in valid_esisla.ficha_esisla


def test_streaming_endpoint_registered_and_guarded():
    # Verifica que a rota existe no mapa de URLs do Flask
    rules = [str(r) for r in app.url_map.iter_rules()]
    assert any("/api/ai/justificativa/stream" in r for r in rules)

    # Verifica que sem autenticação a rota bloqueia com 401
    client = app.test_client()
    resp = client.post("/api/ai/justificativa/stream", json={})
    assert resp.status_code == 401
    data = resp.get_json()
    assert data["error"]["code"] == "AUTH_ERROR"


def test_streaming_generator_sse_format():
    # Mock simplificado do cliente do Gemini para validar geração de SSE
    class MockChunk:
        def __init__(self, text):
            self.text = text

    class MockModels:
        def generate_content_stream(self, model, contents, config):
            yield MockChunk("Considero a capacidade ")
            yield MockChunk("laborativa prejudicada.")

    class MockClient:
        def __init__(self):
            self.models = MockModels()

    gen = generate_justificativa_stream(
        client=MockClient(),
        models=["gemini-2.5-flash"],
        instruction="Gerar justificativa",
        system_instruction="Sistema DPME"
    )

    chunks = list(gen)
    assert len(chunks) >= 3
    assert 'data: {"text": "Considero a capacidade ", "done": false}' in chunks[0]
    assert 'data: {"text": "laborativa prejudicada.", "done": false}' in chunks[1]
    assert '"done": true' in chunks[-1]
