import React, { useState } from 'react';
import WorkerChat from './pages/WorkerChat';
import Dashboard from './pages/Dashboard';
import KycModal from './pages/KycModal';

const NAV = [
  { id: 'chat', icon: '💬', label: 'Worker Bot' },
  { id: 'dashboard', icon: '📊', label: 'Dashboard' },
];

export default function App() {
  const [activeView, setActiveView] = useState('chat');
  const [isKycVerified, setIsKycVerified] = useState(false);

  return (
    <>
      {!isKycVerified && <KycModal onVerify={() => setIsKycVerified(true)} />}
      <div className="app-shell" style={{ filter: !isKycVerified ? 'blur(4px)' : 'none', transition: 'filter 0.3s' }}>
      {/* Sidebar */}
      <nav className="sidebar">
        <div className="sidebar-logo">🛡️</div>
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
        {activeView === 'dashboard' && <Dashboard />}
      </div>
    </div>
    </>
  );
}
