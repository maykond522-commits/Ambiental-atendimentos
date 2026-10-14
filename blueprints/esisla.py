from __future__ import annotations

import logging
import re
from datetime import datetime, timezone
from flask import Blueprint, jsonify, request

logger = logging.getLogger("ambiental.esisla")

bp_esisla = Blueprint("bp_esisla", __name__)


@bp_esisla.get("/api/v2/esisla/health")
def api_esisla_health():
    """Health check do motor de integração e-SISLA."""
    return jsonify({"status": "ok", "module": "esisla", "version": "v2"}), 200


@bp_esisla.post("/api/esisla/importar-agenda")
def api_esisla_importar_agenda():
    """
    Importação direta 1-clique da agenda de perícias extraída da tela do e-SISLA pela extensão.
    Permite ao médico perito importar sua grade diária diretamente para o sistema Ambiental.
    """
    import app as main_app

    # Validação de autenticação
    user_id = str(getattr(request, "user_id", "") or "").strip()
    if not user_id:
        return main_app._error("AUTH_ERROR", "Sessão inválida ou expirada.", False, 401)

    user_role = str(getattr(request, "user_role", "") or "").strip()
    effective_user = main_app._get_effective_user()
    effective_id = effective_user.get("id") if effective_user else user_id

    try:
        body = main_app._json_body()
        data_str = str(body.get("data") or "").strip()
        if not data_str:
            data_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        elif not re.match(r"^\d{4}-\d{2}-\d{2}$", data_str):
            m = re.match(r"^(\d{2})/(\d{2})/(\d{4})$", data_str)
            if m:
                data_str = f"{m.group(3)}-{m.group(2)}-{m.group(1)}"
            else:
                return main_app._error("VALIDATION_ERROR", "Data inválida. Use AAAA-MM-DD ou DD/MM/AAAA.", False, 400)

        itens = body.get("itens")
        if not isinstance(itens, list) or len(itens) == 0:
            return main_app._error("VALIDATION_ERROR", "Nenhum agendamento foi encontrado para importação.", False, 400)

        medico_id = str(body.get("medico_id") or "").strip()
        if user_role == "Administrador" and medico_id:
            target_medico_id = medico_id
        else:
            target_medico_id = effective_id

        db = main_app.get_db()
        cur = db.cursor()
        now = main_app._utc_now()

        inseridos = 0
        for it in itens:
            if not isinstance(it, dict):
                continue
            nome = str(it.get("servidor") or it.get("nome_periciado") or it.get("nome") or "").strip()
            if not nome:
                continue
            hora = str(it.get("horario") or it.get("hora") or "08:00").strip()[:10]
            protocolo = str(it.get("protocolo") or "").strip()[:60]
            cpf = str(it.get("cpf") or "").strip()[:30]
            rg = str(it.get("rg") or "").strip()[:30]
            tipo = str(it.get("tipo") or "Perícia Médica e-SISLA").strip()[:60]

            # Verifica duplicidade
            cur.execute("""
                SELECT id FROM agendas
                WHERE medico_id = %s AND data = %s AND (
                    (protocolo <> '' AND protocolo = %s) OR
                    (LOWER(nome_periciado) = LOWER(%s) AND hora = %s)
                )
            """, (target_medico_id, data_str, protocolo, nome, hora))
            existing = cur.fetchone()

            if not existing:
                cur.execute("""
                    INSERT INTO agendas (
                        medico_id, data, hora, nome_periciado, protocolo, ni, tipo, status, criado_em, atualizado_em
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, 'Agendado', %s, %s
                    )
                """, (target_medico_id, data_str, hora, nome, protocolo, cpf or rg, tipo, now, now))
                inseridos += 1

        db.commit()
        cur.close()

        return main_app._ok({
            "mensagem": f"{inseridos} agendamentos importados com sucesso para a data {data_str}.",
            "data": data_str,
            "total_recebidos": len(itens),
            "inseridos": inseridos,
            "medico_id": target_medico_id
        })

    except Exception as exc:
        logger.exception("Erro ao importar agenda do e-SISLA: %s", exc)
        return main_app._error("IMPORT_ERROR", f"Falha ao importar agenda do e-SISLA: {str(exc)}", False, 500)
