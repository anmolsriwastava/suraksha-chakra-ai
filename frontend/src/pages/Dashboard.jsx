import React, { useState, useEffect } from 'react';
import {
  fetchDashboardOverview,
  fetchHighRiskContractors,
  fetchVulnerabilityScores,
  fetchRecentAlerts,
} from '../utils/api';

// ── Helpers ──────────────────────────────────────────────────────────

function RiskBadge({ score }) {
  const level = score >= 80 ? 'low' : score >= 50 ? 'medium' : 'high';
  const label = score >= 80 ? '✅ Safe' : score >= 50 ? '⚠️ Caution' : '🚨 High Risk';
  return <span className={`risk-badge ${level}`}>{label}</span>;
}

function VulnBadge({ score }) {
  const level = score >= 70 ? 'high' : score >= 45 ? 'medium' : 'low';
  const label = score >= 70 ? '🔴 Danger' : score >= 45 ? '🟡 Watch' : '🟢 Normal';
  return <span className={`risk-badge ${level}`}>{label}</span>;
}

function StatCard({ label, value, sub, accent }) {
  return (
    <div className="stat-card">
      <div className="stat-card-label">{label}</div>
      <div className="stat-card-value" style={accent ? { color: accent } : {}}>
        {value}
      </div>
      {sub && <div className="stat-card-sub">{sub}</div>}
    </div>
  );
}

function Section({ title, children }) {
  return (
    <div style={{ marginBottom: 28 }}>
      <p className="section-title">{title}</p>
      {children}
    </div>
  );
}

// ── Mock data fallback (used if backend is not running) ──────────────

const MOCK_OVERVIEW = {
  total_anonymous_reports: 247,
  high_risk_contractors: 12,
  ngo_alerts_sent: 34,
  average_wage_gap_inr: 198,
};

const MOCK_CONTRACTORS = [
  { name: 'Ramesh Constructions', district: 'Delhi', state: 'Delhi', risk_score: 24, total_reports: 18, verified_bad_reports: 15 },
  { name: 'Sharma Builders', district: 'Noida', state: 'UP', risk_score: 38, total_reports: 11, verified_bad_reports: 9 },
  { name: 'JP Infrastructure', district: 'Mumbai', state: 'Maharashtra', risk_score: 42, total_reports: 8, verified_bad_reports: 7 },
  { name: 'Gupta & Sons Labour', district: 'Patna', state: 'Bihar', risk_score: 19, total_reports: 22, verified_bad_reports: 19 },
];

const MOCK_VULN = [
  { district: 'Darbhanga', state: 'Bihar', composite_score: 78, disaster_risk: 70, historical_crime_spike: 65, migration_pressure: 80, active_wage_reports: 60, forecast_window_days: 30 },
  { district: 'Sitamarhi', state: 'Bihar', composite_score: 74, disaster_risk: 72, historical_crime_spike: 60, migration_pressure: 80, active_wage_reports: 40, forecast_window_days: 30 },
  { district: 'Azamgarh', state: 'UP', composite_score: 62, disaster_risk: 45, historical_crime_spike: 55, migration_pressure: 80, active_wage_reports: 50, forecast_window_days: 30 },
  { district: 'Muzaffarpur', state: 'Bihar', composite_score: 68, disaster_risk: 65, historical_crime_spike: 58, migration_pressure: 72, active_wage_reports: 45, forecast_window_days: 30 },
];

const MOCK_ALERTS = [
  { id: 1, alert_type: 'wage_theft', district: 'Delhi', sent_at: new Date(Date.now() - 3600000).toISOString(), acknowledged: false },
  { id: 2, alert_type: 'vulnerability_window', district: 'Darbhanga', sent_at: new Date(Date.now() - 86400000).toISOString(), acknowledged: true },
  { id: 3, alert_type: 'wage_theft', district: 'Patna', sent_at: new Date(Date.now() - 172800000).toISOString(), acknowledged: false },
];

// ── Dashboard ────────────────────────────────────────────────────────

