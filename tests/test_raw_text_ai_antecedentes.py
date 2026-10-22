import pytest
from pathlib import Path
from app import parse_esisla_text, _clean_antecedentes_morbidos_text, _detectar_regiao_osteomuscular, PreenchimentoCompletoResult

ROOT = Path(__file__).resolve().parents[1]
APP_PY = (ROOT / "app.py").read_text(encoding="utf-8")
HTML_FILE = (ROOT / "ambiental_avaliacao_medica_lts_cid_assistente.html").read_text(encoding="utf-8")

def test_parse_esisla_text_extracts_antecedentes():
    sample_text = """
Registro da perícia Médica para Licença

(*) Queixa e Duração:
Servidora de 38 anos, relatou não ser readaptada, é Escrivã de Polícia há 7 anos, com queixa de Transtorno depressivo maior.

Antecedentes Mórbidos:
Nega antecedentes mórbidos relevantes, cirurgias prévias, neoplasias ou hábitos tabágicos e etilistas.

Atestado/Relatório/Exames Complementares:
Em anexo.
"""
    dados = parse_esisla_text(sample_text)
    assert "historico_pregresso" in dados
    assert "Nega antecedentes mórbidos relevantes" in dados["historico_pregresso"]
    assert dados["historicoPregresso"] == dados["historico_pregresso"]

def test_parse_esisla_text_extracts_comorbidities():
    sample_text = """
Consulta Médica Pericial
Queixa: Dor lombar
Antecedentes:
Refere hipertensão arterial sistêmica em uso de Losartana 50mg ao dia. Nega diabetes e cirurgias prévias.
Exame Físico:
Dor à palpação paravertebral.
"""
    dados = parse_esisla_text(sample_text)
    assert "historico_pregresso" in dados
    assert "hipertensão arterial sistêmica" in dados["historico_pregresso"]

def test_parse_esisla_text_extracts_inline_comorbidities_without_header():
    # Caso onde o usuário apagou o cabeçalho 'Antecedentes Mórbidos:'
    sample_user_text = """
Nome Completo: MARIANA DA SILVA ALMEIDA
CPF: 345.892.108-72 RG: 42189034X Nasc: 14/05/1986
Cargo: Professor de Educação Básica II
Ingresso: 10/02/2012 Readaptado: Não
Servidora comparece referindo quadro de lombociatalgia intensa com irradiação para membro inferior direito iniciada há 3 semanas.
Em uso de Pregabalina 75mg 12/12h e Paracetamol com Codeína 30mg se dor forte. Nega psicoterapia. Iniciou fisioterapia motora esta semana (2x por semana).
Hipertensão arterial sistêmica diagnosticada há 4 anos em uso regular de Losartana 50mg ao dia. Relata cirurgia prévia de apendicectomia aos 18 anos sem intercorrências. Nega diabetes, neoplasias, tabagismo ou etilismo.
Deambulação com marcha antálgica à direita. Contratura muscular paravertebral lombar bilateral. Flexão de tronco limitada a 40 graus com dor. Teste de Lasègue positivo a 45 graus à direita. Reflexos patelar e aquileu presentes e simétricos. Sem déficits motores agudos em membros inferiores. PA: 125/80 mmHg, Pulso: 78 bpm.
Emitido em 21/10/2026 pelo Dr. Rodrigo Mendes (CRM 184520), solicitando 15 dias de repouso por CID M54.4 (Lombociatalgia).
Parecer: Favorável, conceder 15 dias a partir de 21/10/2026.
"""
    dados = parse_esisla_text(sample_user_text)
    assert "historico_pregresso" in dados
    assert "Hipertensão arterial sistêmica" in dados["historico_pregresso"]
    assert "apendicectomia" in dados["historico_pregresso"]
    assert dados.get("fisioterapia") is True
    assert dados.get("psicoterapia") is False

def test_detectar_terapias_texto_colloquial_and_informal():
    from app import _detectar_terapias_texto
    # 1. Caso informal bagunçado (Carlos Eduardo)
    t1 = "usa cetoprofeno 150mg 1x ao dia e codeina 30 se dor forte. ta fazendo fisio motora 3x por semana (ja fez 6 sessoes). nega psicoterapia."
    fisio1, psico1 = _detectar_terapias_texto(t1)
    assert fisio1 is True
    assert psico1 is False

    # 2. Ambas negadas em conjunto
    t2 = "Nega fazer fisioterapia ou psicoterapia. Sem comorbidades."
    fisio2, psico2 = _detectar_terapias_texto(t2)
    assert fisio2 is False
    assert psico2 is False

    # 3. Psicoterapia afirmativa e fisio negativa
    t3 = "Acompanhamento semanal com psicóloga. Não realiza fisioterapia."
    fisio3, psico3 = _detectar_terapias_texto(t3)
    assert fisio3 is False
    assert psico3 is True

    # 4. Ambas afirmativas
    t4 = "Em sessões de fisioterapia 2x por semana e psicoterapia quinzenal."
    fisio4, psico4 = _detectar_terapias_texto(t4)
    assert fisio4 is True
    assert psico4 is True

