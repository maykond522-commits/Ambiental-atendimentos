"""Small, privacy-conscious observability layer for Flask."""
from __future__ import annotations

import logging
import time
from collections import Counter
from contextvars import ContextVar
from typing import Any
from flask import g, request
from uuid import uuid4

_request_id: ContextVar[str] = ContextVar("request_id", default="-")
_metrics = Counter()


def current_request_id() -> str:
    return _request_id.get()


def install(app: Any) -> None:
    logger = logging.getLogger("ambiental")
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

    @app.before_request
    def _obs_before() -> None:
        rid = str(app.config.get("REQUEST_ID_HEADER", "X-Request-ID"))
        incoming = str(request.headers.get(rid) or "").strip()
        if len(incoming) > 100 or not incoming.replace("-", "").replace("_", "").isalnum():
            incoming = ""
        token = _request_id.set(incoming or uuid4().hex)
        g._ambiental_request_id_token = token
        g._ambiental_request_started = time.perf_counter()

    @app.after_request
    def _obs_after(response: Any) -> Any:
        rid = current_request_id()
        response.headers[app.config.get("REQUEST_ID_HEADER", "X-Request-ID")] = rid
        started = getattr(g, "_ambiental_request_started", None)
        elapsed_ms = int((time.perf_counter() - started) * 1000) if started else -1
        key = f"{request.method} {request.path} {response.status_code // 100}xx"
        _metrics[key] += 1
        # Avoid query strings and request bodies so medical data cannot enter logs.
        logger.info("request_id=%s method=%s path=%s status=%s duration_ms=%s", rid, request.method, request.path, response.status_code, elapsed_ms)
        return response

    @app.teardown_request
    def _obs_teardown(_exc: BaseException | None) -> None:
        token = getattr(g, "_ambiental_request_id_token", None)
        if token is not None:
            _request_id.reset(token)


def metrics_snapshot() -> dict[str, int]:
    return dict(_metrics)
