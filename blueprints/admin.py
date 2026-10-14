from __future__ import annotations

import logging
from flask import Blueprint, jsonify, request

logger = logging.getLogger("ambiental.admin")

bp_admin = Blueprint("bp_admin", __name__)

@bp_admin.get("/api/v2/admin/health")
def api_admin_health():
    """Health check do módulo administrativo."""
    return jsonify({"status": "ok", "module": "admin", "version": "v2"}), 200
