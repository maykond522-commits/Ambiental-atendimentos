#!/usr/bin/env python3
"""Provisiona uma conta de Médico para testes no Supabase + perfil local.

Uso:
  SUPABASE_SERVICE_ROLE_KEY='...' python scripts/criar_medico_teste.py

Opcionalmente, sobrescreva TEST_MEDICO_EMAIL, TEST_MEDICO_PASSWORD,
TEST_MEDICO_NOME e TEST_MEDICO_CRM no ambiente.
"""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

import psycopg2

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_dotenv_simple(path: str) -> None:
    if not os.path.exists(path):
        return
    with open(path, "r", encoding="utf-8") as fh:
        for raw in fh:
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            os.environ.setdefault(key, value)


load_dotenv_simple(os.path.join(BASE_DIR, ".env"))

SUPABASE_URL = os.getenv("SUPABASE_URL", "").rstrip("/")
SERVICE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip()
DATABASE_URL = os.getenv("DATABASE_URL", "").strip()
EMAIL = os.getenv("TEST_MEDICO_EMAIL", "medico.teste@ambientalqvt.com.br").strip().lower()
PASSWORD = os.getenv("TEST_MEDICO_PASSWORD", "TesteMedico#2026")
NOME = os.getenv("TEST_MEDICO_NOME", "Dr. Médico Teste").strip()
CRM = os.getenv("TEST_MEDICO_CRM", "CRM-TESTE-2026").strip()


def api(method: str, path: str, payload=None):
    if not SUPABASE_URL or not SERVICE_KEY:
        raise RuntimeError("Defina SUPABASE_URL e SUPABASE_SERVICE_ROLE_KEY no ambiente/.env.")
    body = None if payload is None else json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"{SUPABASE_URL}{path}",
        data=body,
        method=method,
        headers={
            "Authorization": f"Bearer {SERVICE_KEY}",
            "apikey": SERVICE_KEY,
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            text = resp.read().decode("utf-8")
            return resp.status, (json.loads(text) if text else {})
    except urllib.error.HTTPError as exc:
        text = exc.read().decode("utf-8", errors="replace")
        try:
            detail = json.loads(text)
        except json.JSONDecodeError:
            detail = {"message": text}
        return exc.code, detail


def find_auth_user() -> dict | None:
    page = 1
    while page <= 20:
        qs = urllib.parse.urlencode({"page": page, "per_page": 1000})
        status, data = api("GET", f"/auth/v1/admin/users?{qs}")
        if status != 200:
            raise RuntimeError(f"Não foi possível consultar usuários do Auth ({status}): {data}")
        users = data.get("users") if isinstance(data, dict) else None
        users = users if isinstance(users, list) else []
        for user in users:
            if str(user.get("email") or "").strip().lower() == EMAIL:
                return user
        if len(users) < 1000:
            return None
        page += 1
    raise RuntimeError("Não foi possível localizar o usuário após várias páginas do Auth.")


def provision_auth() -> str:
    status, data = api(
        "POST",
        "/auth/v1/admin/users",
        {
            "email": EMAIL,
            "password": PASSWORD,
            "email_confirm": True,
            "user_metadata": {"nome": NOME},
        },
    )
    if status in (200, 201):
        user_id = str(data.get("id") or data.get("user", {}).get("id") or "")
        if not user_id:
            raise RuntimeError(f"Auth criou a conta, mas não retornou o id: {data}")
        return user_id
    if status not in (400, 422):
        raise RuntimeError(f"Falha ao criar usuário no Supabase Auth ({status}): {data}")

    existing = find_auth_user()
    if not existing:
        raise RuntimeError(f"O Auth recusou a criação ({status}), mas não encontrei a conta existente: {data}")
    user_id = str(existing.get("id") or "")
    if not user_id:
        raise RuntimeError(f"Conta existente sem id: {existing}")
    status, data = api(
        "PUT",
        f"/auth/v1/admin/users/{urllib.parse.quote(user_id, safe='')}",
        {
            "password": PASSWORD,
            "email_confirm": True,
            "user_metadata": {"nome": NOME},
        },
    )
    if status not in (200, 204):
        raise RuntimeError(f"Não foi possível atualizar a senha do usuário existente ({status}): {data}")
    return user_id


def provision_profile(user_id: str) -> None:
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL não configurada; não foi possível criar o perfil em usuarios.")
    conn = psycopg2.connect(DATABASE_URL)
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO usuarios (id, nome, perfil, ativo, criado_em, crm)
                VALUES (%s, %s, 'Médico', 1, NOW(), %s)
                ON CONFLICT (id) DO UPDATE SET
                    nome = EXCLUDED.nome,
                    perfil = 'Médico',
                    ativo = 1,
                    crm = EXCLUDED.crm
                """,
                (user_id, NOME, CRM),
            )
        conn.commit()
    finally:
        conn.close()


def main() -> int:
    if not SERVICE_KEY:
        print("ERRO: SUPABASE_SERVICE_ROLE_KEY não configurada.", file=sys.stderr)
        return 2
    try:
        user_id = provision_auth()
        provision_profile(user_id)
    except Exception as exc:
        print(f"ERRO: {exc}", file=sys.stderr)
        return 1

    print("MÉDICO DE TESTE CONFIGURADO")
    print(f"E-mail: {EMAIL}")
    print(f"Senha:  {PASSWORD}")
    print(f"Nome:   {NOME}")
    print(f"CRM:    {CRM}")
    print(f"Auth ID: {user_id}")
    print("Perfil: Médico")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
