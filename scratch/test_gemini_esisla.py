import os, sys
sys.path.insert(0, ".")
from pydantic import BaseModel, ConfigDict
from google.genai import types
from app import _client, GEMINI_MODEL

PDF_PATH = r"C:\Users\maykon.moraes\.gemini\antigravity\brain\489024fa-3d24-468a-adee-a576b3498293\.user_uploaded\media_1791223263444.pdf"

class EsislaImportResult(BaseModel):
    model_config = ConfigDict(extra="ignore")
    protocolo: str
    nome_paciente: str
    cpf_paciente: str
    rg_paciente: str
    data_nascimento: str
    idade: str
    sexo: str
    ni: str
    orgao: str
    unidade: str
    municipio: str
    regime_juridico: str
    cargo: str
    situacao: str
    readaptado: str
    possui_nexo: str
    ultima_licenca_dias: str
    ultima_licenca_inicio: str
    ultima_licenca_fim: str
    motivo_pericia: str
    crm_assistente: str
    nome_assistente: str
    cid: str
    dias_solicitados: str
    data_documento: str

client = _client()
with open(PDF_PATH, "rb") as f:
    pdf_bytes = f.read()

prompt = (
    "Extraia todos os dados do formulário Consulta Perícia Licença do e-SISLA / DPME em anexo. "
    "Preencha rigorosamente conforme os campos do documento. "
    "Se o campo Readaptação tiver o radio 'Não' selecionado, coloque 'Não'. "
    "Se o campo Sexo tiver 'Masculino' selecionado, coloque 'Masculino'."
)

config = types.GenerateContentConfig(
    system_instruction="Você é um assistente pericial especializado na extração exata de documentos e-SISLA.",
    temperature=0.0,
    response_mime_type="application/json",
    response_schema=EsislaImportResult,
)

response = client.models.generate_content(
    model=GEMINI_MODEL,
    contents=[
        types.Part.from_bytes(data=pdf_bytes, mime_type="application/pdf"),
        prompt,
    ],
    config=config,
)

print(response.text)
