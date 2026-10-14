from __future__ import annotations

from .atendimentos import bp_atendimentos
from .ai import (
    bp_ai,
    RefinarFichaEsislaResult,
    AudioTranscricaoAtendimentoResult,
    DadosExtraidosAudio,
    JustificationResult,
    EsislaResult,
    DocumentSuggestion,
    QuesitoSuggestion,
    FillSuggestionFields,
    FillSuggestionResult,
    generate_justificativa_stream
)
from .agendas import bp_agendas
from .admin import bp_admin
from .esisla import bp_esisla

__all__ = [
    "bp_atendimentos",
    "bp_ai",
    "bp_agendas",
    "bp_admin",
    "bp_esisla",
    "RefinarFichaEsislaResult",
    "AudioTranscricaoAtendimentoResult",
    "DadosExtraidosAudio",
    "JustificationResult",
    "EsislaResult",
    "DocumentSuggestion",
    "QuesitoSuggestion",
    "FillSuggestionFields",
    "FillSuggestionResult",
    "generate_justificativa_stream"
]
