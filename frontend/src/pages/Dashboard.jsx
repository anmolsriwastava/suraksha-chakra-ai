import React, { useState } from 'react';
import LabourDashboard from './LabourDashboard';
import VulnerabilityDashboard from './VulnerabilityDashboard';
import styles from './Dashboard.module.css';

export default function Dashboard({ onBack }) {
  const [activeModule, setActiveModule] = useState('gateway'); // 'gateway', 'labour', 'vulnerability'

  if (activeModule === 'labour') {
    return <LabourDashboard onBack={() => setActiveModule('gateway')} />;
  }

  if (activeModule === 'vulnerability') {
    return <VulnerabilityDashboard onBack={() => setActiveModule('gateway')} />;
  }

  return (
    <div className={styles.dashboardPage}>
      <div className={styles.header}>
        <button className={styles.backBtn} onClick={onBack}>← Back to Home</button>
        <h1 className={styles.title}>Suraksha Chakra Intelligence</h1>
        <p className={styles.subtitle}>Select an intelligence module to view live field data.</p>
      </div>

      <div className={styles.gatewayGrid}>
        {/* Labour Intelligence Card */}
        <div className={styles.gatewayCard}>
          <h3>Labour Intelligence <span className={`${styles.badge} ${styles.green}`}>Active</span></h3>
          <p>Worker complaints, contractor monitoring, legal notices and exploitation analytics directly from the field.</p>
          <button className={styles.gatewayBtn} onClick={() => setActiveModule('labour')}>Open Labour Intelligence</button>
        </div>

        {/* Vulnerability Intelligence Card */}
        <div className={styles.gatewayCard}>
          <h3>Vulnerability Intelligence <span className={`${styles.badge} ${styles.red}`}>Active</span></h3>
          <p>Disaster forecasting, trafficking prediction, migration intelligence and district risk forecasting.</p>
          <button className={styles.gatewayBtn} onClick={() => setActiveModule('vulnerability')}>Open Vulnerability Intelligence</button>
        </div>
      </div>

      <div className={styles.header} style={{ marginTop: 80, marginBottom: 30, textAlign: 'left' }}>
        <div style={{ display: 'inline-block', padding: '6px 14px', background: 'rgba(59, 130, 246, 0.1)', border: '1px solid rgba(59, 130, 246, 0.2)', color: '#60a5fa', borderRadius: '100px', fontSize: '12px', fontWeight: 'bold', textTransform: 'uppercase', letterSpacing: '1px', marginBottom: '16px' }}>
          Scalable Architecture
        </div>
        <h2 className={styles.title} style={{ fontSize: 24, marginBottom: 8 }}>Future Intelligence Expansion</h2>
        <p className={styles.subtitle} style={{ maxWidth: '800px', margin: '0' }}>Suraksha Chakra AI is architected to progressively expand its intelligence network from district-level monitoring to highly localized community intelligence.</p>
      </div>

      <div className={styles.gatewayGrid} style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))' }}>
        <div className={styles.gatewayCard}>
          <h3 style={{ fontSize: '18px', marginBottom: '12px', color: '#f8fafc' }}>Region-Specific NGO Intelligence</h3>
          <p style={{ fontSize: '14px', color: '#94a3b8', margin: 0, lineHeight: 1.5 }}>Each NGO dashboard will automatically filter intelligence based on its operational districts and states.</p>
        </div>
        <div className={styles.gatewayCard}>
          <h3 style={{ fontSize: '18px', marginBottom: '12px', color: '#f8fafc' }}>Village & Block-Level Monitoring</h3>
          <p style={{ fontSize: '14px', color: '#94a3b8', margin: 0, lineHeight: 1.5 }}>Extend monitoring beyond major cities to villages, panchayats and blocks.</p>
        </div>
        <div className={styles.gatewayCard}>
          <h3 style={{ fontSize: '18px', marginBottom: '12px', color: '#f8fafc' }}>River Basin Intelligence</h3>
          <p style={{ fontSize: '14px', color: '#94a3b8', margin: 0, lineHeight: 1.5 }}>Monitor vulnerable settlements along rivers such as Kosi, Gandak, Ganga and Brahmaputra.</p>
        </div>
        <div className={styles.gatewayCard}>
          <h3 style={{ fontSize: '18px', marginBottom: '12px', color: '#f8fafc' }}>NLP-Based Location Intelligence</h3>
          <p style={{ fontSize: '14px', color: '#94a3b8', margin: 0, lineHeight: 1.5 }}>Extract locations from worker reports, disaster bulletins and local news (e.g., "near Kosi Barrage") and map them into geographic clusters.</p>
        </div>
        <div className={styles.gatewayCard}>
          <h3 style={{ fontSize: '18px', marginBottom: '12px', color: '#f8fafc' }}>Migration Corridor Detection</h3>
          <p style={{ fontSize: '14px', color: '#94a3b8', margin: 0, lineHeight: 1.5 }}>Identify emerging migration routes and displacement hotspots after disasters.</p>
        </div>
        <div className={styles.gatewayCard}>
          <h3 style={{ fontSize: '18px', marginBottom: '12px', color: '#f8fafc' }}>Predictive Community Risk</h3>
          <p style={{ fontSize: '14px', color: '#94a3b8', margin: 0, lineHeight: 1.5 }}>Forecast trafficking and labour exploitation risk before large-scale migration begins.</p>
        </div>
      </div>
    </div>
  );
}