export default function Dashboard() {
  const [overview, setOverview] = useState(null);
  const [contractors, setContractors] = useState([]);
  const [vulnScores, setVulnScores] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const [ov, ct, vs, al] = await Promise.all([
          fetchDashboardOverview(),
          fetchHighRiskContractors(),
          fetchVulnerabilityScores(40),
          fetchRecentAlerts(),
        ]);
        setOverview(ov);
        setContractors(ct.contractors || []);
        setVulnScores(vs.vulnerability_districts || []);
        setAlerts(al.alerts || []);
      } catch {
        // backend not running — use mock data for demo
        setOverview(MOCK_OVERVIEW);
        setContractors(MOCK_CONTRACTORS);
        setVulnScores(MOCK_VULN);
        setAlerts(MOCK_ALERTS);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  if (loading) {
    return (
      <div className="dashboard-page" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <p className="text-muted">Loading dashboard…</p>
      </div>
    );
  }

  return (
    <div className="dashboard-page">
      <div className="dashboard-header">
        <h1>Suraksha Chakra — Command Centre</h1>
        <p>Anonymised intelligence from field reports · Updated every 24 hours</p>
      </div>

      {/* Stat cards */}
      <div className="stat-grid">
        <StatCard
          label="Anonymous Reports"
          value={overview.total_anonymous_reports}
          sub="from workers across India"
        />
        <StatCard
          label="High-Risk Contractors"
          value={overview.high_risk_contractors}
          sub="score below 50/100"
          accent="#ef4444"
        />
        <StatCard
          label="NGO Alerts Sent"
          value={overview.ngo_alerts_sent}
          sub="NGOs + Labour Officers"
          accent="#10b981"
        />
        <StatCard
          label="Avg Wage Gap"
          value={`₹${overview.average_wage_gap_inr}/day`}
          sub="across all reports"
          accent="#fbbf24"
        />
      </div>

      {/* Contractor risk table */}
      <Section title="🚨 High-Risk Contractors">
        <div className="table-card">
          <table className="contractor-table">
            <thead>
              <tr>
                <th>Contractor</th>
                <th>District</th>
                <th>State</th>
                <th>Risk Score</th>
                <th>Reports</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {contractors.length === 0 ? (
                <tr>
                  <td colSpan={6} style={{ textAlign: 'center', padding: 24, color: 'var(--text-muted)' }}>
                    No high-risk contractors yet. Good news!
                  </td>
                </tr>
              ) : (
                contractors.map((c, i) => (
                  <tr key={i}>
                    <td style={{ fontWeight: 500 }}>{c.name}</td>
                    <td className="text-muted">{c.district}</td>
                    <td className="text-muted">{c.state}</td>
                    <td style={{ fontWeight: 600, color: c.risk_score < 50 ? 'var(--accent-red)' : 'var(--accent-yellow)' }}>
                      {c.risk_score}/100
                    </td>
                    <td className="text-muted">{c.verified_bad_reports} verified</td>
                    <td><RiskBadge score={c.risk_score} /></td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </Section>

      {/* Vulnerability scores */}
      <Section title="🌊 District Vulnerability Forecast (Next 30 days)">
        <div className="table-card">
          <table className="contractor-table">
            <thead>
              <tr>
                <th>District</th>
                <th>State</th>
                <th>Composite Score</th>
                <th>Disaster Risk</th>
                <th>Crime Spike</th>
                <th>Migration</th>
                <th>Alert Level</th>
              </tr>
            </thead>
            <tbody>
              {vulnScores.map((v, i) => (
                <tr key={i}>
                  <td style={{ fontWeight: 500 }}>{v.district}</td>
                  <td className="text-muted">{v.state}</td>
                  <td style={{ fontWeight: 600 }}>{v.composite_score}/100</td>
                  <td className="text-muted">{v.disaster_risk}</td>
                  <td className="text-muted">{v.historical_crime_spike}</td>
                  <td className="text-muted">{v.migration_pressure}</td>
                  <td><VulnBadge score={v.composite_score} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Section>

      {/* Recent alerts */}
      <Section title="📨 Recent Alerts Sent">
        <div className="table-card">
          <table className="contractor-table">
            <thead>
              <tr>
                <th>Type</th>
                <th>District</th>
                <th>Sent</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {alerts.map((a) => (
                <tr key={a.id}>
                  <td>
                    {a.alert_type === 'wage_theft'
                      ? '⚠️ Wage Theft Cluster'
                      : '🌊 Vulnerability Window'}
                  </td>
                  <td className="text-muted">{a.district || '—'}</td>
                  <td className="text-muted">{new Date(a.sent_at).toLocaleDateString('en-IN')}</td>
                  <td>
                    <span className={`risk-badge ${a.acknowledged ? 'low' : 'medium'}`}>
                      {a.acknowledged ? '✅ Acknowledged' : '⏳ Pending'}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Section>
    </div>
  );
}
