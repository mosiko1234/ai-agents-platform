import React, { useState } from 'react';
import AdminDashboard from './AdminDashboard';
import AgentDetails from './AgentDetails';
import AgentSettings from './AgentSettings';
import KnowledgeManagement from './KnowledgeManagement';
import SystemMonitoring from './SystemMonitoring';
import SystemHistory from './SystemHistory';
import AnalyticsReports from './AnalyticsReports';
import BackupRestore from './BackupRestore';
import ApiSettings from './ApiSettings';
import UserManagement from './UserManagement';

const MainDashboard = () => {
  const [currentSection, setCurrentSection] = useState('overview');
  const [selectedAgent, setSelectedAgent] = useState(null);

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Navigation Header */}
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex justify-between items-center">
            <h1 className="text-2xl font-bold text-gray-900">מערכת ניהול AI Agents</h1>
            <div className="flex items-center space-x-4">
              <div className="flex items-center">
                <div className="w-2 h-2 rounded-full bg-green-500 ml-2"></div>
                <span className="text-sm text-gray-600">מחובר</span>
              </div>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex gap-8">
          {/* Sidebar Navigation */}
          <nav className="w-64 bg-white rounded-lg shadow p-4 space-y-1">
            <NavItem
              id="overview"
              label="סקירה כללית"
              icon={<DashboardIcon />}
              selected={currentSection === 'overview'}
              onClick={setCurrentSection}
            />
            <NavItem
              id="agents"
              label="ניהול סוכנים"
              icon={<AgentsIcon />}
              selected={currentSection === 'agents'}
              onClick={setCurrentSection}
            />
            <NavItem
              id="knowledge"
              label="מאגר ידע"
              icon={<KnowledgeIcon />}
              selected={currentSection === 'knowledge'}
              onClick={setCurrentSection}
            />
            <NavItem
              id="monitoring"
              label="ניטור מערכת"
              icon={<MonitoringIcon />}
              selected={currentSection === 'monitoring'}
              onClick={setCurrentSection}
            />
            <NavItem
              id="analytics"
              label="אנליטיקס ודוחות"
              icon={<AnalyticsIcon />}
              selected={currentSection === 'analytics'}
              onClick={setCurrentSection}
            />
            <NavItem
              id="history"
              label="היסטוריית מערכת"
              icon={<HistoryIcon />}
              selected={currentSection === 'history'}
              onClick={setCurrentSection}
            />
            <NavItem
              id="backup"
              label="גיבוי ושחזור"
              icon={<BackupIcon />}
              selected={currentSection === 'backup'}
              onClick={setCurrentSection}
            />
            <NavItem
              id="settings"
              label="הגדרות API"
              icon={<SettingsIcon />}
              selected={currentSection === 'settings'}
              onClick={setCurrentSection}
            />
            <NavItem
              id="users"
              label="ניהול משתמשים"
              icon={<UsersIcon />}
              selected={currentSection === 'users'}
              onClick={setCurrentSection}
            />
          </nav>

          {/* Main Content Area */}
          <main className="flex-1">
            {currentSection === 'overview' && <AdminDashboard />}
            {currentSection === 'agents' && (
              selectedAgent ? 
                <AgentDetails agentId={selectedAgent} onBack={() => setSelectedAgent(null)} /> :
                <AgentSettings />
            )}
            {currentSection === 'knowledge' && <KnowledgeManagement />}
            {currentSection === 'monitoring' && <SystemMonitoring />}
            {currentSection === 'analytics' && <AnalyticsReports />}
            {currentSection === 'history' && <SystemHistory />}
            {currentSection === 'backup' && <BackupRestore />}
            {currentSection === 'settings' && <ApiSettings />}
            {currentSection === 'users' && <UserManagement />}
          </main>
        </div>
      </div>
    </div>
  );
};

const NavItem = ({ id, label, icon, selected, onClick }) => (
  <button
    onClick={() => onClick(id)}
    className={`w-full flex items-center px-3 py-2 rounded-lg text-sm ${
      selected 
        ? 'bg-blue-50 text-blue-700'
        : 'text-gray-700 hover:bg-gray-50'
    }`}
  >
    <span className="mr-2">{icon}</span>
    {label}
  </button>
);

// Simple Icon Components
const DashboardIcon = () => (
  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" />
  </svg>
);

const AgentsIcon = () => (
  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
  </svg>
);

const KnowledgeIcon = () => (
  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
  </svg>
);

const MonitoringIcon = () => (
  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
  </svg>
);

const AnalyticsIcon = () => (
  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 8v8m-4-5v5m-4-2v2m-2 4h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
  </svg>
);

const HistoryIcon = () => (
  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
  </svg>
);

const BackupIcon = () => (
  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7v8a2 2 0 002 2h6M8 7V5a2 2 0 012-2h4.586a1 1 0 01.707.293l4.414 4.414a1 1 0 01.293.707V15a2 2 0 01-2 2h-2M8 7H6a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2v-2" />
  </svg>
);

const SettingsIcon = () => (
  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
  </svg>
);

const UsersIcon = () => (
  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
  </svg>
);

export default MainDashboard;