def test_detectar_regiao_osteomuscular():
    assert _detectar_regiao_osteomuscular("M54.4", "lombociatalgia direita", "dor lombar", "teste de lasegue") == "lombar"
    assert _detectar_regiao_osteomuscular("M54.5", "dor lombar", "lombalgia", "palpação lombar") == "lombar"
    assert _detectar_regiao_osteomuscular("M54.2", "dor cervical", "cervicalgia", "cervical") == "cervical"
    assert _detectar_regiao_osteomuscular("M75.1", "dor no ombro direito", "manguito", "jobe positivo") == "ombro_direito"
    assert _detectar_regiao_osteomuscular("M75.1", "dor no ombro esquerdo", "manguito esquerdo", "jobe positivo esq") == "ombro_esquerdo"
    assert _detectar_regiao_osteomuscular("M17.0", "dor no joelho direito", "gonartrose", "derrame articular") == "joelho_direito"
    # Mão e túnel do carpo
    assert _detectar_regiao_osteomuscular("G56.0", "sindrome do tunel do carpo mao esquerda", "parestesia dedos mao esq", "phalen positivo") == "mao_esquerda"
    assert _detectar_regiao_osteomuscular("G56.0", "tunel do carpo a direita", "dor ao digitar", "tinel direito") == "mao_direita"

def test_detectar_todas_regioes_osteomusculares_multiplos_segmentos():
    from app import _detectar_todas_regioes_osteomusculares
    regs = _detectar_todas_regioes_osteomusculares(
        "M51.1",
        "dorsolombalgia ciatalgia perna esquerda, associada a parestesia em dedos da mao esquerda e dor no cotovelo esquerdo ao digitar. phalen e tinel positivos no punho esquerdo, dor no epicondilo lateral esquerdo com teste de cozen positivo.",
        "transtornos de discos lombares",
        "espasmo paravertebral lombar, lasegue positivo a 45 graus no mbro inferior esquerdo",
        ["M54.4", "G56.0", "M77.1", "F41.2"]
    )
    assert "mao_esquerda" in regs
    assert "cotovelo_esquerdo" in regs
    assert "lombar" in regs

def test_app_py_preencher_ficha_has_antecedentes_and_fisioterapia_guarantees():
    # 1. Prompt includes mandatory directive
    assert 'CAMPO OBRIGATÓRIO — Histórico patológico pregresso / antecedentes mórbidos' in APP_PY
    assert 'ATENÇÃO CRÍTICA: Mesmo que o texto NÃO possua o cabeçalho explícito "Antecedentes Mórbidos:"' in APP_PY
    
    # 2. Endpoint guarantees populating historico_pregresso, fisioterapia, regiao_osteomuscular
    assert 'body["historicoPregresso"] = result.historico_pregresso' in APP_PY
    assert 'body["historico_pregresso"] = result.historico_pregresso' in APP_PY
    assert 'body["antecedentes"] = result.historico_pregresso' in APP_PY
    assert 'body["fisioterapia"] = bool(result.fisioterapia)' in APP_PY
    assert 'body["regiao_osteomuscular"] =' in APP_PY
    assert 'body["regioes_osteomusculares"] =' in APP_PY
    assert 'body["cids_secundarios"] = all_secondary' in APP_PY
    assert 'body["cidsSecundarios"] =' in APP_PY

def test_html_aplicar_preenchimento_ia_sets_antecedentes_and_osteo():
    html_content = (ROOT / "ambiental_avaliacao_medica_lts_cid_assistente.html").read_text(encoding="utf-8")
    # 1. Handles antParaPreencher with conditions fallback
    assert 'const PADRAO_NEGA_ANTECEDENTES = "Nega antecedentes mórbidos relevantes, cirurgias prévias, neoplasias ou hábitos tabágicos e etilistas.";' in html_content
    assert 'hasConds' in html_content
    assert 'state.historicoPregresso = antParaPreencher;' in html_content
    assert 'setVal("historicoPregresso", state.historicoPregresso);' in html_content

    # 2. Fisioterapia checkbox and sync guarantees
    assert 'setCheck("fisioterapia", state.fisioterapia);' in html_content
    assert '$("agilFisioterapia").checked = !!state.fisioterapia;' in html_content

    # 3. Interactive osteomuscular body map integration
    assert 'function detectarRegiaoOsteomuscular' in html_content
    assert 'function detectarTodasRegioesOsteomusculares' in html_content
    assert 'state.osteomuscularRegioes[r] = "Alterado";' in html_content
    assert 'aplicarOsteomuscularNormal();' in html_content
    assert 'updateOsteoUI();' in html_content

    # 4. Secondary CIDs and vital signs sanitization
    assert 'renderSecondaryCIDs();' in html_content
    assert 'state.cidsSecundarios = rawSecList;' in html_content
