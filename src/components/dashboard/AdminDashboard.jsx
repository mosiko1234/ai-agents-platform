import React, { useState, useEffect } from 'react';
import { LineChart, XAxis, YAxis, Tooltip, Legend, Line } from 'recharts';

const AdminDashboard = () => {
  const [stats, setStats] = useState({
    totalRequests: 0,
    activeAgents: 0,
    errorRate: 0,
    responseTime: 0
  });
  const [alerts, setAlerts] = useState([]);
  const [selectedAgent, setSelectedAgent] = useState(null);

  useEffect(() => {
    fetchStats();
    fetchAlerts();
  }, []);

  const fetchStats = async () => {
    try {
      const response = await fetch('/api/v1/stats');
      const data = await response.json();
      setStats(data);
    } catch (error) {
      console.error('Error fetching stats:', error);
    }
  };

  const fetchAlerts = async () => {
    try {
      const response = await fetch('/api/v1/alerts');
      const data = await response.json();
      setAlerts(data);
    } catch (error) {
      console.error('Error fetching alerts:', error);
    }
  };

  return (
    <div className="p-6 bg-gray-50 min-h-screen">
      <header className="mb-8">
        <h1 className="text-3xl font-bold">דשבורד ניהול</h1>
      </header>

      {/* Stats Overview */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
        <StatCard
          title="פניות"
          value={stats.totalRequests}
          icon={
            <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
            </svg>
          }
        />
        <StatCard
          title="סוכנים פעילים"
          value={stats.activeAgents}
          icon={
            <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
            </svg>
          }
        />
        <StatCard
          title="אחוז שגיאות"
          value={`${(stats.errorRate * 100).toFixed(1)}%`}
          icon={
            <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          }
        />
        <StatCard
          title="זמן תגובה ממוצע"
          value={`${stats.responseTime.toFixed(2)}s`}
          icon={
            <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          }
        />
      </div>

      {/* Performance Graph */}
      <div className="bg-white p-4 rounded-lg shadow mb-8">
        <h2 className="text-xl font-semibold mb-4">ביצועי מערכת</h2>
        <div className="h-96">
          <LineChart
            width={800}
            height={300}
            data={performanceData}
            margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
          >
            <XAxis dataKey="name" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Line type="monotone" dataKey="requests" stroke="#8884d8" />
            <Line type="monotone" dataKey="errors" stroke="#82ca9d" />
          </LineChart>
        </div>
      </div>

      {/* Recent Alerts */}
      <div className="bg-white p-4 rounded-lg shadow mb-8">
        <h2 className="text-xl font-semibold mb-4">התראות אחרונות</h2>
        <div className="space-y-4">
          {alerts.map((alert, index) => (
            <AlertCard
              key={index}
              severity={alert.severity}
              title={alert.title}
              description={alert.description}
              timestamp={alert.timestamp}
            />
          ))}
        </div>
      </div>

      {/* Agent Management */}
      <div className="bg-white p-4 rounded-lg shadow">
        <h2 className="text-xl font-semibold mb-4">ניהול סוכנים</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <AgentCard
            name="שמעון"
            status="active"
            type="legal"
            lastUpdate="2024-01-23T10:30:00"
            onSelect={() => setSelectedAgent('shimon')}
          />
          {/* Add more agent cards here */}
        </div>
      </div>
    </div>
  );
};

const StatCard = ({ title, value, icon }) => (
  <div className="bg-white p-4 rounded-lg shadow">
    <div className="flex items-center justify-between mb-2">
      <h3 className="text-lg font-medium text-gray-700">{title}</h3>
      {icon}
    </div>
    <p className="text-2xl font-bold">{value}</p>
  </div>
);

const AlertCard = ({ severity, title, description, timestamp }) => (
  <div className={`p-4 rounded-lg border ${getAlertStyle(severity)}`}>
    <div className="flex items-center">
      <svg className="w-6 h-6 ml-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
      </svg>
      <div>
        <h4 className="font-semibold">{title}</h4>
        <p className="text-sm">{description}</p>
        <span className="text-xs text-gray-500">{new Date(timestamp).toLocaleString()}</span>
      </div>
    </div>
  </div>
);

const AgentCard = ({ name, status, type, lastUpdate, onSelect }) => (
  <div 
    className="bg-gray-50 p-4 rounded-lg border cursor-pointer hover:shadow-md transition-shadow"
    onClick={onSelect}
  >
    <h3 className="font-semibold text-lg">{name}</h3>
    <div className="mt-2 space-y-1">
      <p className="text-sm">סטטוס: {status}</p>
      <p className="text-sm">סוג: {type}</p>
      <p className="text-sm">עדכון אחרון: {new Date(lastUpdate).toLocaleString()}</p>
    </div>
  </div>
);

const getAlertStyle = (severity) => {
  switch (severity) {
    case 'critical': return 'border-red-500 bg-red-50';
    case 'warning': return 'border-yellow-500 bg-yellow-50';
    default: return 'border-blue-500 bg-blue-50';
  }
};

const performanceData = [
  { name: '10:00', requests: 40, errors: 2 },
  { name: '11:00', requests: 30, errors: 1 },
  { name: '12:00', requests: 45, errors: 3 },
  { name: '13:00', requests: 50, errors: 2 },
  { name: '14:00', requests: 35, errors: 1 },
];

export default AdminDashboard;