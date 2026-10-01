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


def test_esisla_programa_melhoria_continua_guidelines():
    required_phrases = (
        "Programa de Melhoria Contínua",
        "Dosagens sempre em mg/dia e histórico de trocas de medicações",
        "Doenças de base crônicas (HAS, DM, etc.)",
        "Cirurgias prévias e tempo decorrido",
        "Hábitos e vícios (uso ou negação registrada de bebida alcoólica, tabagismo ou substâncias ilícitas)",
        "Histórico de neoplasias e tratamentos associados",
        "solicita [dias_solicitados] dias de afastamento a partir de [data_documento], pelo CID [cid] – Relatório médico em anexo",
        "atividades estas constantes no Rol de Atividades do cargo",
        "Do ponto de vista médico não se observa limitações",
        "Capacidade laborativa parcial e temporariamente prejudicada",
        "Capacidade laborativa preservada",
        "tempo este considerado suficiente para restabelecimento da capacidade laborativa",
        "Guia com mais de 3 dias de retroação",
        "caracterizando sobreposição de períodos",
    )
    for phrase in required_phrases:
        assert phrase in APP, f"Falta a diretriz obrigatória de melhoria contínua: '{phrase}'"


def test_cid_catalog_and_info():
    import app
    info_dot = app.get_cid_info("J70.4")
    assert info_dot and "Transt" in info_dot.get("nome", "")
    info_nodot = app.get_cid_info("J704")
    assert info_nodot and "Transt" in info_nodot.get("nome", "")
    info_c20 = app.get_cid_info("C20")
    assert info_c20 and "reto" in info_c20.get("nome", "").lower()


def test_clean_justificativa_removes_granting_and_fixes_mismatched_cid():
    import app
    sample = (
        "Considero a capacidade laborativa parcial e temporariamente prejudicada considerando as atribuições do rol do cargo de "
        "Investigador de polícia, em razão de limitações na esfera de Aparelho Respiratório decorrentes do CID J70.4 (C20 — Neoplasia maligna do reto), "
        "tais como dispneia aos médios esforços. Concedo 1 dia de afastamento a contar da data de início dos sintomas, tempo este considerado suficiente "
        "para restabelecimento da capacidade laborativa para a função periciada."
    )
    cleaned = app._clean_justificativa_text(sample)
    assert "Concedo 1 dia" not in cleaned
    assert "tempo este considerado suficiente" not in cleaned
    assert "C20" not in cleaned
    assert "CID J70.4" in cleaned
    assert "Transt" in cleaned


def test_task_instruction_justificativa_sanitizes_mismatched_doenca_motivo():
    import app
    payload = {
        "cid": "J70.4",
        "doenca_motivo": "C20 — Neoplasia maligna do reto",
        "cargo": "Investigador de polícia",
        "idade": "38 anos",
        "exame_fisico_tipo": "Outros",
        "area_exame_clinico": "Aparelho Respiratório",
        "resultado_avaliacao": "Alterado",
    }
    instruction = app._task_instruction("justificativa", payload)
    assert "C20 — Neoplasia" not in instruction
    assert "Transt" in instruction


