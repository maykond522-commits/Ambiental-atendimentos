# -*- coding: utf-8 -*-
"""
Testes de validação da qualidade de redação da Ficha e-SISLA:
1. Eliminação de 'Queixa-se de Relata que' / 'Queixa-se de Refere que'.
2. Eliminação de repetição viciosa entre 'com queixa de' e 'Queixa-se de'.
3. Unificação de ponto final espúrio entre doença e início de tratamento/consultas ('dor local desde 2026').
4. Eliminação de barras soltas em dosagens ('Dipirona 1 g/' -> 'Dipirona 1 g').
5. Pontuação e contexto adequado em indicações como 'Analgesia' ('não informado sua dosagem, para analgesia').
6. Remoção de CAPSLOCK em cargos e textos na primeira geração da ficha e-SISLA.
"""
from pathlib import Path
import pytest
from app import _clean_queixa_duracao_text, _clean_antecedentes_morbidos_text, _clean_esisla_text, TASK_PROMPTS

ROOT = Path(__file__).resolve().parent.parent
ATTENDANCE_HTML = (ROOT / "ambiental_avaliacao_medica_lts_cid_assistente.html").read_text(encoding="utf-8")
GESTAO_HTML = (ROOT / "gestao_atendimentos.html").read_text(encoding="utf-8")
APP_PY = (ROOT / "app.py").read_text(encoding="utf-8")

def test_clean_queixa_duracao_caso_real_usuario():
    texto_usuario = (
        "Servidora de 46 anos, relatou ser readaptada, é Professor de Educação Básica II há 20 anos, "
        "com queixa de Pós-operatório de mastopexia e ressecção de nódulos mamários com deiscência parcial de sutura cirúrgica, edema e dor local. "
        "Desde 2026, realizando consultas mensalmente. "
        "Queixa-se de Relata que realizou cirurgia de mastopexia e ressecção de dois nódulos mamários, apresentando no pós-operatório dor local contínua, edema e abertura de 3 pontos cirúrgicos, acarretando limitação funcional para movimentação ampla de membros superiores e esforço físico. "
        "Em uso de Dipirona 1 g/, não informado sua dosagem Analgesia. "
        "Não relatou troca de alteração de dosagem da medicação. "
        "Não alegou fazer fisioterapia e psicoterapia."
    )

    resultado = _clean_queixa_duracao_text(texto_usuario)

    # 1. 'Queixa-se de Relata que' eliminado
    assert "Queixa-se de Relata" not in resultado
    assert "Relata que realizou cirurgia" in resultado

    # 2. Ponto final espúrio removido antes de 'desde 2026'
    assert "dor local desde 2026, realizando consultas mensalmente" in resultado

    # 3. Barra solta removida e analgesia pontuada formalmente
    assert "Dipirona 1 g/" not in resultado
    assert "Dipirona 1 g, não informado sua dosagem, para analgesia" in resultado
    assert "não informado sua dosagem Analgesia" not in resultado

def test_clean_esisla_text_primeira_geracao_aplica_capslock_e_regras():
    ficha_com_capslock = (
        "Registro da perícia Médica para Licença\n\n"
        "(*) Queixa e Duração:\n"
        "Servidora de 46 anos, relatou ser readaptada, é PROFESSOR DE EDUCACAO BASICA II há 20 anos, "
        "com queixa de pós-operatório. Desde 2026, realizando consultas mensalmente. "
        "Queixa-se de Relata que realizou cirurgia. "
        "Em uso de Dipirona 1 g/, não informado sua dosagem Analgesia. "
        "Não relatou troca de alteração de dosagem da medicação. "
        "Não alegou fazer fisioterapia e psicoterapia.\n\n"
        "Antecedentes Mórbidos:\n"
        "Nega antecedentes mórbidos relevantes, cirurgias prévias e neoplasias.\n\n"
        "Atestado/Relatório/Exames Complementares:\n"
        "Em anexo.\n\n"
        "(*)Exame Físico Geral\n"
        "Cicatriz cirúrgica em mama com deiscência parcial.\n\n"
        "Descrição das Alterações Clínicas encontradas e Relato dos Exames Complementares:\n"
        "Não foram apresentados exames complementares (imagem ou laboratoriais) no ato pericial.\n\n"
        "(*)Descrição da(s) Limitação(ções) Física(s) e/ou Mental(is) encontrada(s):\n"
        "Limitação para movimentação ampla de membros superiores.\n\n"
        "(*)Parecer Médico\n"
        "Parecer: FAVORÁVEL\n"
        "Nº Dias: 30\n"
        "Data Início: 01/10/2026\n"
        "CID 10: T81.3\n"
        "Descrição: Deiscência de sutura cirúrgica\n"
        "Médico Perito: Dr. Perito\n"
        "CRM: 12345\n"
        "Dt/Hr Perícia: 01/10/2026 10:00\n\n"
        "(*)Resposta aos quesitos\n"
        "1) Sim\n"
        "2) Sim\n"
        "3) Sim\n\n"
        "(*)Justificativa Parecer Médico\n"
        "Capacidade laborativa temporariamente prejudicada para esforço físico.\n\n"
        "(*) Parecer Final\n"
        "Nº Dias: 30\n"
        "Data Início: 01/10/2026\n"
        "CID 10: T81.3\n"
    )

    limpa = _clean_esisla_text(ficha_com_capslock)

    # Cargo convertido de CAPSLOCK para caixa mista
    assert ("Professora de Educação Básica II" in limpa or "Professor de Educação Básica II" in limpa)

    # Queixa-se de Relata que eliminado
    assert "Queixa-se de Relata" not in limpa
    assert "Relata que realizou cirurgia" in limpa

    # Barra solta e analgesia corrigidas
    assert "Dipirona 1 g, não informado sua dosagem, para analgesia" in limpa

