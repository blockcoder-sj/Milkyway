/* The research transport boundary. Spending requires an explicit approve() call. */
(() => {
  const sessionPath = id => `/api/research/sessions/${encodeURIComponent(id)}`;
  const turnPath = id => `/api/research/turns/${encodeURIComponent(id)}`;
  const post = body => ({method: "POST", body: JSON.stringify(body)});
  function create(api) {
    return Object.freeze({
      configuration: () => api("/api/research/config"),
      sessions: () => api("/api/research/sessions"),
      session: id => api(sessionPath(id)),
      createSession: body => api("/api/research/sessions", post(body)),
      rename: (id, title) => api(sessionPath(id), {method: 'PATCH', body: JSON.stringify({title})}),
      prepare: (id, body) => api(`${sessionPath(id)}/messages`, post(body)),
      compare: (id, body) => api(`${sessionPath(id)}/experiments`, post(body)),
      deploy: (id, body) => api(`${sessionPath(id)}/deploy`, post(body)),
      adjust: (id, strategyId, body) => api(`${sessionPath(id)}/versions/${encodeURIComponent(strategyId)}/adjust`, post(body)),
      select: (id, strategyId) => api(`${sessionPath(id)}/select/${encodeURIComponent(strategyId)}`, post({})),
      cancel: id => api(`${turnPath(id)}/cancel`, post({})),
      approve: (id, digest) => api(`${turnPath(id)}/approve`, post({approved: true, request_digest: digest})),
    });
  }
  window.MilkywayResearchApi = Object.freeze({create, sessionPath});
})();
