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

// ── Wages ────────────────────────────────────────────────────────────

export function queryFairWage(occupation, district, state) {
  return post('/api/wages/query', { occupation, district, state });
}

export function fetchOccupations() {
  return get('/api/wages/occupations');
}

// ── Reports ──────────────────────────────────────────────────────────

export function submitWageReport(payload) {
  return post('/api/reports/submit', payload);
}

export function checkContractor(contractorName, district, state) {
  return post('/api/reports/contractor-check', {
    contractor_name: contractorName,
    district,
    state,
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

export function fetchDistrictHeatmap() {
  return get('/api/dashboard/district-heatmap');
}

export function fetchVulnerabilityScores(minScore = 0) {
  return get(`/api/dashboard/vulnerability-scores?min_score=${minScore}`);
}

export function fetchRecentAlerts() {
  return get('/api/dashboard/recent-alerts');
}

// ── WhatsApp webhook (web simulation) ───────────────────────────────

/**
 * Simulate a WhatsApp message to the bot.
 * In real Twilio setup, Twilio calls this — here the browser calls it directly.
 */
export async function sendBotMessage(text, phoneHash = 'demo-user') {
  const formData = new FormData();
  formData.append('From', `whatsapp:${phoneHash}`);
  formData.append('Body', text);

  const res = await fetch(`${BASE}/webhook/whatsapp`, {
    method: 'POST',
    body: formData,
  });

  if (!res.ok) throw new Error(`Bot request failed: ${res.status}`);
  return res.text(); // webhook returns plain text
}
