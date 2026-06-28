import React, { useState } from 'react';
import WorkerChat from './pages/WorkerChat';
import Dashboard from './pages/Dashboard';

const NAV = [
  { id: 'chat', icon: '💬', label: 'Worker Bot' },
  { id: 'dashboard', icon: '📊', label: 'Dashboard' },
];

export default function App() {
  const [activeView, setActiveView] = useState('chat');

  return (
    <div className="app-shell">
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
  );
}
