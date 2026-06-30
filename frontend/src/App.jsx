import React, { useState } from 'react';
import WorkerChat from './pages/WorkerChat';
import Dashboard from './pages/Dashboard';
import KycModal from './pages/KycModal';
import LandingPage from './pages/LandingPage';
import LabourOfficerDashboard from './pages/LabourOfficerDashboard';

const NAV = [
  { id: 'chat', icon: '💬', label: 'Worker Bot' },
];

export default function App() {
  const [activeView, setActiveView] = useState('landing');
  const [isKycVerified, setIsKycVerified] = useState(false);

  // The KYC modal should only block the chat view
  const showKyc = activeView === 'chat' && !isKycVerified;

  if (activeView === 'landing') {
    return <LandingPage onNavigate={setActiveView} />;
  }

  if (activeView === 'dashboard') {
    return <Dashboard onBack={() => setActiveView('landing')} />;
  }

  if (activeView === 'labour-officer') {
    return <LabourOfficerDashboard onBack={() => setActiveView('landing')} />;
  }

  return (
    <>
      {showKyc && <KycModal onVerify={() => setIsKycVerified(true)} />}
      <div className="app-shell" style={{ filter: showKyc ? 'blur(4px)' : 'none', transition: 'filter 0.3s' }}>
      {/* Sidebar */}
      <nav className="sidebar">
        <div className="sidebar-logo" onClick={() => setActiveView('landing')} style={{cursor: 'pointer'}}>🛡️</div>
        {NAV.map((item) => (
          <button
            key={item.id}
            className={`sidebar-nav-btn ${activeView === item.id ? 'active' : ''}`}
            onClick={() => setActiveView(item.id)}
            title={item.label}
          >
            {item.icon}
          </button>
        ))}
      </nav>

      {/* Main */}
      <div className="main-content">
        {activeView === 'chat' && <WorkerChat />}
      </div>
    </div>

    </>
  );
}
