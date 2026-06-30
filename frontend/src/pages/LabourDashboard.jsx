import React, { useState, useEffect } from 'react';
import { fetchDashboardOverview, fetchRecentComplaints, fetchAllContractors, fetchDistrictHeatmap } from '../utils/api';
import styles from './Dashboard.module.css';

function RiskBadge({ score }) {
  let levelClass = styles.green;
  let label = '🟢 Safe';
  
  if (score > 75) {
    levelClass = styles.red;
    label = '🔴 High Risk';
  } else if (score > 50) {
    levelClass = styles.orange;
    label = '🟠 Warning';
  } else if (score > 25) {
    levelClass = styles.yellow;
    label = '🟡 Caution';
  }

  return <span className={`${styles.badge} ${levelClass}`}>{label}</span>;
}

export default function LabourDashboard({ onBack }) {
  const [overview, setOverview] = useState(null);
  const [complaints, setComplaints] = useState([]);
  const [contractors, setContractors] = useState([]);
  const [districts, setDistricts] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      try {
        const [ov, cmp, ctn, dst] = await Promise.all([
          fetchDashboardOverview(),
          fetchRecentComplaints(20),
          fetchAllContractors(),
          fetchDistrictHeatmap()
        ]);
        setOverview(ov);
        setComplaints(cmp.complaints || []);
        setContractors(ctn.contractors || []);
        setDistricts(dst.districts || []);
      } catch (err) {
        console.error("Failed to load labour dashboard:", err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  if (loading) return <div className={styles.dashboardPage}><p>Loading Intelligence...</p></div>;

  return (
    <div className={styles.dashboardPage}>
      <div className={styles.header}>
        <button className={styles.backBtn} onClick={onBack}>← Back to Gateway</button>
        <h1 className={styles.title}>Labour Intelligence</h1>
        <p className={styles.subtitle}>Worker complaints, contractor monitoring, and exploitation analytics.</p>
      </div>

      <div className={styles.statGrid}>
        <div className={styles.statCard}>
          <div className={styles.statLabel}>Total Complaints</div>
          <div className={styles.statValue}>{overview?.total_complaints || 0}</div>
        </div>
        <div className={styles.statCard}>
          <div className={styles.statLabel}>Complaints (Last 7 Days)</div>
          <div className={styles.statValue}>{overview?.complaints_last_7_days || 0}</div>
        </div>
        <div className={styles.statCard}>
          <div className={styles.statLabel}>High Risk Contractors</div>
          <div className={styles.statValue} style={{ color: '#ef4444' }}>{overview?.high_risk_contractors || 0}</div>
        </div>
        <div className={styles.statCard}>
          <div className={styles.statLabel}>Legal Notices Generated</div>
          <div className={styles.statValue} style={{ color: '#10b981' }}>{overview?.legal_notices_generated || 0}</div>
        </div>
      </div>

      <div className={styles.tableCard}>
        <h3 className={styles.tableTitle}>Recent Complaints</h3>
        <table className={styles.dataTable}>
          <thead>
            <tr>
              <th>Worker ID</th>
              <th>District</th>
              <th>Contractor</th>
              <th>Reported / Fair</th>
              <th>Wage Gap</th>
              <th>Status</th>
              <th>Reported Time</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {complaints.length === 0 ? (
              <tr><td colSpan={8} style={{ textAlign: 'center' }}>No recent complaints found.</td></tr>
            ) : (
              complaints.map(c => (
                <tr key={c.id}>
                  <td style={{ fontFamily: 'monospace' }}>{c.worker_id}</td>
                  <td>{c.district}</td>
                  <td>{c.contractor_name}</td>
                  <td>₹{c.reported_wage} / ₹{c.fair_wage}</td>
                  <td style={{ color: c.wage_gap > 0 ? '#ef4444' : '#10b981' }}>
                    {c.wage_gap > 0 ? `+₹${c.wage_gap}` : `₹${c.wage_gap}`}
                  </td>
                  <td><span className={`${styles.badge} ${c.status === 'pending' ? styles.yellow : styles.green}`}>{c.status}</span></td>
                  <td>{new Date(c.reported_at).toLocaleDateString()}</td>
                  <td>
                    <button className={styles.actionBtn}>View</button>
                    {c.wage_gap > 0 && (
                      <a 
                        href={`http://localhost:8000/api/reports/legal-notice/${c.id}`} 
                        target="_blank" 
                        rel="noreferrer"
                        className={`${styles.actionBtn} ${styles.primary}`}
                        style={{ textDecoration: 'none' }}
                      >
                        PDF
                      </a>
                    )}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      <div className={styles.detailGrid}>
        <div className={styles.tableCard} style={{ marginBottom: 0 }}>
          <h3 className={styles.tableTitle}>High Risk Contractors</h3>
          <table className={styles.dataTable}>
            <thead>
              <tr>
                <th>Contractor</th>
                <th>District</th>
                <th>Risk Score</th>
                <th>Complaints</th>
                <th>Risk Badge</th>
              </tr>
            </thead>
            <tbody>
              {contractors.map(c => (
                <tr key={c.id}>
                  <td>{c.name}</td>
                  <td>{c.district}</td>
                  <td style={{ fontWeight: 600 }}>{c.risk_score}</td>
                  <td>{c.total_reports}</td>
                  <td>
                    <RiskBadge score={c.risk_score} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className={styles.tableCard} style={{ marginBottom: 0 }}>
          <h3 className={styles.tableTitle}>District Labour Analytics</h3>
          <table className={styles.dataTable}>
            <thead>
              <tr>
                <th>District</th>
                <th>Complaints</th>
                <th>Avg Gap</th>
                <th>Trend</th>
              </tr>
            </thead>
            <tbody>
              {districts.map((d, i) => (
                <tr key={i}>
                  <td>{d.district}</td>
                  <td>{d.report_count}</td>
                  <td style={{ color: '#ef4444' }}>₹{d.avg_wage_gap}</td>
                  <td>
                    <span className={`${styles.badge} ${d.trend === 'Up' ? styles.red : styles.green}`}>{d.trend}</span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

    </div>
  );
}
