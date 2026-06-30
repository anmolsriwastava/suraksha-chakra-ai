import React, { useState, useEffect } from 'react';
import styles from './LabourOfficerDashboard.module.css';
import { 
  fetchDashboardOverview, 
  fetchRecentComplaints, 
  fetchAllContractors, 
  fetchComplaintAnalytics,
  fetchDistrictHeatmap,
  fetchRecentAlerts
} from '../utils/api';

export default function LabourOfficerDashboard({ onBack }) {
  const [loading, setLoading] = useState(true);
  const [overview, setOverview] = useState(null);
  const [complaints, setComplaints] = useState([]);
  const [contractors, setContractors] = useState([]);
  const [analytics, setAnalytics] = useState(null);
  const [districts, setDistricts] = useState([]);
  const [alerts, setAlerts] = useState([]);
  
  const [toast, setToast] = useState(null);
  
  // For demo Timeline
  const [selectedCase, setSelectedCase] = useState(null);

  useEffect(() => {
    async function loadData() {
      try {
        const [
          overviewRes, 
          complaintsRes, 
          contractorsRes, 
          analyticsRes,
          heatmapRes,
          alertsRes
        ] = await Promise.all([
          fetchDashboardOverview(),
          fetchRecentComplaints(50),
          fetchAllContractors(),
          fetchComplaintAnalytics(),
          fetchDistrictHeatmap(),
          fetchRecentAlerts()
        ]);
        
        setOverview(overviewRes);
        setComplaints(complaintsRes.complaints);
        setContractors(contractorsRes.contractors);
        setAnalytics(analyticsRes);
        setDistricts(heatmapRes.districts);
        setAlerts(alertsRes.alerts);
        
        if (complaintsRes.complaints.length > 0) {
          setSelectedCase(complaintsRes.complaints[0]);
        }
        
      } catch (err) {
        console.error("Failed to load officer dashboard data:", err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  const showToast = (message) => {
    setToast(message);
    setTimeout(() => setToast(null), 3000);
  };

  const renderTimeline = () => {
    if (!selectedCase) return null;
    
    // Determine mock timeline based on status and assigned_officer
    const isAssigned = selectedCase.assigned_officer !== "Unassigned";
    const isVerified = selectedCase.status === "verified";
    const isResolved = selectedCase.status === "dismissed"; // just using dismissed as resolved for demo
    
    const steps = [
      { id: 1, label: 'Complaint Received', active: true },
      { id: 2, label: 'AI Wage Verification', active: true },
      { id: 3, label: 'Legal Notice Generated', active: isVerified },
      { id: 4, label: 'Officer Assigned', active: isAssigned },
      { id: 5, label: 'Inspection Scheduled', active: isAssigned && isVerified },
      { id: 6, label: 'Case Closed', active: isResolved }
    ];

    const activeStepsCount = steps.filter(s => s.active).length;
    const progressPercent = ((activeStepsCount - 1) / (steps.length - 1)) * 100;

    return (
      <div className={styles.section}>
        <h2 className={styles.sectionTitle}>
          <span>⏱️</span> Case Timeline (ID: {selectedCase.id})
        </h2>
        <div className={styles.timelineContainer}>
          <div className={styles.timelineLine}></div>
          <div className={styles.timelineLineFill} style={{ width: `${progressPercent}%` }}></div>
          
          {steps.map((step) => (
            <div key={step.id} className={styles.timelineStep}>
              <div className={`${styles.stepDot} ${step.active ? styles.completed : ''}`}>✓</div>
              <div className={`${styles.stepLabel} ${step.active ? styles.completed : ''}`}>{step.label}</div>
            </div>
          ))}
        </div>
      </div>
    );
  };

  if (loading) return <div style={{ color: 'white', padding: 40 }}>Loading Intelligence...</div>;

  return (
    <div className={styles.pageContainer}>
      
      {/* Toast Notification */}
      {toast && (
        <div className={styles.toastContainer}>
          <div className={styles.toast}>
            <span>✅</span> {toast}
          </div>
        </div>
      )}

      {/* Hero Section */}
      <div className={styles.header}>
        <button className={styles.backBtn} onClick={onBack}>← Back to Gateway</button>
        <h1 className={styles.title}>Labour Enforcement & Investigation Portal</h1>
        <p className={styles.subtitle}>AI-assisted labour law enforcement, complaint investigation, contractor monitoring and legal action management.</p>
      </div>

      <div className={styles.kpiGrid}>
        <div className={styles.kpiCard}>
          <div className={styles.kpiLabel}>Pending Investigations</div>
          <div className={styles.kpiValue}>{overview?.pending_investigations || 0}</div>
        </div>
        <div className={styles.kpiCard}>
          <div className={styles.kpiLabel}>Active Officers</div>
          <div className={styles.kpiValue}>{overview?.active_officers || 4}</div>
        </div>
        <div className={styles.kpiCard}>
          <div className={styles.kpiLabel}>High-Risk Contractors</div>
          <div className={styles.kpiValue}>{overview?.high_risk_contractors || 0}</div>
        </div>
        <div className={styles.kpiCard}>
          <div className={styles.kpiLabel}>Legal Notices Generated</div>
          <div className={styles.kpiValue}>{overview?.legal_notices_generated || 0}</div>
        </div>
      </div>

      {/* Complaint Analytics */}
      <div className={styles.section}>
        <h2 className={styles.sectionTitle}><span>📊</span> Complaint Analytics</h2>
        <div className={styles.analyticsGrid}>
          <div className={styles.analyticsCard}>
            <h4>Complaints Today</h4>
            <p className={styles.val}>{analytics?.complaints_today}</p>
          </div>
          <div className={styles.analyticsCard}>
            <h4>Last 7 Days</h4>
            <p className={styles.val}>{analytics?.complaints_7_days}</p>
          </div>
          <div className={styles.analyticsCard}>
            <h4>Last 30 Days</h4>
            <p className={styles.val}>{analytics?.complaints_30_days}</p>
          </div>
          <div className={styles.analyticsCard}>
            <h4>Average Wage Gap</h4>
            <p className={styles.val}>₹{analytics?.avg_wage_gap}</p>
          </div>
          <div className={styles.analyticsCard}>
            <h4>Most Affected Occ.</h4>
            <p className={styles.val} style={{ fontSize: '1.2rem', marginTop: '0.5rem' }}>{analytics?.most_affected_occupation}</p>
          </div>
          <div className={styles.analyticsCard}>
            <h4>Highest District</h4>
            <p className={styles.val} style={{ fontSize: '1.2rem', marginTop: '0.5rem' }}>{analytics?.highest_complaint_district}</p>
          </div>
        </div>
      </div>

      {/* Officer Actions */}
      <div className={styles.section}>
        <h2 className={styles.sectionTitle}><span>⚡</span> Officer Actions</h2>
        <div className={styles.actionPanelGrid}>
          <button className={`${styles.panelBtn} ${styles.primary}`} onClick={() => showToast('Assigning inspection route to active field officers...')}>
            <span>👮</span> Assign Inspection
          </button>
          <button className={`${styles.panelBtn} ${styles.danger}`} onClick={() => showToast('Generating legal notices for critical offenses...')}>
            <span>⚖️</span> Generate Legal Notice
          </button>
          <button className={styles.panelBtn} onClick={() => showToast('Downloading PDF Investigation Report...')}>
            <span>📄</span> Download Report
          </button>
          <button className={styles.panelBtn} onClick={() => showToast('Exporting enforcement data to CSV...')}>
            <span>📊</span> Export CSV
          </button>
          <button className={styles.panelBtn} onClick={() => showToast('Escalated selected cases to State Labour Dept.')}>
            <span>🚨</span> Escalate to State
          </button>
        </div>
      </div>

      {/* Investigation Queue */}
      <div className={styles.section}>
        <h2 className={styles.sectionTitle}><span>📋</span> Investigation Queue</h2>
        <div className={styles.tableContainer}>
          <table className={styles.table}>
            <thead>
              <tr>
                <th>Case ID</th>
                <th>Worker ID</th>
                <th>District</th>
                <th>Contractor</th>
                <th>Occupation</th>
                <th>Wage Gap</th>
                <th>Priority</th>
                <th>Status</th>
                <th>Assigned Officer</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {complaints.map(c => (
                <tr key={c.id} onClick={() => setSelectedCase(c)} style={{ cursor: 'pointer', background: selectedCase?.id === c.id ? 'rgba(255,255,255,0.05)' : '' }}>
                  <td>#{c.id}</td>
                  <td>{c.worker_id}</td>
                  <td>{c.district}</td>
                  <td>{c.contractor_name}</td>
                  <td>{c.occupation}</td>
                  <td style={{ color: '#f87171', fontWeight: 'bold' }}>₹{c.wage_gap}</td>
                  <td>
                    <span className={`${styles.badge} ${c.priority === 'High' ? styles.badgeRed : (c.priority === 'Medium' ? styles.badgeOrange : styles.badgeYellow)}`}>
                      {c.priority}
                    </span>
                  </td>
                  <td>
                    <span className={`${styles.badge} ${c.status === 'verified' ? styles.badgeGreen : styles.badgeYellow}`}>
                      {c.status}
                    </span>
                  </td>
                  <td>{c.assigned_officer}</td>
                  <td>
                    <button className={styles.actionBtn} onClick={(e) => { e.stopPropagation(); showToast(`Action requested for Case #${c.id}`); }}>Investigate</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Case Timeline */}
      {renderTimeline()}

      {/* Contractor Investigation */}
      <div className={styles.section}>
        <h2 className={styles.sectionTitle}><span>🏢</span> Contractor Investigation</h2>
        <div className={styles.tableContainer}>
          <table className={styles.table}>
            <thead>
              <tr>
                <th>Contractor</th>
                <th>District</th>
                <th>Risk Score</th>
                <th>Complaints</th>
                <th>Status</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {contractors.map(c => {
                let badgeClass = styles.badgeGreen;
                if (c.risk_score < 50) badgeClass = styles.badgeRed;
                else if (c.risk_score < 70) badgeClass = styles.badgeOrange;
                else if (c.risk_score < 90) badgeClass = styles.badgeYellow;

                return (
                  <tr key={c.id}>
                    <td style={{ fontWeight: 'bold' }}>{c.name}</td>
                    <td>{c.district}</td>
                    <td>
                      <span className={`${styles.badge} ${badgeClass}`}>
                        {c.risk_score}/100
                      </span>
                    </td>
                    <td>{c.total_reports}</td>
                    <td>{c.risk_score < 50 ? 'Repeat Offender' : 'Under Observation'}</td>
                    <td>
                      <button className={styles.actionBtn} onClick={() => showToast(`Generated Notice for ${c.name}`)}>Send Notice</button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* District Enforcement Heatmap */}
      <div className={styles.section}>
        <h2 className={styles.sectionTitle}><span>🗺️</span> District Enforcement Heatmap</h2>
        <div className={styles.heatmapGrid}>
          {districts.map(d => (
            <div key={d.district} className={styles.districtCard}>
              <div className={styles.districtHeader}>
                <h3 className={styles.districtName}>{d.district}</h3>
                <span className={`${styles.badge} ${d.trend === 'Up' ? styles.badgeRed : styles.badgeGreen}`}>{d.trend}</span>
              </div>
              <div className={styles.districtStats}>
                <div className={styles.statRow}>
                  <span className={styles.statLabel}>Complaint Density</span>
                  <span className={styles.statValue}>{d.report_count}</span>
                </div>
                <div className={styles.statRow}>
                  <span className={styles.statLabel}>Avg Wage Gap</span>
                  <span className={styles.statValue} style={{ color: '#f87171' }}>₹{d.avg_wage_gap}</span>
                </div>
                <div className={styles.statRow}>
                  <span className={styles.statLabel}>High Risk Entity</span>
                  <span className={styles.statValue}>{d.highest_risk_contractor}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Recent Activity Feed */}
      <div className={styles.section}>
        <h2 className={styles.sectionTitle}><span>📡</span> Recent Activity Feed</h2>
        <div className={styles.feedList}>
          {alerts.slice(0, 5).map(a => (
            <div key={a.id} className={styles.feedItem}>
              <div className={styles.feedIcon}>{a.alert_type === 'wage_theft' ? '🚨' : '⚠️'}</div>
              <div className={styles.feedContent}>
                <p className={styles.feedText}>
                  System generated <strong>{a.alert_type}</strong> alert in {a.district}.
                </p>
                <p className={styles.feedTime}>{new Date(a.sent_at).toLocaleString()}</p>
              </div>
            </div>
          ))}
          {alerts.length === 0 && <p style={{ color: '#94a3b8' }}>No recent activity.</p>}
        </div>
      </div>

    </div>
  );
}