def test_frontend_contracts_queixa_melhoria_continua():
    # 1. Assistente HTML possui regra anti-prefixo e anti-repetição
    assert 'sClean.replace(/^[Qq]ueixa-se\\s+de\\s+[Rr]elata\\s+que\\s+/i, "Relata que ");' in ATTENDANCE_HTML
    assert r'replace(/[\.\,\;\:]+$/, "")' in ATTENDANCE_HTML
    assert 'item += `, para analgesia`;' in ATTENDANCE_HTML

    # 2. Ambos os HTMLs possuem regras atualizadas em cleanQueixaDuracao
    assert 't = t.replace(/\\bQueixa-se de\\s+[Rr]elata(?:r|ndo)?\\s+que\\b/gi, "Relata que");' in ATTENDANCE_HTML
    assert 't = t.replace(/\\bQueixa-se de\\s+[Rr]elata(?:r|ndo)?\\s+que\\b/gi, "Relata que");' in GESTAO_HTML
    assert 't = t.replace(/\\bn[ãa]o\\s+informad[oa]\\s+sua\\s+dosagem\\s+Analgesia\\b/gi, "não informado sua dosagem, para analgesia");' in ATTENDANCE_HTML
    assert 't = t.replace(/\\bn[ãa]o\\s+informad[oa]\\s+sua\\s+dosagem\\s+Analgesia\\b/gi, "não informado sua dosagem, para analgesia");' in GESTAO_HTML

def test_clean_queixa_duracao_caso_acompanhante_imagem_usuario():
    texto_imagem = (
        "Servidora de 35 anos, relatou não ser readaptada, é Técnico de Enfermagem há 4 anos, "
        "com queixa de Acompanhamento de pessoa doente, sua filha menor de idade: Manuela Bueno Braga. "
        "Desde 02/10/2026. "
        "Queixa-se de A periciada refere que acompanha a filha menor, a qual iniciou com febre, tosse e odinofagia, "
        "estando em uso de amoxicilina e apresentando melhora da febre no dia da avaliação, com orofaringe hiperemiada. "
        "Negou uso de medicações. "
        "Não relatou troca de alteração de dosagem da medicação. "
        "Não alegou fazer fisioterapia e psicoterapia."
    )
    resultado = _clean_queixa_duracao_text(texto_imagem)

    # 1. 'Queixa-se de A periciada refere que' eliminado
    assert "Queixa-se de A periciada" not in resultado
    assert "A periciada refere que acompanha a filha menor" in resultado

    # 2. Ponto final espúrio removido antes de 'desde 02/10/2026'
    assert "Manuela Bueno Braga, desde 02/10/2026" in resultado
    assert "Braga. Desde 02/10/2026" not in resultado

    # 3. Flexão correta de gênero do cargo no feminino
    assert "é Técnico de Enfermagem" not in resultado
    assert "é Técnica de Enfermagem há 4 anos" in resultado

    # 4. Contexto de acompanhante sem 'com queixa de acompanhamento'
    assert "com queixa de Acompanhamento de pessoa doente" not in resultado
    assert "para acompanhamento de familiar enfermo" in resultado

    # 5. Negação de medicação da servidora clara e sem contradição com o dependente
    assert "A servidora negou uso de medicações próprias de uso contínuo." in resultado


