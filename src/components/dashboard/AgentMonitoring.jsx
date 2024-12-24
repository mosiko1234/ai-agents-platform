import React, { useState, useEffect } from 'react';
import { LineChart, XAxis, YAxis, Tooltip, Legend, Line } from 'recharts';

const AgentMonitoring = ({ agentId }) => {
  const [metrics, setMetrics] = useState(null);
  const [logs, setLogs] = useState([]);
  const [timeRange, setTimeRange] = useState('24h');

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 60000);
    return () => clearInterval(interval);
  }, [agentId, timeRange]);

  const fetchData = async () => {
    const [metricsRes, logsRes] = await Promise.all([
      fetch(`/api/v1/agents/${agentId}/metrics?timeRange=${timeRange}`),
      fetch(`/api/v1/agents/${agentId}/logs?timeRange=${timeRange}`)
    ]);
    
    setMetrics(await metricsRes.json());
    setLogs(await logsRes.json());
  };

  if (!metrics) return null;

  return (
    <div className="space-y-6">
      {/* Time Range Selector */}
      <div className="flex justify-end">
        <select 
          value={timeRange}
          onChange={(e) => setTimeRange(e.target.value)}
          className="p-2 border rounded"
        >
          <option value="1h">שעה אחרונה</option>
          <option value="24h">24 שעות</option>
          <option value="7d">שבוע</option>
          <option value="30d">חודש</option>
        </select>
      </div>

      {/* Performance Metrics */}
      <div className="bg-white rounded-lg shadow p-4">
        <h3 className="text-lg font-semibold mb-4">מדדי ביצועים</h3>
        <LineChart
          width={800}
          height={300}
          data={metrics.history}
          margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
        >
          <XAxis dataKey="timestamp" />
          <YAxis />
          <Tooltip />
          <Legend />
          <Line type="monotone" dataKey="requests" name="פניות" stroke="#8884d8" />
          <Line type="monotone" dataKey="errors" name="שגיאות" stroke="#ff4d4f" />
          <Line type="monotone" dataKey="responseTime" name="זמן תגובה" stroke="#82ca9d" />
        </LineChart>
      </div>

      {/* System Resources */}
      <div className="grid grid-cols-3 gap-4">
        <MetricCard
          title="CPU"
          value={`${metrics.cpu}%`}
          trend={metrics.cpuTrend}
          icon={
            <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z" />
            </svg>
          }
        />
        <MetricCard
          title="Memory"
          value={`${metrics.memory}MB`}
          trend={metrics.memoryTrend}
          icon={
            <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
            </svg>
          }
        />
        <MetricCard
          title="Active Threads"
          value={metrics.threads}
          trend={metrics.threadsTrend}
          icon={
            <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
          }
        />
      </div>

      {/* Recent Logs */}
      <div className="bg-white rounded-lg shadow p-4">
        <h3 className="text-lg font-semibold mb-4">לוגים אחרונים</h3>
        <div className="space-y-2">
          {logs.map((log) => (
            <LogEntry key={log.id} log={log} />
          ))}
        </div>
      </div>
    </div>
  );
};

const MetricCard = ({ title, value, trend, icon }) => (
  <div className="bg-white rounded-lg shadow p-4">
    <div className="flex justify-between items-center mb-2">
      <div className="flex items-center space-x-2">
        {icon}
        <h4 className="text-gray-600">{title}</h4>
      </div>
      <TrendIndicator value={trend} />
    </div>
    <p className="text-2xl font-bold">{value}</p>
  </div>
);

const TrendIndicator = ({ value }) => {
  if (value > 0) {
    return (
      <svg className="w-4 h-4 text-green-500" viewBox="0 0 20 20" fill="currentColor">
        <path fillRule="evenodd" d="M3.293 9.707a1 1 0 010-1.414l6-6a1 1 0 011.414 0l6 6a1 1 0 01-1.414 1.414L11 5.414V17a1 1 0 11-2 0V5.414L4.707 9.707a1 1 0 01-1.414 0z" clipRule="evenodd" />
      </svg>
    );
  }
  return (
    <svg className="w-4 h-4 text-red-500" viewBox="0 0 20 20" fill="currentColor">
      <path fillRule="evenodd" d="M16.707 10.293a1 1 0 010 1.414l-6 6a1 1 0 01-1.414 0l-6-6a1 1 0 111.414-1.414L9 14.586V3a1 1 0 012 0v11.586l4.293-4.293a1 1 0 011.414 0z" clipRule="evenodd" />
    </svg>
  );
};

const LogEntry = ({ log }) => {
  const levelColors = {
    error: 'text-red-600 bg-red-50',
    warn: 'text-yellow-600 bg-yellow-50',
    info: 'text-blue-600 bg-blue-50',
    debug: 'text-gray-600 bg-gray-50'
  };

  return (
    <div className={`p-2 rounded ${levelColors[log.level]}`}>
      <div className="flex justify-between">
        <span className="font-mono text-sm">{new Date(log.timestamp).toLocaleString()}</span>
        <span className="font-medium">{log.level.toUpperCase()}</span>
      </div>
      <p className="mt-1">{log.message}</p>
      {log.metadata && (
        <pre className="mt-2 text-xs bg-black bg-opacity-5 p-2 rounded">
          {JSON.stringify(log.metadata, null, 2)}
        </pre>
      )}
    </div>
  );
};

export default AgentMonitoring;