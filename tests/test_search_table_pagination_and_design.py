from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GESTAO_ATD = (ROOT / "gestao_atendimentos.html").read_text(encoding="utf-8")
GESTAO_MED = (ROOT / "gestao_medicos.html").read_text(encoding="utf-8")
GESTAO_ADM = (ROOT / "gestao-medicos-admin.html").read_text(encoding="utf-8")


def test_gestao_atendimentos_table_pagination_limit_40():
    """Garante que a tabela de busca de atendimentos possui limite estrito de 40 itens por página."""
    assert "searchPageSize = 40" in GESTAO_ATD
    assert "tablePaginationFooter" in GESTAO_ATD
    assert "changeSearchPage" in GESTAO_ATD
    assert "renderTablePage" in GESTAO_ATD
    assert "renderPaginationUI" in GESTAO_ATD
    assert "page-nav-btn" in GESTAO_ATD
    assert "page-num-btn" in GESTAO_ATD


def test_gestao_medicos_table_pagination_limit_40():
    """Garante que o portal do médico possui limite de 40 atendimentos por página e paginador elegante."""
    assert "pageSize = 40" in GESTAO_MED
    assert "doctorPageNumbers" in GESTAO_MED
    assert "updateDoctorPaginationUI" in GESTAO_MED
    assert "goToDoctorPage" in GESTAO_MED


def test_gestao_medicos_admin_table_pagination_limit_40():
    """Garante que a gestão administrativa de médicos possui paginação de 40 médicos por página."""
    assert "doctorPageSize = 40" in GESTAO_ADM
    assert "doctorPaginationFooter" in GESTAO_ADM
    assert "renderDoctorPaginationUI" in GESTAO_ADM
    assert "changeDoctorPage" in GESTAO_ADM


def test_buttons_and_design_tokens_aligned_with_brand():
    """Garante que os botões possuem gradientes corporativos e estilos modernos da Ambiental."""
    assert "#0284C7" in GESTAO_ATD or "var(--blue)" in GESTAO_ATD
    assert "btn-primary" in GESTAO_ATD
    assert "btn-esisla" in GESTAO_ATD
    assert "btn-danger" in GESTAO_ATD
    assert "page-nav-btn" in GESTAO_MED
    assert "page-num-btn" in GESTAO_ADM