def test_antecedentes_morbidos_desduplicacao_caso_usuario():
    # Caso 1: Texto com duplicidade exata reportada pelo usuário
    texto_usuario = "Nega outras comorbidades crônicas relevantes. Nega demais antecedentes mórbidos relevantes, cirurgias prévias e neoplasias."
    res = _clean_antecedentes_morbidos_text(texto_usuario)
    assert res == "Nega outras comorbidades crônicas relevantes, cirurgias prévias e neoplasias."
    assert "Nega demais antecedentes" not in res
    assert "Nega outras comorbidades crônicas relevantes. Nega" not in res

    # Caso 2: Entrada simples de negação sem o complemento
    texto_simples = "Nega outras comorbidades crônicas relevantes."
    res2 = _clean_antecedentes_morbidos_text(texto_simples)
    assert res2 == "Nega outras comorbidades crônicas relevantes, cirurgias prévias e neoplasias."
    assert "Nega demais antecedentes" not in res2

    # Caso 3: Negação pura ("Nega" ou "Nega.")
    res3 = _clean_antecedentes_morbidos_text("Nega.")
    assert res3 == "Nega."

    # Caso 4: Relato positivo de comorbidades prévias deve manter o complemento formal pericial
    texto_positivo = "Refere histórico relacionado a Artrose avançada no joelho direito há cerca de 5 anos."
    res4 = _clean_antecedentes_morbidos_text(texto_positivo)
    assert "Nega demais antecedentes mórbidos relevantes, cirurgias prévias e neoplasias." in res4
    assert res4.startswith("Refere histórico relacionado a Artrose avançada")

    # Caso 5: Limpeza dentro da ficha inteira e-SISLA
    ficha_exemplo = (
        "Registro da perícia Médica para Licença\n\n"
        "(*) Queixa e Duração:\n"
        "Servidora de 46 anos, relatou ser readaptada, é Professora de Educação Básica II há 20 anos.\n\n"
        "Antecedentes Mórbidos:\n"
        "Nega outras comorbidades crônicas relevantes. Nega demais antecedentes mórbidos relevantes, cirurgias prévias e neoplasias.\n\n"
        "Atestado/Relatório/Exames Complementares:\n"
        "Atestado médico anexado.\n"
    )
    ficha_limpa = _clean_esisla_text(ficha_exemplo)
    assert "Nega outras comorbidades crônicas relevantes, cirurgias prévias e neoplasias." in ficha_limpa
    assert "Nega demais antecedentes" not in ficha_limpa


