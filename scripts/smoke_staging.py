"""Smoke test opcional contra um staging real.

Uso:
  STAGING_BASE_URL=https://staging.exemplo.com python scripts/smoke_staging.py
  STAGING_BASE_URL=... STAGING_BEARER_TOKEN=... python scripts/smoke_staging.py
"""
from __future__ import annotations

import os
import sys
import requests

BASE = os.getenv("STAGING_BASE_URL", "").rstrip("/")
TOKEN = os.getenv("STAGING_BEARER_TOKEN", "").strip()
TIMEOUT = float(os.getenv("STAGING_TIMEOUT", "10"))

if not BASE:
    print("STAGING_BASE_URL não configurada; smoke test não executado.")
    raise SystemExit(0)


def check(method: str, path: str, expected: set[int], **kwargs):
    r = requests.request(method, f"{BASE}{path}", timeout=TIMEOUT, **kwargs)
    print(f"{method} {path}: HTTP {r.status_code}")
    if r.status_code not in expected:
        print(r.text[:500])
        raise SystemExit(1)
    return r

check("GET", "/health", {200})
ready = check("GET", "/ready", {200, 503})
config = check("GET", "/api/auth/config", {200, 503})
unauth = check("GET", "/api/auth/me", {401})

if TOKEN:
    headers = {"Authorization": f"Bearer {TOKEN}"}
    me = check("GET", "/api/auth/me", {200}, headers=headers)
    body = me.json()
    assert body.get("success") is True
    profile = body.get("data") or {}
    assert profile.get("perfil") in {"Administrador", "Médico", "Coordenador", "Revisor", "Gestor", "Consulta"}
    check("GET", "/api/atendimentos?page=1&page_size=1", {200}, headers=headers)
    if profile.get("perfil") in {"Administrador", "Médico"}:
        check("GET", "/api/medico/dashboard", {200}, headers=headers)

print("Smoke staging concluído com sucesso.")
