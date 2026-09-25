# Ambiental — Avaliação Médica Pericial LTS

Reformulação profissional de autenticação, sessão e controle de acesso do sistema existente.

## Configuração

1. Copie `.env.example` para `.env` e preencha:
   - `SUPABASE_URL`: URL do projeto Supabase.
   - `SUPABASE_PUBLISHABLE_KEY`: chave publicável/anon do Supabase.
   - `DATABASE_URL`: string PostgreSQL real.
   - `GEMINI_API_KEY`: chave do provedor de IA, somente no servidor.
2. Mantenha `AUTH_REQUIRED=1`.
3. Em produção, use `APP_ENV=production`, HTTPS e `CORS_ORIGINS` com os domínios autorizados.

### Perfis

A autorização é baseada em perfis configurados no servidor. A tabela `usuarios` pode vincular o UUID do Supabase ao perfil (`Administrador`, `Médico`, `Coordenador`, `Revisor`, `Gestor`, `Consulta`). Como alternativa, um papel pode ser fornecido em `app_metadata` do usuário no Supabase — nunca em `user_metadata` enviado pelo navegador.

O usuário precisa possuir um perfil permitido para entrar nas áreas protegidas.

### Recuperação de senha

O Supabase Auth envia o link para `/reset-password.html`. Cadastre essa URL como Redirect URL no projeto Supabase.

### Segurança

O frontend não define perfil, usuário proprietário ou permissão. Os endpoints sensíveis validam a sessão no servidor, usando o token enviado ao endpoint oficial de usuário do Supabase. O servidor cria um cookie de sessão `HttpOnly`, `SameSite=Lax` e `Secure` em produção.

Senhas nunca são armazenadas pelo aplicativo. O sistema não grava `ambiental_access_token` manualmente.

Os segredos que estavam no pacote original foram removidos da versão entregue. Considere-os comprometidos e faça a rotação no provedor antes da produção, especialmente senha do PostgreSQL, chave da IA e qualquer segredo privado do Supabase.

### Dados existentes

Não são apagados os atendimentos. A inicialização adiciona apenas a coluna opcional `usuario_id` em `atendimentos` para permitir associação server-side do proprietário. Atendimentos históricos sem proprietário ficam preservados; médicos não recebem acesso a registros que não estejam vinculados a eles.

## Execução local

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
# source .venv/bin/activate

pip install -r requirements.txt
python app.py
```

Abra `http://127.0.0.1:8000/login.html`.

## Gestão de contas médicas (administrador)

A página `/gestao-medicos-admin.html` permite ao perfil `Administrador` criar e remover contas médicas.
A criação sincroniza o Supabase Authentication com a tabela `public.usuarios` (nome, perfil, CRM e ativo).
A remoção preserva os registros de atendimento e desativa o perfil em `usuarios`, além de remover a conta correspondente do Authentication.

Para habilitar a criação/remoção, configure no servidor a variável `SUPABASE_SERVICE_ROLE_KEY` com a chave de serviço do mesmo projeto Supabase. Essa chave deve permanecer exclusivamente no backend e nunca ser exposta ao navegador.
