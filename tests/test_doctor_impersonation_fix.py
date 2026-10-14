from pathlib import Path
import pytest
from app import app, get_db

ROOT = Path(__file__).resolve().parent.parent
APP_PY = (ROOT / "app.py").read_text(encoding="utf-8")
GESTAO_MEDICOS_HTML = (ROOT / "gestao_medicos.html").read_text(encoding="utf-8")
API_JS = (ROOT / "api.js").read_text(encoding="utf-8")

def test_backend_effective_user_and_impersonation_contract():
    # 1. Resolução resiliente de médico por ID ou CRM
    assert "def _get_effective_user():" in APP_PY
    assert "WHERE (id::text = %s OR crm = %s)" in APP_PY
    assert "(perfil ILIKE 'm%%dico' OR perfil = 'Médico' OR perfil = 'Medico')" in APP_PY
    assert 'getattr(request, "user_role", None) == "Administrador"' in APP_PY

    # 2. api_dashboard usa effective_user para escopo de estatísticas
    assert "eff = _get_effective_user()" in APP_PY
    assert 'stat_key = f"{effective_role}:{effective_user_id if is_doctor else \'all\'}"' in APP_PY
    assert 'stat_where = " WHERE usuario_id=%s" if is_doctor else ""' in APP_PY
    assert "stat_params = [effective_user_id] if is_doctor else []" in APP_PY

    # 3. api.js permite parâmetros em medico.dashboard
    assert "dashboard: (params = {}) => {" in API_JS
    assert "URLSearchParams(params)" in API_JS


def test_frontend_impersonation_identity_and_params():
    # 1. O frontend adota imediatamente o nome e CRM salvos em sessionStorage
    assert "ambiental.impersonate_medico_nome" in GESTAO_MEDICOS_HTML
    assert "ambiental.impersonate_medico_crm" in GESTAO_MEDICOS_HTML
    assert "cachedNome" in GESTAO_MEDICOS_HTML
    assert "cachedCrm" in GESTAO_MEDICOS_HTML

    # 2. Chama APIs do portal médico passando medico_id explicitamente
    assert "AmbientalAPI.medico.dashboard(dashParams)" in GESTAO_MEDICOS_HTML
    assert "AmbientalAPI.medico.atendimentos(atdParams)" in GESTAO_MEDICOS_HTML
    assert "medico_id: impId" in GESTAO_MEDICOS_HTML

    # 3. Confirma remoção total do PWA em gestao_medicos.html
    assert "/pwa.js" not in GESTAO_MEDICOS_HTML
    assert "/manifest.json" not in GESTAO_MEDICOS_HTML
