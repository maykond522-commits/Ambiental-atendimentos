"""Service layer for atendimento queries.

Keeps authorization-aware SQL construction out of Flask route handlers.
Never accepts a user id supplied by the browser as the security source.
"""
from __future__ import annotations

from typing import Any, Sequence
import re

MAX_PAGE_SIZE = 100
DEFAULT_PAGE_SIZE = 25


def pagination(args: Any) -> tuple[int, int, int]:
    try:
        page = max(1, int(args.get("page", "1")))
    except (TypeError, ValueError):
        page = 1
    try:
        page_size = min(MAX_PAGE_SIZE, max(1, int(args.get("page_size", args.get("limit", str(DEFAULT_PAGE_SIZE))))))
    except (TypeError, ValueError):
        page_size = DEFAULT_PAGE_SIZE
    return page, page_size, (page - 1) * page_size


def list_filters(args: Any, *, role: str, user_id: str) -> tuple[list[str], list[Any]]:
    clauses: list[str] = []
    params: list[Any] = []

    q = str(args.get("q", "")).strip().lower()
    status = str(args.get("status", "")).strip().upper()
    medico = str(args.get("medico", "")).strip()
    cid = str(args.get("cid", "")).strip()
    unidade = str(args.get("unidade", "")).strip()
    data_inicio = str(args.get("data_inicio", "")).strip()
    data_fim = str(args.get("data_fim", "")).strip()

    # Security boundary: the authenticated server identity defines ownership.
    if role == "Médico":
        clauses.append("usuario_id = %s")
        params.append(user_id)

    if q:
        like = f"%{q}%"
        cpf_q = re.sub(r"\D", "", q)
        clauses.append("(lower(numero) LIKE %s OR lower(medico) LIKE %s OR lower(paciente_nome) LIKE %s OR paciente_cpf LIKE %s OR lower(cid) LIKE %s OR lower(unidade) LIKE %s)")
        params.extend([like, like, like, f"%{cpf_q}%" if cpf_q else f"%{q}%", like, like])
    if status:
        clauses.append("status = %s")
        params.append(status)
    if medico:
        clauses.append("lower(medico) LIKE lower(%s)")
        params.append(f"%{medico}%")
    if cid:
        clauses.append("lower(cid) LIKE lower(%s)")
        params.append(f"%{cid}%")
    if unidade:
        clauses.append("lower(unidade) LIKE lower(%s)")
        params.append(f"%{unidade}%")
    if data_inicio:
        clauses.append("COALESCE(payload_json->'aux'->>'dataAtd', criado_em::text) >= %s")
        params.append(data_inicio)
    if data_fim:
        clauses.append("COALESCE(payload_json->'aux'->>'dataAtd', criado_em::text) <= %s")
        params.append(data_fim)

    return clauses, params


def build_where(clauses: Sequence[str]) -> str:
    return (" WHERE " + " AND ".join(clauses)) if clauses else ""
