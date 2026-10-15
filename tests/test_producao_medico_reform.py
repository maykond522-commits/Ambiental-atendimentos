from pathlib import Path
import pytest
from app import _parse_doctor_name_crm, app

ROOT = Path(__file__).resolve().parent.parent
GESTAO_HTML = (ROOT / "gestao_atendimentos.html").read_text(encoding="utf-8")


def test_parse_doctor_name_crm_normalization():
    # 1. Com CRM e hífen
    name, crm = _parse_doctor_name_crm("PATRICIA NALIN DE LUCENA - CRM: 145669")
    assert name == "PATRICIA NALIN DE LUCENA"
    assert crm == "145669"

    # 2. Apenas nome
    name, crm = _parse_doctor_name_crm("WANIA SANCHES PICASSO")
    assert name == "WANIA SANCHES PICASSO"
    assert crm == ""

    # 3. Com formato CRM alternativo
    name, crm = _parse_doctor_name_crm("MARIA DAS GRAÇAS - CRM: 148311")
    assert name == "MARIA DAS GRAÇAS"
    assert crm == "148311"

    # 4. Caso vazio ou não informado
    name, crm = _parse_doctor_name_crm("Não identificado")
    assert name == "Não identificado"
    assert crm == ""

    name, crm = _parse_doctor_name_crm("")
    assert name == "Não identificado"
    assert crm == ""


def test_gestao_atendimentos_producao_por_medico_elements():
    # 1. Estrutura executiva do view-medicos
    assert 'id="view-medicos"' in GESTAO_HTML
    assert "doctor-kpi-strip" in GESTAO_HTML
    assert 'id="docKpiTotalMedicos"' in GESTAO_HTML
    assert 'id="docKpiTotalAtd"' in GESTAO_HTML
    assert 'id="docKpiTotalFin"' in GESTAO_HTML
    assert 'id="docKpiTotalFav"' in GESTAO_HTML
    assert 'id="docKpiTotalContra"' in GESTAO_HTML

    # 2. Grade de cards e alternância com tabela
    assert 'id="doctorCardsGrid"' in GESTAO_HTML
    assert 'id="doctorTableWrap"' in GESTAO_HTML
    assert "btn-ver-atendimentos" in GESTAO_HTML
    assert "setDocViewMode" in GESTAO_HTML

    # 3. Modal personalizado para ver atendimentos
    assert 'id="modalAtendimentosMedico"' in GESTAO_HTML
    assert 'id="modalDocNome"' in GESTAO_HTML
    assert 'id="modalDocCrm"' in GESTAO_HTML
    assert 'id="modalDocTotalPill"' in GESTAO_HTML
    assert 'id="modalDocHeroCount"' in GESTAO_HTML
    assert 'id="modalDocDataEspecifica"' in GESTAO_HTML
    assert "abrirModalAtendimentosMedico" in GESTAO_HTML
    assert "executarFiltroAtendimentosMedico" in GESTAO_HTML
