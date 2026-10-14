from __future__ import annotations

import logging
from flask import Blueprint, jsonify, request

logger = logging.getLogger("ambiental.atendimentos")

bp_atendimentos = Blueprint("bp_atendimentos", __name__)

@bp_atendimentos.get("/api/v2/atendimentos/health")
def api_atendimentos_health():
    """Health check do módulo de atendimentos."""
    return jsonify({"status": "ok", "module": "atendimentos", "version": "v2"}), 200
