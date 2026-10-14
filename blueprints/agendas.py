from __future__ import annotations

import logging
from flask import Blueprint, jsonify, request

logger = logging.getLogger("ambiental.agendas")

bp_agendas = Blueprint("bp_agendas", __name__)

@bp_agendas.get("/api/v2/agendas/health")
def api_agendas_health():
    """Health check do módulo pericial de agendas."""
    return jsonify({"status": "ok", "module": "agendas", "version": "v2"}), 200
