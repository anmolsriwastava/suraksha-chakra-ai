/**
 * api.js — all backend calls live here.
 * Components never call fetch() directly.
 */

const BASE = process.env.REACT_APP_API_URL || '';

async function post(path, body) {
  const res = await fetch(`${BASE}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Request failed: ${res.status}`);
  }
  return res.json();
}

async function get(path) {
  const res = await fetch(`${BASE}${path}`);
  if (!res.ok) throw new Error(`Request failed: ${res.status}`);
  return res.json();
}

// ── Chat (new AI pipeline) ──────────────────────────────────────────

/**
 * Send a chat message (text or voice) to the new /api/chat endpoint.
 * Returns { reply, session_id, extracted, quick_replies }
 */
export async function sendChatMessage(message, sessionId = 'demo-user', audioBase64 = null, language = 'en') {
  return post('/api/chat', {
    message,
    session_id: sessionId,
    audio_base64: audioBase64,
    language: language
  });
}



export function fetchHighRiskContractors(state = null) {
  const qs = state ? `?state=${state}` : '';
  return get(`/api/reports/contractors/high-risk${qs}`);
}

// ── Dashboard ────────────────────────────────────────────────────────

export function fetchDashboardOverview() {
  return get('/api/dashboard/overview');
}

export function fetchRecentComplaints(limit = 50) {
  return get(`/api/dashboard/reports?limit=${limit}`);
}

export function fetchAllContractors() {
  return get('/api/dashboard/contractors');
}

export function fetchDistrictHeatmap() {
  return get('/api/dashboard/district-heatmap');
}

export function fetchVulnerabilityScores(minScore = 0) {
  return get(`/api/dashboard/vulnerability-scores?min_score=${minScore}`);
}

export function fetchVulnerabilityOverview() {
  return get('/api/dashboard/vulnerability-overview');
}

export function fetchRecentAlerts() {
  return get('/api/dashboard/recent-alerts');
}

export function fetchComplaintAnalytics() {
  return get('/api/dashboard/complaint-analytics');
}
