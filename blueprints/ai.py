from __future__ import annotations

import json
import logging
from typing import Any, Generator, Literal
from flask import Blueprint, Response, jsonify, request
from pydantic import BaseModel, ConfigDict, Field

logger = logging.getLogger("ambiental.ai")

bp_ai = Blueprint("bp_ai", __name__)


# ==============================================================================
# SCHEMAS PYDANTIC ESTRITOS PARA O MOTOR CLÍNICO GEMINI
# ==============================================================================

class RefinarFichaEsislaResult(BaseModel):
    model_config = ConfigDict(extra="ignore")
    ficha_otimizada: str = Field(
        ...,
        description="Texto completo da ficha pericial e-SISLA técnica, formal, estruturada com quebras de linha duplas entre cada seção oficial, sem CAPSLOCK e sem agrupar em parágrafo único contínuo."
    )


class DadosExtraidosAudio(BaseModel):
    model_config = ConfigDict(extra="ignore")
    queixa_duracao: str = Field(description="Queixa principal e tempo de evolução")
    antecedentes: str = Field(description="Histórico patológico pregresso e comorbidades")
    exame_fisico: str = Field(description="Achados semiológicos observados")
    parecer: str = Field(description="'FAVORÁVEL', 'CONTRÁRIO' ou 'NÃO INFORMADO'")
    dias: int = Field(description="Dias concedidos ou sugeridos")
    cid: str = Field(description="Código CID-10 estimado ou citado")


class AudioTranscricaoAtendimentoResult(BaseModel):
    model_config = ConfigDict(extra="ignore")
    transcricao: str = Field(description="Texto completo e literal da fala transcrita")
    dados_extraidos: DadosExtraidosAudio


class JustificationResult(BaseModel):
    model_config = ConfigDict(extra="ignore")
    justificativa: str = Field(..., description="Fundamentação técnico-pericial no padrão DPME")


class EsislaResult(BaseModel):
    model_config = ConfigDict(extra="ignore")
    ficha_esisla: str = Field(..., description="Ficha técnica pericial completa formatada para o e-SISLA")


class DocumentSuggestion(BaseModel):
    model_config = ConfigDict(extra="ignore")
    tipo: str = Field(default="", description="Tipo de documento ou exame")
    data: str = Field(default="", description="Data do documento (DD/MM/AAAA ou YYYY-MM-DD)")
    resultado: str = Field(default="", description="Conclusão ou achados do documento")


class QuesitoSuggestion(BaseModel):
    model_config = ConfigDict(extra="ignore")
    numero: int = Field(..., description="Número do quesito oficial (1, 2 ou 3)")
    resposta: Literal["Sim", "Não", ""] = Field(..., description="Resposta ao quesito")
    justificativa: str = Field(default="", description="Fundamentação da resposta ao quesito")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    evidence: list[str] = Field(default_factory=list)
    requires_human_review: bool = Field(default=False)


class FillSuggestionFields(BaseModel):
    model_config = ConfigDict(extra="ignore")
    queixa_e_duracao: str = Field(default="")
    antecedentes_morbidos: str = Field(default="")
    exame_fisico_mental: str = Field(default="")
    alteracoes_clinicas_exames: str = Field(default="")
    limitacoes_fisicas_mentais: str = Field(default="")
    justificativa_parecer_final: str = Field(default="")
    atestado_relatorio_exames: list[DocumentSuggestion] = Field(default_factory=list)


class FillSuggestionResult(BaseModel):
    model_config = ConfigDict(extra="ignore")
    sugestoes_preenchimento: FillSuggestionFields
    quesitos_sugeridos: list[QuesitoSuggestion] = Field(default_factory=list)
    inconsistencias: list[str] = Field(default_factory=list)
    informacoes_ausentes: list[str] = Field(default_factory=list)
    nivel_atencao: Literal["baixo", "medio", "alto"] = Field(default="baixo")


# ==============================================================================
# MOTOR DE STREAMING EM TEMPO REAL (SERVER-SENT EVENTS - SSE)
# ==============================================================================

def generate_justificativa_stream(
    client: Any,
    models: list[str],
    instruction: str,
    system_instruction: str
) -> Generator[str, None, None]:
    """
    Consome o gerador de streaming oficial do SDK google-genai
    (client.models.generate_content_stream) e transmite chunks via SSE.
    """
    from google.genai import types

    success = False
    last_err: Exception | None = None

    for model_name in models:
        try:
            logger.info("Iniciando streaming Gemini com modelo: %s", model_name)
            stream = client.models.generate_content_stream(
                model=model_name,
                contents=[instruction],
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=0.2,
                ),
            )
            for chunk in stream:
                text_piece = getattr(chunk, "text", "") or ""
                if text_piece:
                    data = json.dumps({"text": text_piece, "done": False}, ensure_ascii=False)
                    yield f"data: {data}\n\n"

            success = True
            yield f"data: {json.dumps({'done': True, 'model': model_name}, ensure_ascii=False)}\n\n"
            break
        except Exception as err:
            logger.warning("Falha no streaming com modelo %s: %s", model_name, err)
            last_err = err
            continue

    if not success:
        err_msg = f"Falha ao gerar streaming da justificativa médica: {str(last_err)}"
        yield f"data: {json.dumps({'error': err_msg, 'done': True}, ensure_ascii=False)}\n\n"


@bp_ai.post("/api/ai/justificativa/stream")
def api_ai_justificativa_stream_route():
    """
    Endpoint de Streaming em tempo real para Justificativas Periciais.
    Retorna chunks de texto via Server-Sent Events (SSE).
    """
    import app as main_app

    try:
        raw = main_app._load_authoritative_ai_payload(main_app._json_body())
        payload = main_app._minimal_ai_context(raw)
        cadastro_id = main_app._get_cadastro_id(payload)

        with main_app._cadastro_ai_lock(cadastro_id, "/api/ai/justificativa/stream"):
            instruction = main_app._task_instruction("justificativa", payload)
            endpoint = "/api/ai/justificativa/stream"
            allowed, retry_after = main_app._rate_limit(endpoint)
            if not allowed:
                raise main_app.AIRateLimitError(retry_after)

            client = main_app._client()
            models = [main_app.GEMINI_MODEL] + main_app.GEMINI_FALLBACK_MODELS

            stream_gen = generate_justificativa_stream(
                client=client,
                models=models,
                instruction=instruction,
                system_instruction=main_app.SYSTEM_PROMPT
            )

            return Response(
                stream_gen,
                mimetype="text/event-stream",
                headers={
                    "Cache-Control": "no-cache, no-transform",
                    "X-Accel-Buffering": "no",
                    "Connection": "keep-alive",
                }
            )
    except Exception as exc:
        if isinstance(exc, ValueError):
            return main_app._error("VALIDATION_ERROR", str(exc), False, 400)
        return main_app._provider_error(exc)
