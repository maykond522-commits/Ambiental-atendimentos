-- RLS de produção: isolamento por médico + acesso administrativo.
-- A identidade vem do Supabase Auth (auth.uid()) e é comparada ao
-- usuarios.id, que neste projeto é armazenado como TEXT.

create or replace function public.app_role()
returns text
language sql
stable
security definer
set search_path = public
as $$
  select coalesce((select u.perfil from public.usuarios u where u.id = auth.uid()::text and u.ativo = 1), '');
$$;

revoke all on function public.app_role() from public;
grant execute on function public.app_role() to authenticated;

-- Tabelas sensíveis
alter table if exists public.usuarios enable row level security;
alter table if exists public.atendimentos enable row level security;
alter table if exists public.historico_atendimento enable row level security;
alter table if exists public.logs_ia enable row level security;
alter table if exists public.relatorios enable row level security;
alter table if exists public.configuracoes enable row level security;
alter table if exists public.cache_ia enable row level security;
alter table if exists public.documentos enable row level security;
alter table if exists public.quesitos enable row level security;
alter table if exists public.ia_rate_limits enable row level security;

-- Recriação idempotente das policies deste arquivo

drop policy if exists usuarios_select_self_or_admin on public.usuarios;
drop policy if exists usuarios_update_self_or_admin on public.usuarios;

drop policy if exists atendimentos_select_owner_or_admin on public.atendimentos;
drop policy if exists atendimentos_insert_owner_or_admin on public.atendimentos;
drop policy if exists atendimentos_update_owner_or_admin on public.atendimentos;
drop policy if exists atendimentos_delete_owner_or_admin on public.atendimentos;

drop policy if exists historico_select_owner_or_admin on public.historico_atendimento;
drop policy if exists historico_insert_owner_or_admin on public.historico_atendimento;

drop policy if exists logs_select_owner_or_admin on public.logs_ia;
drop policy if exists relatorios_select_owner_or_admin on public.relatorios;
drop policy if exists documentos_select_owner_or_admin on public.documentos;
drop policy if exists quesitos_select_owner_or_admin on public.quesitos;

drop policy if exists admin_all_configuracoes on public.configuracoes;
drop policy if exists admin_all_cache_ia on public.cache_ia;
drop policy if exists admin_all_ia_rate_limits on public.ia_rate_limits;

-- Usuário/profissional: médico vê apenas seu próprio perfil.
create policy usuarios_select_self_or_admin
on public.usuarios
for select
to authenticated
using (
  id = auth.uid()::text
  or public.app_role() in ('Administrador','Gestor','Coordenador','Revisor')
);

-- Médico não pode alterar o próprio perfil/role diretamente pelo cliente.
-- Administradores e perfis de gestão mantêm o fluxo administrativo existente.
create policy usuarios_update_self_or_admin
on public.usuarios
for update
to authenticated
using (
  public.app_role() in ('Administrador','Gestor','Coordenador','Revisor')
)
with check (
  public.app_role() in ('Administrador','Gestor','Coordenador','Revisor')
);

-- REGRA PRINCIPAL: cada Médico só enxerga atendimentos cujo usuario_id
-- corresponde ao seu auth.uid(). O usuário_id é TEXT nesta tabela.
create policy atendimentos_select_owner_or_admin
on public.atendimentos
for select
to authenticated
using (
  usuario_id = auth.uid()::text
  or public.app_role() in ('Administrador','Gestor','Coordenador','Revisor','Consulta')
);

create policy atendimentos_insert_owner_or_admin
on public.atendimentos
for insert
to authenticated
with check (
  usuario_id = auth.uid()::text
  or public.app_role() in ('Administrador','Coordenador')
);

create policy atendimentos_update_owner_or_admin
on public.atendimentos
for update
to authenticated
using (
  usuario_id = auth.uid()::text
  or public.app_role() in ('Administrador','Coordenador')
)
with check (
  usuario_id = auth.uid()::text
  or public.app_role() in ('Administrador','Coordenador')
);

create policy atendimentos_delete_owner_or_admin
on public.atendimentos
for delete
 to authenticated
using (
  usuario_id = auth.uid()::text
  or public.app_role() = 'Administrador'
);

-- Dados derivados do atendimento herdam o mesmo isolamento.
create policy historico_select_owner_or_admin
on public.historico_atendimento
for select
 to authenticated
using (
  exists (
    select 1
    from public.atendimentos a
    where a.id = historico_atendimento.atendimento_id
      and (
        a.usuario_id = auth.uid()::text
        or public.app_role() in ('Administrador','Gestor','Coordenador','Revisor','Consulta')
      )
  )
);

create policy historico_insert_owner_or_admin
on public.historico_atendimento
for insert
 to authenticated
with check (
  exists (
    select 1
    from public.atendimentos a
    where a.id = historico_atendimento.atendimento_id
      and (
        a.usuario_id = auth.uid()::text
        or public.app_role() in ('Administrador','Coordenador')
      )
  )
);

create policy logs_select_owner_or_admin
on public.logs_ia
for select
 to authenticated
using (
  exists (
    select 1 from public.atendimentos a
    where a.id = logs_ia.atendimento_id
      and (a.usuario_id = auth.uid()::text or public.app_role() in ('Administrador','Gestor','Coordenador','Revisor','Consulta'))
  )
);

create policy relatorios_select_owner_or_admin
on public.relatorios
for select
 to authenticated
using (
  exists (
    select 1 from public.atendimentos a
    where a.id = relatorios.atendimento_id
      and (a.usuario_id = auth.uid()::text or public.app_role() in ('Administrador','Gestor','Coordenador','Revisor','Consulta'))
  )
);

create policy documentos_select_owner_or_admin
on public.documentos
for select
 to authenticated
using (
  exists (
    select 1 from public.atendimentos a
    where a.id = documentos.atendimento_id
      and (a.usuario_id = auth.uid()::text or public.app_role() in ('Administrador','Gestor','Coordenador','Revisor','Consulta'))
  )
);

create policy quesitos_select_owner_or_admin
on public.quesitos
for select
 to authenticated
using (
  exists (
    select 1 from public.atendimentos a
    where a.id = quesitos.atendimento_id
      and (a.usuario_id = auth.uid()::text or public.app_role() in ('Administrador','Gestor','Coordenador','Revisor','Consulta'))
  )
);

-- Configurações, cache e rate limits não ficam expostos ao cliente médico.
create policy admin_all_configuracoes
on public.configuracoes
for all
 to authenticated
using (public.app_role() = 'Administrador')
with check (public.app_role() = 'Administrador');

create policy admin_all_cache_ia
on public.cache_ia
for all
 to authenticated
using (public.app_role() = 'Administrador')
with check (public.app_role() = 'Administrador');

create policy admin_all_ia_rate_limits
on public.ia_rate_limits
for all
 to authenticated
using (public.app_role() = 'Administrador')
with check (public.app_role() = 'Administrador');

-- Observação: o backend Flask continua sendo a camada principal de autorização.
-- Estas policies são defesa adicional para acessos diretos via Supabase.
