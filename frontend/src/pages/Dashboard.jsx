import React, { useState, useEffect } from 'react';
import {
  fetchDashboardOverview,
  fetchHighRiskContractors,
  fetchVulnerabilityScores,
  fetchRecentAlerts,
} from '../utils/api';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';

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

// Removed MOCK fallbacks completely as per predictive layer activation requirements.

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
      } catch (err) {
        // backend not running — show empty clean state
        setOverview({ total_anonymous_reports: 0, high_risk_contractors: 0, ngo_alerts_sent: 0, average_wage_gap_inr: 0 });
        setContractors([]);
        setVulnScores([]);
        setAlerts([]);
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

      {/* Displacement Risk */}
      <Section title="🚨 Displacement & Trafficking Risk">
        <p className="text-muted" style={{ marginBottom: '16px' }}>
          Districts with elevated composite vulnerability have historically experienced increased risks of trafficking and labour exploitation following climate-related displacement.
        </p>
        <div className="table-card" style={{ height: '300px', padding: '16px' }}>
          {vulnScores.length === 0 ? (
            <div style={{ textAlign: 'center', paddingTop: '100px', color: 'var(--text-muted)' }}>No vulnerability data available</div>
          ) : (
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={vulnScores.slice(0, 5).map(v => ({ name: v.district, score: v.composite_score }))}>
                <XAxis dataKey="name" stroke="#a1a1aa" />
                <YAxis stroke="#a1a1aa" />
                <Tooltip />
                <Bar dataKey="score" fill="#ef4444" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>
      </Section>

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
