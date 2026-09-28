# Isolamento de atendimentos por médico

O projeto já aplica a regra no backend: quando o perfil é `Médico`, as consultas de `atendimentos` recebem `usuario_id = request.user_id` e endpoints de detalhe/edição verificam o proprietário.

Para proteger também acessos diretos pelo Supabase, execute **uma vez** o arquivo `RLS_PRODUCAO.sql` no SQL Editor do projeto Supabase.

## Regra

- Médico: somente registros em `atendimentos.usuario_id = auth.uid()::text`.
- Administrador: acesso completo aos atendimentos.
- Gestor/Coordenador/Revisor/Consulta: mantêm o escopo de leitura/gestão previsto pelo sistema.
- `historico_atendimento`, `documentos`, `quesitos`, `relatorios` e `logs_ia` acompanham o mesmo proprietário do atendimento.

A coluna `usuarios.id` e `atendimentos.usuario_id` são `text`, por isso a comparação com o Supabase Auth usa `auth.uid()::text`.