def test_refinamento_10_fichas_usuario():
    # Caso 1: Gênero de Professor -> Professora e Dipirona 1 g sem negação de dosagem espúria
    f1 = (
        "Servidora de 46 anos, relatou ser readaptada, é Professor de Educação Básica II há 20 anos, "
        "com queixa de Pós-operatório de mastopexia e ressecção de nódulos mamários com deiscência parcial de sutura cirúrgica, edema e dor local desde 2026, realizando consultas mensalmente. "
        "Relata que realizou cirurgia de mastopexia e ressecção de dois nódulos mamários, apresentando no pós-operatório dor local contínua, edema e abertura de 3 pontos cirúrgicos, acarretando limitação funcional para movimentação ampla de membros superiores e esforço físico. "
        "Em uso de Dipirona 1 g, não informado sua dosagem, para analgesia. "
        "Não relatou troca de alteração de dosagem da medicação. Não alegou fazer fisioterapia e psicoterapia."
    )
    r1 = _clean_queixa_duracao_text(f1)
    assert "é Professora de Educação Básica II" in r1
    assert "Dipirona 1 g" in r1
    assert "para analgesia." in r1
    assert "Dipirona 1 g/" not in r1

    # Caso 2: Gênero Professora, eliminação de 'com queixa ... Queixa-se de' e crase em 'sensibilidade à luz'
    f2 = (
        "Servidora de 38 anos, relatou não ser readaptada, é Professor há 3 anos, com queixa de câncer ocular desde 2026. "
        "Queixa-se de visão baixa, sensibilidade a luz, lacrimejamento, hiperemia ocular e edema de pálpebra esquerda. "
        "Negou uso de medicações. Não relatou troca de alteração de dosagem da medicação. Não alegou fazer fisioterapia e psicoterapia."
    )
    r2 = _clean_queixa_duracao_text(f2)
    assert "é Professora há 3 anos" in r2
    assert "Refere visão baixa" in r2
    assert "Queixa-se de visão baixa" not in r2
    assert "sensibilidade à luz" in r2

    # Caso 4: Concordância 'há 1 ano' e eliminação de duplicação 'não informado sua dosagem Não informada'
    f4 = (
        "Servidora de 42 anos, relatou não ser readaptada, é Técnica de Enfermagem há 1 anos, com queixa de Sinusite e conjuntivite aguda desde 2026. "
        "Refere secreção ocular, prurido, hiperemia e dor em face. Apresenta melhora do quadro clínico atual. "
        "Em uso de Amoxicilina com Clavulanato, não informado sua dosagem Não informada. "
        "Não relatou troca de alteração de dosagem da medicação. Não alegou fazer fisioterapia e psicoterapia."
    )
    r4 = _clean_queixa_duracao_text(f4)
    assert "há 1 ano" in r4
    assert "há 1 anos" not in r4
    assert "não informada sua dosagem." in r4
    assert "Não informada" not in r4

    # Caso 5: Professora de Educação Básica II (preposição e gênero) e sem 'Queixa-se de' repetido
    f5 = (
        "Servidora de 57 anos, relatou não ser readaptada, é Professor Educação Básica II, com queixa de esgotamento profissional e sintomas de insônia, cansaço e déficit de concentração. "
        "Queixa-se de insônia, cansaço e pouca concentração. Atualmente refere melhora da insônia com o uso de alprazolam. "
        "Em uso de Alprazolam, não informado sua dosagem e Losartana, não informado sua dosagem. "
        "Não relatou troca de alteração de dosagem da medicação. Não alegou fazer fisioterapia e psicoterapia."
    )
    r5 = _clean_queixa_duracao_text(f5)
    assert "é Professora de Educação Básica II" in r5
    assert "Refere insônia" in r5
    assert "Alprazolam e Losartana, e não foram informadas suas dosagens" in r5

    # Caso 6: Gênero Enfermeira, 'Refere dor de ouvido' e pontuação com frequência
    f6 = (
        "Servidora de 38 anos, relatou não ser readaptada, é Enfermeiro há 4 anos, com queixa de Paralisia de Bell / Paralisia facial à esquerda com antecedente de herpes ótico. "
        "Queixa-se de dor de ouvido, dor mandibular, melhora do quadro atual, apresenta paralisia facial à direita, sem secreção em ouvidos. "
        "Em uso de Pregabalina, não informado sua dosagem a cada 12 horas. "
        "Não relatou troca de alteração de dosagem da medicação. Não alegou fazer fisioterapia e psicoterapia."
    )
    r6 = _clean_queixa_duracao_text(f6)
    assert "é Enfermeira há 4 anos" in r6
    assert "Refere dor de ouvido" in r6
    assert "sua dosagem, a cada 12 horas" in r6

    # Caso 7: Artigo 'O periciado refere', parênteses em sintomáticos e eliminação de s/n
    f7 = (
        "Servidor de 30 anos, relatou não ser readaptado, é Técnico em Administração há 4 anos, com queixa de Síndrome gripal / Influenza desde 2026. "
        "Periciado refere tosse, febre, mal-estar e coriza, estando atualmente em melhora do quadro gripal, apresentando voz anasalada, sem febre. "
        "Em uso de Nimesulida, não informado sua dosagem (Sintomático) e Dipirona 1 g se dor até 6/6h (Uso sintomático s/n). "
        "Não relatou troca de alteração de dosagem da medicação. Não alegou fazer fisioterapia e psicoterapia."
    )
    r7 = _clean_queixa_duracao_text(f7)
    assert "O periciado refere tosse" in r7
    assert "(para alívio sintomático)" in r7
    assert "(uso sintomático se necessário)" in r7
    assert "s/n" not in r7

    # Caso 9: Desaglutinação de mgdia -> mg/dia e remoção de negação de troca de dose quando houve aumento relatado
    f9 = (
        "Servidor de 42 anos, relatou não ser readaptado, é Policial penal há 13 anos, com queixa de irritabilidade, angústia e pensamentos de morte há 1 ano. "
        "Alega que trabalha na vigília, fica muito sozinho e já pensou em se matar usando sua arma, além de ter pensado em causar um acidente enquanto dirigia. "
        "Queixa-se de sintomas de angústia, irritabilidade e pensamentos de morte. "
        "Alega que recentemente foi aumentada a medicação devido à não resolução do quadro. "
        "Em uso de Exodus 10 mgdia, Carbolitium 300 mgdia, Melatonina 6 mgdia e Risperidona 2 mgdia. "
        "Não relatou troca de alteração de dosagem da medicação. Não alegou fazer fisioterapia e psicoterapia."
    )
    r9 = _clean_queixa_duracao_text(f9)
    assert "Exodus 10 mg/dia" in r9
    assert "Carbolitium 300 mg/dia" in r9
    assert "Melatonina 6 mg/dia" in r9
    assert "Risperidona 2 mg/dia" in r9
    assert "mgdia" not in r9
    assert "Não relatou troca de alteração de dosagem da medicação" not in r9

    # Caso 10: Laserterapia, Seacalm e antecedentes sem prefixos anômalos nem espaços antes de ponto
    f10 = (
        "Servidora de 51 anos, relatou não ser readaptada, é Psicóloga há 24 anos, com queixa de dor e rangendo os dentes inferiores com desconforto em mandíbula e cabeça associada a ansiedade há 8 meses. "
        "Queixa-se de dor em mandíbula e dor de cabeça há 8 meses. "
        "Em uso de tratamento com toxina botulínica e laser terapia e ceacalm, não informado sua dosagem. "
        "Não relatou troca de alteração de dosagem da medicação. Realiza fisioterapia (e cessou terapia com psicóloga)."
    )
    r10 = _clean_queixa_duracao_text(f10)
    assert "laserterapia" in r10
    assert "Seacalm" in r10
    assert "e cessou terapia com psicóloga." in r10
    assert "(e cessou" not in r10

    ant10 = (
        "Refere histórico relacionado a Alega ter apresentado dor e rangendo os dentes inferiores com desconforto em mandíbula e cabeça, há 8 meses . "
        "Relata ansiedade associada . Transtorno doloroso somatoforme persistente. Nega demais antecedentes mórbidos relevantes, cirurgias prévias e neoplasias."
    )
    rant10 = _clean_antecedentes_morbidos_text(ant10)
    assert "Refere histórico de dor e bruxismo" in rant10 or "Refere histórico de dor" in rant10
    assert "Alega ter apresentado" not in rant10
    assert "há 8 meses." in rant10
    assert "associada." in rant10
    assert "há 8 meses ." not in rant10
    assert "Nega demais antecedentes mórbidos relevantes, cirurgias prévias e neoplasias." in rant10


