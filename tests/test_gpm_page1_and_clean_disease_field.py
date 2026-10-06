from pathlib import Path
import pypdf
import pytest
from app import parse_esisla_text, app

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.py").read_text(encoding="utf-8")
ATTENDANCE = (ROOT / "ambiental_avaliacao_medica_lts_cid_assistente.html").read_text(encoding="utf-8")


def test_gpm_layout_extraction_complete():
    sample_gpm_page0 = """
GOVERNO DO ESTADO DE SÃO PAULO
DPME - DIRETORIA DE PERÍCIAS MÉDICAS DO ESTADO
Av Prefeito Passos S/N - Cx Postal 3078 - Cep 01517-020 - São Paulo-SP - Fone:(11) 3386-5001
SECRETARIA DE GESTÃO E GOVERNO DIGITAL
GPM - Guia para Perícia Médica
NI:
Nome: CPF: RG:
Sexo:Nasc.: Estado Civil: Def Físico:
Mãe: Pai:DENISE MARIA BARIANI MARCELINO
1495709
ALINE ROBERTA BARIANI MARCELIN 34258583863 344467648
FEMININO25/07/1985 CASADO
Status: ATIVO
Dados Pessoais
Endereço:
CEP:
Município:Bairro:
(19) 99267-1154Fone Contato:(19) 99267-9782Fone :
1Licenças:
Dados Funcionais
Órgão:
UA:
Endereço:
CEP:
Município:
Regime Jurídico: Cargo/Função: Ingresso:
121200000000000 - DEPARTAMENTO DE CIENCIAS
PROFESSOR MAG SEC TECNICO IIIAUTÁRQUICO
04858 - UNICAMP UNIVERSIDADE ESTADUAL DE CAMPINAS
CAMPINAS
02/05/2019
Readaptado: NAO Data Readaptação: CID-10:
Número: 954382209
CAMPINAS
Válida até o final do expediente do 1º dia útil subseqüente a Expedição
25 Setembro 2026,
Local e Data da Expedição
COLEGIO TECNICO DE CAMPINAS Documento gerado por:
KAREN LEANDRO DA SILVA
Parecer do Médico Assistente
CRM: 238997 Nome: THAYNA B GRIGGIO
CID 10: J029 2Dias: Data de Emissão do Atestado: 24/09/2026
Sobre a Perícia
Tipo:
Pessoa a ser periciada:
A PEDIDO
Nome:O PROPRIO 
Motivo: LTS - TRATAMENTO DE SAUDE
Local da Perícia: EXTERNO CAMPINAS - POLI LEM SERVIÇOS MEDICOS E HOSPITALARES
Data Perícia: 28/09/2026 09:03
Município:
Hospital/Domiciliar:
Registro da Perícia Médica para LicençaQueixa e Duração:
Página 1 de 4Emissão:06/10/2026 10:05 05884450885
"""
    dados = parse_esisla_text(sample_gpm_page0)

    # 1. Campos essenciais cadastrais e periciais
    assert dados["protocolo"] == "954382209"
    assert dados["nome_paciente"] == "ALINE ROBERTA BARIANI MARCELIN"
    assert dados["cpf_paciente"] == "342.585.838-63"
    assert dados["rg_paciente"] == "344467648"
    assert dados["ni"] == "1495709"
    assert dados["sexo"] == "Feminino"
    assert dados["data_nascimento"] == "25/07/1985"
    assert dados["orgao"] == "04858 - UNICAMP UNIVERSIDADE ESTADUAL DE CAMPINAS"
    assert dados["unidade"] == "121200000000000 - DEPARTAMENTO DE CIENCIAS"
    assert dados["cargo"] == "PROFESSOR MAG SEC TECNICO III"
    assert dados["regime_juridico"] == "AUTÁRQUICO"
    assert dados["municipio"] == "CAMPINAS"
    assert dados["readaptado"] == "Não"
    assert dados["crm_cro"] == "238997"
    assert dados["nome_medico_assistente"] == "THAYNA B GRIGGIO"
    assert dados["cid"] == "J02.9"
    assert dados["dias_solicitados"] == "2"
    assert dados["data_documento"] == "2026-09-24"
    assert dados["motivo_pericia"] == "LTS - TRATAMENTO DE SAUDE"
    assert dados["tipo_pericia"] == "A PEDIDO"

    # Regra estrita: doenca_motivo NÃO deve ser preenchida com CID para periciado titular
    assert dados.get("doenca_motivo") == ""


def test_first_page_only_extraction_in_endpoints():
    # 1. api_esisla_parse_pdf deve ler estritamente a 1ª página
    parse_pdf_block = APP[APP.index('def api_esisla_parse_pdf():'):APP.index('if not raw_text and not file_bytes:')]
    assert 'reader.pages[0].extract_text()' in parse_pdf_block
    assert 'for page in reader.pages:' not in parse_pdf_block

    # 2. api_esisla_vincular_agenda_batch deve ler estritamente a 1ª página
    batch_idx = APP.index('def api_esisla_vincular_agenda_batch():')
    batch_end = APP.index('dados = parse_esisla_text(raw_text) if raw_text else {}', batch_idx)
    batch_block = APP[batch_idx:batch_end]
    assert 'reader.pages[0].extract_text()' in batch_block
    assert 'for p in reader.pages:' not in batch_block


def test_attendance_clean_disease_motive_field():
    # 1. Em aplicarDadosEsisla, doencaMotivo não é preenchido com CID para periciado titular
    aplica_block = ATTENDANCE[ATTENDANCE.index('function aplicarDadosEsisla(dados)'):ATTENDANCE.index('window.aplicarDadosEsisla = aplicarDadosEsisla;')]
    assert 'isAcomp && dados.doenca_motivo' in aplica_block

    # 2. Em selectAgilCID, não há mais injeção do rótulo do CID em doencaMotivo
    agil_cid_block = ATTENDANCE[ATTENDANCE.index('function selectAgilCID(code)'):ATTENDANCE.index('function findCID(code)')]
    assert 'state.aux.doencaMotivo = rotulo;' not in agil_cid_block
    assert 'state.doencaMotivo = rotulo;' not in agil_cid_block
