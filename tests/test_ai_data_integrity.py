from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.py").read_text(encoding="utf-8")
HTML = (ROOT / "gestao_atendimentos.html").read_text(encoding="utf-8")
EVAL = (ROOT / "ambiental_avaliacao_medica_lts_cid_assistente.html").read_text(encoding="utf-8")


def test_esisla_loads_authoritative_server_payload():
    assert "raw = _load_authoritative_ai_payload(raw)" in APP
    assert "const detailResponse = await AmbientalAuth.authFetch('/api/atendimentos/' + encodeURIComponent(id)" in HTML


def test_justification_context_contains_occupationally_relevant_fields():
    for token in ("doenca_motivo", "queixa_duracao", "medicamentos", "antecedentes", "exame_fisico_tipo", "atividades_comprometidas", "quesitos"):
        assert token in EVAL or token in APP


def test_esisla_does_not_invent_vitals():
    assert 'NÃO crie sinais vitais' in APP
    assert 'DEIXE O VALOR EM BRANCO' in APP


def test_esisla_strict_source_only_and_no_ai_markers():
    assert 'Use EXCLUSIVAMENTE informações presentes no questionário' in APP
    assert 'NÃO invente, complete, suponha, interprete ou deduza' in APP
    assert 'Não use linguagem que revele geração automática, IA ou assistência computacional' in APP
    assert 'Não acrescente o texto legal da justificativa final' in APP


def test_esisla_cache_version_and_deterministic_generation():
    assert 'ESISLA_PROMPT_VERSION' in APP
    assert 'prompt_version = ESISLA_PROMPT_VERSION if endpoint.endswith("/esisla") else "default"' in APP
    assert 'temperature=0.0 if endpoint.endswith("/esisla") else 0.2' in APP

def test_esisla_rewrites_only_five_narrative_fields_from_explicit_sources():
    for token in (
        'REDAÇÃO INTELIGENTE DOS CINCO CAMPOS NARRATIVOS',
        'Queixa e Duração',
        'Antecedentes Mórbidos',
        '(*)Exame Físico Geral',
        'Descrição das Alterações Clínicas encontradas e Relato dos Exames Complementares',
        '(*)Descrição da(s) Limitação(ções) Física(s) e/ou Mental(is) encontrada(s)',
        'ZERO INFORMAÇÃO NOVA',
        'exame_fisico_descricao',
        'pressao_sistolica',
        'pressao_diastolica',
        'pulso',
    ):
        assert token in APP