def test_caso_servidora_peb_ii_multiplas_medicacoes_sem_dosagem():
    texto = (
        "Servidora de 61 anos, relatou não ser readaptada, é Peb II há 14 anos, com queixa de dor na região cervical e no ouvido após agressão física por aluno, ocorrida há aproximadamente 7 dias. "
        "Refere episódios de taquicardia, dormência nas mãos e braços, além de dor difusa pelo corpo, cervicalgia, dor em ouvido, taquicardia, parestesia em mãos e braços, dor generalizada e tristeza. "
        "Em uso de Cetoprofeno, não informado sua dosagem, tramadol, não informado sua dosagem, dipirona, não informado sua dosagem, meclizina, não informado sua dosagem e cetorolaco, não informado sua dosagem. "
        "Não relatou troca de alteração de dosagem da medicação. Não alegou fazer fisioterapia e psicoterapia."
    )
    resultado = _clean_queixa_duracao_text(texto)

    # 1. Cargo PEB II expandido e com gênero feminino
    assert "é Professora de Educação Básica II há 14 anos" in resultado

    # 2. Múltiplas medicações consolidadas sem repetição de 'não informado sua dosagem'
    assert "Em uso de Cetoprofeno, Tramadol, Dipirona, Meclizina e Cetorolaco, e não foram informadas suas dosagens." in resultado
    assert "não informado sua dosagem" not in resultado

    # 3. Deduplicação de sintomas repetidos ou sinônimos óbvios
    assert "cervicalgia, dor em ouvido" not in resultado
    assert resultado.count("taquicardia") == 1
    assert "parestesia em mãos e braços" not in resultado
    assert "dor generalizada" not in resultado




