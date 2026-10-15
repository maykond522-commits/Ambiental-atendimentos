import pytest
from pathlib import Path
from app import parse_esisla_text, app

ROOT = Path(__file__).resolve().parents[1]
APP_PY = (ROOT / "app.py").read_text(encoding="utf-8")
ASSISTENTE_HTML = (ROOT / "ambiental_avaliacao_medica_lts_cid_assistente.html").read_text(encoding="utf-8")
GESTAO_HTML = (ROOT / "gestao_atendimentos.html").read_text(encoding="utf-8")


def test_parse_esisla_expedicao_textual_month_user_case():
    """
    Testa exatamente o caso enviado pelo usuário na imagem:
    Local e Data da Expedição: 'SAO VICENTE , 06 Outubro 2026'
    Data de Emissão do Atestado: '13/05/2026'
    Resultado esperado:
    - data_expedicao = '06/10/2026'
    - data_expedicao_iso = '2026-10-06'
    - data_documento = '2026-05-13'
    - retroacao_dias = 146 (> 3 dias)
    - retroacao_invalida = True
    - parecer = 'CONTRÁRIO'
    - justificativa contém texto padrão DPME de retroação > 3 dias
    """
    sample_text = """
GOVERNO DO ESTADO DE SÃO PAULO
DPME - DIRETORIA DE PERÍCIAS MÉDICAS DO ESTADO
GPM - Guia para Perícia Médica
Protocolo: 987654321
Nome: MARIA DA SILVA SANTOS
CPF: 123.456.789-00
RG: 12345678X
Data de Nascimento: 10/02/1980
Cargo: PROFESSOR EDUCACAO BASICA II
Órgão: 08000 - SECRETARIA DA EDUCACAO
UA: 12345 - EE MARGARIDA PINHO RODRIGUES
Local e Data da Expedição
EE MARGARIDA PINHO RODRIGUES        Documento gerado por:
SAO VICENTE          ,  06 Outubro 2026
Válida até o final do expediente do 1º dia útil subseqüente a Expedição    JUPIRA ALVES OLIVEIRA
Parecer do Médico Assistente
CRM: 86978 Nome: DRA SIMONE CRISTINA FERREIRA DE FREITAS
CID 10: J04 Dias: 2 Data de Emissão do Atestado: 13/05/2026
Tipo: A PEDIDO
Motivo: LTS - TRATAMENTO DE SAUDE
"""
    dados = parse_esisla_text(sample_text)

    assert dados.get("data_expedicao") == "06/10/2026"
    assert dados.get("data_expedicao_iso") == "2026-10-06"
    assert dados.get("data_documento") == "2026-05-13"
    assert dados.get("data_documento_br") == "13/05/2026"

    # Verificação estrita da regra de retroação inválida
    assert dados.get("retroacao_invalida") is True
    assert dados.get("retroacao_dias") == 146
    assert dados.get("parecer") == "CONTRÁRIO"
    assert "Guia com mais de 3 dias de retroação" in dados.get("justificativa", "")


def test_parse_esisla_expedicao_valida_dentro_do_prazo():
    """
    Testa caso com intervalo <= 3 dias (ex: expedição 25/09/2026 e atestado 24/09/2026 = 1 dia).
    Resultado esperado:
    - retroacao_invalida = False
    - retroacao_dias = 1
    - parecer NÃO é forçado como CONTRÁRIO
    """
    sample_text = """
Local e Data da Expedição
COLEGIO TECNICO DE CAMPINAS Documento gerado por:
CAMPINAS , 25 Setembro 2026
Parecer do Médico Assistente
CRM: 238997 Nome: THAYNA B GRIGGIO
CID 10: J029 Dias: 2 Data de Emissão do Atestado: 24/09/2026
"""
    dados = parse_esisla_text(sample_text)

    assert dados.get("data_expedicao") == "25/09/2026"
    assert dados.get("data_documento") == "2026-09-24"
    assert dados.get("retroacao_invalida") is False
    assert dados.get("retroacao_dias") == 1
    assert dados.get("parecer") != "CONTRÁRIO"


def test_frontend_uses_data_expedicao_reference():
    """
    Verifica que o frontend em ambiental_avaliacao_medica_lts_cid_assistente.html:
    1. Lê a data de expedição em calcularDatasAtestado como prioridade sobre a data atual.
    2. Possui o input de data de expedição (agilDataExpedicao).
    3. Possui a função aplicarParecerContrarioRetroacao().
    """
    assert "agilDataExpedicao" in ASSISTENTE_HTML
    assert "calcDataExpedicaoTxt" in ASSISTENTE_HTML
    assert "calcRetroacaoTxt" in ASSISTENTE_HTML
    assert "aplicarParecerContrarioRetroacao" in ASSISTENTE_HTML
    assert "const isUsingExpedicao = !!expDate;" in ASSISTENTE_HTML
    assert "refDate = expDate || todayZero" in ASSISTENTE_HTML


def test_gestao_preview_has_expedicao_and_retroacao_alert():
    """
    Verifica que gestao_atendimentos.html possui o badge de expedição e alerta de retroação inválida.
    """
    assert "prevDataExpedicaoBadge" in GESTAO_HTML
    assert "prevRetroacaoAlert" in GESTAO_HTML
    assert "prevRetroacaoTexto" in GESTAO_HTML
