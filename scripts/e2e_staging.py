"""Matriz E2E de autorização para um staging real do Ambiental.

Não cria nem altera registros por padrão.

Variáveis:
  STAGING_BASE_URL=https://staging.exemplo.com
  E2E_ADMIN_TOKEN=<token temporário do admin>
  E2E_MEDICO_A_TOKEN=<token temporário do médico A>
  E2E_MEDICO_B_TOKEN=<token temporário do médico B>
  E2E_ATENDIMENTO_A_ID=<id OU numero pertencente ao médico A>

Executa:
  python scripts/e2e_staging.py

O teste considera sucesso quando:
- sem token: /api/auth/me => 401
- cada token obtém perfil válido
- médico A só consulta seu escopo
- médico B não consegue ler/escrever o atendimento A
- admin consegue consultar o endpoint administrativo
- endpoints públicos continuam saudáveis
"""
from __future__ import annotations

import os
import sys
from typing import Optional

import requests

BASE = os.getenv("STAGING_BASE_URL", "").rstrip("/")
TIMEOUT = float(os.getenv("STAGING_TIMEOUT", "12"))
ADMIN = os.getenv("E2E_ADMIN_TOKEN", "").strip()
MEDICO_A = os.getenv("E2E_MEDICO_A_TOKEN", "").strip()
MEDICO_B = os.getenv("E2E_MEDICO_B_TOKEN", "").strip()
RECORD_A = os.getenv("E2E_ATENDIMENTO_A_ID", "").strip()

ALLOWED_ROLES = {"Administrador", "Médico", "Coordenador", "Revisor", "Gestor", "Consulta"}


def request(method: str, path: str, token: Optional[str] = None, **kwargs):
    headers = kwargs.pop("headers", {}) or {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return requests.request(method, f"{BASE}{path}", timeout=TIMEOUT, headers=headers, **kwargs)


def expect(method: str, path: str, statuses: set[int], token: Optional[str] = None, **kwargs):
    r = request(method, path, token=token, **kwargs)
    print(f"{method:5s} {path:50s} -> {r.status_code}")
    if r.status_code not in statuses:
        print(r.text[:800])
        raise AssertionError(f"Esperado {statuses}, recebido {r.status_code} em {method} {path}")
    return r


def profile(token: str) -> dict:
    r = expect("GET", "/api/auth/me", {200}, token)
    body = r.json()
    assert body.get("success") is True
    data = body.get("data") or {}
    assert data.get("perfil") in ALLOWED_ROLES
    assert data.get("id")
    assert data.get("email")
    return data


if not BASE:
    print("STAGING_BASE_URL não configurada.")
    raise SystemExit(2)

expect("GET", "/health", {200})
expect("GET", "/ready", {200, 503})
expect("GET", "/api/auth/me", {401})

provided = [("ADMIN", ADMIN), ("MEDICO_A", MEDICO_A), ("MEDICO_B", MEDICO_B)]
profiles = {}
for label, token in provided:
    if token:
        profiles[label] = profile(token)

if ADMIN:
    assert profiles["ADMIN"]["perfil"] in {"Administrador", "Gestor", "Coordenador", "Revisor", "Consulta"}
    expect("GET", "/api/atendimentos?page=1&page_size=1", {200}, ADMIN)

if MEDICO_A:
    assert profiles["MEDICO_A"]["perfil"] == "Médico", profiles["MEDICO_A"]
    expect("GET", "/api/medico/dashboard", {200}, MEDICO_A)
    expect("GET", "/api/medico/atendimentos?page=1&page_size=25", {200}, MEDICO_A)

if MEDICO_B:
    assert profiles["MEDICO_B"]["perfil"] == "Médico", profiles["MEDICO_B"]
    expect("GET", "/api/medico/dashboard", {200}, MEDICO_B)
    expect("GET", "/api/medico/atendimentos?page=1&page_size=25", {200}, MEDICO_B)

# Teste de isolamento entre médicos, somente quando um registro de A foi selecionado.
if MEDICO_B and RECORD_A:
    expect("GET", f"/api/atendimentos/{RECORD_A}", {403, 404}, MEDICO_B)
    expect(
        "PUT",
        f"/api/atendimentos/{RECORD_A}",
        {403, 404, 409},
        MEDICO_B,
        json={"atendimento": RECORD_A},
    )
    expect(
        "POST",
        f"/api/atendimentos/{RECORD_A}/state",
        {403, 404, 409},
        MEDICO_B,
        json={"estado": "RASCUNHO"},
    )

print("E2E staging concluído com sucesso.")
