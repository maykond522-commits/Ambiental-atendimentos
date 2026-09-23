/* Ambiental — API Service Layer
 * Frontend deve chamar este módulo em vez de repetir fetch/auth/error handling.
 */
(() => {
  'use strict';
  const json = async (res) => res.json().catch(() => null);
  const messageFor = (body, status) => {
    const code = body?.error?.code;
    const map = {
      AUTH_ERROR: 'Sua sessão expirou ou não é válida. Entre novamente.',
      PERMISSION_DENIED: 'Seu perfil não possui permissão para esta ação.',
      VERSION_CONFLICT: 'Este atendimento foi atualizado em outro dispositivo. Recarregue antes de continuar.',
      VALIDATION_ERROR: body?.error?.message,
      AI_PROVIDER_BUSY: 'A assistência inteligente está temporariamente ocupada. Tente novamente em instantes.',
      AI_UNAVAILABLE: 'A assistência inteligente está temporariamente indisponível.'
    };
    return map[code] || body?.error?.message || body?.detail || `Não foi possível concluir a solicitação (HTTP ${status}).`;
  };

  async function request(path, options = {}) {
    if (!window.AmbientalAuth?.authFetch) throw new Error('Camada de autenticação indisponível.');
    const timeoutMs = Number(options.timeoutMs || 20000);
    const { timeoutMs: _ignored, ...requestOptions } = options;
    const method = String(requestOptions.method || 'GET').toUpperCase();
    const canRetry = method === 'GET' && requestOptions.retry !== false;
    const attempts = canRetry ? 2 : 1;

    for (let attempt = 1; attempt <= attempts; attempt++) {
      const controller = new AbortController();
      const timer = window.setTimeout(() => controller.abort(), timeoutMs);
      let response;
      try {
        response = await AmbientalAuth.authFetch(path, {
          credentials: 'same-origin',
          cache: 'no-store',
          ...requestOptions,
          signal: requestOptions.signal || controller.signal,
          headers: {
            Accept: 'application/json',
            ...(requestOptions.body ? { 'Content-Type': 'application/json' } : {}),
            ...(requestOptions.headers || {})
          }
        });
      } catch (err) {
        if (attempt < attempts && err?.name !== 'AbortError') {
          await new Promise(r => setTimeout(r, 250));
          continue;
        }
        const error = new Error(err?.name === 'AbortError' ? 'A solicitação demorou mais que o esperado.' : 'Não foi possível conectar ao servidor.');
        error.code = err?.name === 'AbortError' ? 'REQUEST_TIMEOUT' : 'NETWORK_ERROR';
        error.retryable = true;
        throw error;
      } finally {
        window.clearTimeout(timer);
      }
      const body = await json(response);
      if (response.ok && body?.success !== false) return body?.data ?? body;
      const error = new Error(messageFor(body, response.status));
      error.code = body?.error?.code || `HTTP_${response.status}`;
      error.status = response.status;
      error.body = body;
      error.requestId = response.headers.get('X-Request-ID') || body?.request_id || null;
      if (attempt < attempts && [502, 503, 504].includes(response.status)) {
        await new Promise(r => setTimeout(r, 350));
        continue;
      }
      throw error;
    }
    throw new Error('Não foi possível concluir a solicitação.');
  }

  const API = {
    request,
    auth: {
      me: () => request('/api/auth/me'),
      logout: () => AmbientalAuth.logout()
    },
    medico: {
      dashboard: () => request('/api/medico/dashboard'),
      atendimentos: (params = {}) => request(`/api/medico/atendimentos?${new URLSearchParams(params)}`)
    },
    atendimento: {
      get: (id) => request(`/api/atendimentos/${encodeURIComponent(id)}`),
      save: (id, payload) => request(id ? `/api/atendimentos/${encodeURIComponent(id)}` : '/api/atendimentos', {
        method: id ? 'PUT' : 'POST', body: JSON.stringify(payload)
      }),
      history: (id) => request(`/api/atendimentos/${encodeURIComponent(id)}/historico`)
    },
    ai: {
      justificativa: (payload) => request('/api/ai/justificativa', { method: 'POST', body: JSON.stringify(payload) }),
      preenchimento: (payload) => request('/api/ai/preenchimento', { method: 'POST', body: JSON.stringify(payload) }),
      documento: (payload) => request('/api/ai/documento', { method: 'POST', body: JSON.stringify(payload) }),
      esisla: (payload) => request('/api/ai/esisla', { method: 'POST', body: JSON.stringify(payload) })
    },
    admin: {
      medicos: () => request('/api/admin/medicos'),
      createMedico: (payload) => request('/api/admin/medicos', { method: 'POST', body: JSON.stringify(payload) }),
      updateMedico: (id, payload) => request(`/api/admin/medicos/${encodeURIComponent(id)}`, { method: 'PUT', body: JSON.stringify(payload) }),
      toggleStatus: (id) => request(`/api/admin/medicos/${encodeURIComponent(id)}/status`, { method: 'PATCH' }),
      resetSenha: (id, senha) => request(`/api/admin/medicos/${encodeURIComponent(id)}/senha`, { method: 'POST', body: JSON.stringify({ senha }) }),
      deleteMedico: (id) => request(`/api/admin/medicos/${encodeURIComponent(id)}`, { method: 'DELETE' })
    }
  };

  window.AmbientalAPI = API;
})();
