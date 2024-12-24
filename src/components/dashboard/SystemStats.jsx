import React, { useState, useEffect } from 'react';
import { LineChart, XAxis, YAxis, Tooltip, Legend, Line } from 'recharts';

const SystemStats = () => {
  const [stats, setStats] = useState({
    usageStats: [],
    agentStats: [],
    platformStats: {},
    topQueries: []
  });
  const [timeframe, setTimeframe] = useState('24h');

  useEffect(() => {
    fetchStats();
    const interval = setInterval(fetchStats, 60000);
    return () => clearInterval(interval);
  }, [timeframe]);

  const fetchStats = async () => {
    const response = await fetch(`/api/v1/stats?timeframe=${timeframe}`);
    const data = await response.json();
    setStats(data);
  };

  return (
    <div className="space-y-6">
      {/* Time Range Selector */}
      <div className="flex justify-between items-center">
        <h2 className="text-xl font-bold">סטטיסטיקות מערכת</h2>
        <select
          value={timeframe}
          onChange={(e) => setTimeframe(e.target.value)}
          className="border rounded p-2"
        >
          <option value="1h">שעה אחרונה</option>
          <option value="24h">24 שעות</option>
          <option value="7d">שבוע אחרון</option>
          <option value="30d">חודש אחרון</option>
        </select>
      </div>

      {/* Usage Graph */}
      <div className="bg-white rounded-lg shadow p-4">
        <h3 className="text-lg font-semibold mb-4">שימוש במערכת</h3>
        <LineChart
          width={800}
          height={300}
          data={stats.usageStats}
          margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
        >
          <XAxis dataKey="timestamp" />
          <YAxis />
          <Tooltip />
          <Legend />
          <Line type="monotone" dataKey="requests" name="פניות" stroke="#8884d8" />
          <Line type="monotone" dataKey="activeUsers" name="משתמשים פעילים" stroke="#82ca9d" />
        </LineChart>
      </div>

      {/* Platform Stats */}
      <div className="grid grid-cols-4 gap-4">
        <StatsCard
          title="זמינות"
          value={`${stats.platformStats.uptime}%`}
          icon={
            <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
          }
        />
        <StatsCard
          title="זמן תגובה ממוצע"
          value={`${stats.platformStats.avgResponseTime}ms`}
          icon={
            <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          }
        />
        <StatsCard
          title="סוכנים פעילים"
          value={stats.platformStats.activeAgents}
          icon={
            <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
            </svg>
          }
        />
        <StatsCard
          title="אחוז הצלחה"
          value={`${stats.platformStats.successRate}%`}
          icon={
            <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          }
        />
      </div>

      {/* Agent Performance */}
      <div className="grid grid-cols-2 gap-6">
        <div className="bg-white rounded-lg shadow p-4">
          <h3 className="text-lg font-semibold mb-4">ביצועי סוכנים</h3>
          <div className="space-y-4">
            {stats.agentStats.map((agent) => (
              <AgentPerformanceRow key={agent.id} agent={agent} />
            ))}
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-4">
          <h3 className="text-lg font-semibold mb-4">שאלות נפוצות</h3>
          <div className="space-y-4">
            {stats.topQueries.map((query, index) => (
              <TopQueryRow key={index} query={query} rank={index + 1} />
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

const StatsCard = ({ title, value, icon }) => (
  <div className="bg-white rounded-lg shadow p-4">
    <div className="flex items-center justify-between mb-2">
      <h4 className="text-gray-600">{title}</h4>
      {icon}
    </div>
    <p className="text-2xl font-bold">{value}</p>
  </div>
);

const AgentPerformanceRow = ({ agent }) => (
  <div className="flex items-center justify-between">
    <div className="flex items-center space-x-2">
      <span className="font-medium">{agent.name}</span>
      <span className={`px-2 py-1 rounded text-sm ${
        agent.status === 'active' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
      }`}>
        {agent.status}
      </span>
    </div>
    <div className="flex items-center space-x-4">
      <span>{agent.requestCount} פניות</span>
      <span>{agent.successRate}% הצלחה</span>
      <span>{agent.avgResponseTime}ms</span>
    </div>
  </div>
);

const TopQueryRow = ({ query, rank }) => (
  <div className="flex items-center justify-between">
    <div className="flex items-center space-x-2">
      <span className="font-bold text-gray-500">#{rank}</span>
      <span>{query.text}</span>
    </div>
    <div className="text-gray-500">
      {query.count} פעמים
    </div>
  </div>
);

export default SystemStats;