-- Migração: materializa identificação do paciente para busca rápida.
-- Execute no SQL Editor do Supabase uma única vez. É idempotente.

ALTER TABLE public.atendimentos
  ADD COLUMN IF NOT EXISTS paciente_nome TEXT,
  ADD COLUMN IF NOT EXISTS paciente_cpf TEXT;

CREATE INDEX IF NOT EXISTS idx_atd_paciente_nome_lower
  ON public.atendimentos (LOWER(paciente_nome));

CREATE INDEX IF NOT EXISTS idx_atd_paciente_cpf
  ON public.atendimentos (paciente_cpf);

UPDATE public.atendimentos
SET paciente_nome = NULLIF(BTRIM(COALESCE(payload_json->'aux'->>'nomePaciente', payload_json->>'nomePaciente', '')), ''),
    paciente_cpf = NULLIF(REGEXP_REPLACE(COALESCE(payload_json->'aux'->>'cpfPaciente', payload_json->>'cpfPaciente', ''), '[^0-9]', '', 'g'), '')
WHERE paciente_nome IS NULL OR paciente_cpf IS NULL;

-- Verificação opcional
SELECT id, numero, paciente_nome, paciente_cpf
FROM public.atendimentos
ORDER BY atualizado_em DESC
LIMIT 20;
