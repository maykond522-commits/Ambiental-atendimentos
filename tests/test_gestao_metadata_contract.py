from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / 'app.py'
GESTAO = ROOT / 'gestao_atendimentos.html'


def test_list_endpoint_selects_payload_json_for_metadata_extraction():
    text = APP.read_text(encoding='utf-8')
    marker = 'SELECT id, numero, status, medico, cid, unidade, completude,'
    start = text.index(marker)
    end = text.index('FROM atendimentos', start)
    block = text[start:end]
    assert 'payload_json' in block
    assert 'paciente_nome' in block and 'paciente_cpf' in block


def test_gestao_has_staged_loaders_for_detail_and_history():
    text = GESTAO.read_text(encoding='utf-8')
    assert 'detail-open-skeleton' in text
    assert 'Carregando ficha' in text
    assert 'Carregando histórico' in text
