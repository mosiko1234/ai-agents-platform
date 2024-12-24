import React, { useState, useEffect } from 'react';
import { LineChart, XAxis, YAxis, Tooltip, Legend, Line } from 'recharts';

const SystemMonitoring = () => {
  const [metrics, setMetrics] = useState(null);
  const [healthStatus, setHealthStatus] = useState({});
  const [selectedService, setSelectedService] = useState(null);
  const [autoRefresh, setAutoRefresh] = useState(true);

  useEffect(() => {
    fetchInitialData();
    const interval = setInterval(fetchMetrics, 5000);
    return () => clearInterval(interval);
  }, []);

  const fetchInitialData = async () => {
    await Promise.all([
      fetchMetrics(),
      fetchHealthStatus()
    ]);
  };

  const fetchMetrics = async () => {
    if (!autoRefresh) return;
    const response = await fetch('/api/v1/system/metrics');
    const data = await response.json();
    setMetrics(data);
  };

  const fetchHealthStatus = async () => {
    const response = await fetch('/api/v1/system/health');
    const data = await response.json();
    setHealthStatus(data);
  };

  return (
    <div className="bg-white rounded-lg shadow p-6">
      {/* Header */}
      <div className="flex justify-between items-center mb-6">
        <div>
          <h2 className="text-xl font-bold">ניטור מערכת</h2>
          <p className="text-gray-500">מצב המערכת בזמן אמת</p>
        </div>
        <div className="flex gap-4 items-center">
          <label className="flex items-center">
            <input
              type="checkbox"
              checked={autoRefresh}
              onChange={(e) => setAutoRefresh(e.target.checked)}
              className="ml-2"
            />
            <span>רענון אוטומטי</span>
          </label>
          <button
            onClick={fetchInitialData}
            className="px-4 py-2 text-blue-500 border border-blue-500 rounded hover:bg-blue-50"
          >
            רענן
          </button>
        </div>
      </div>

      {/* System Health Overview */}
      <div className="grid grid-cols-4 gap-4 mb-6">
        <HealthCard
          title="CPU"
          value={`${metrics?.cpu.usage}%`}
          status={getHealthStatus(metrics?.cpu.usage, 80, 90)}
          detail={`${metrics?.cpu.cores} Cores`}
        />
        <HealthCard
          title="Memory"
          value={`${metrics?.memory.used}/${metrics?.memory.total}GB`}
          status={getHealthStatus(metrics?.memory.percentage, 80, 90)}
          detail={`${metrics?.memory.free}GB Free`}
        />
        <HealthCard
          title="Response Time"
          value={`${metrics?.responseTime}ms`}
          status={getHealthStatus(metrics?.responseTime, 1000, 2000, true)}
          detail={`Avg last 5m`}
        />
        <HealthCard
          title="Error Rate"
          value={`${metrics?.errorRate}%`}
          status={getHealthStatus(metrics?.errorRate, 5, 10, true)}
          detail={`Last 5m`}
        />
      </div>

      {/* Performance Graphs */}
      <div className="grid grid-cols-2 gap-6 mb-6">
        <div className="bg-gray-50 p-4 rounded-lg">
          <h3 className="font-semibold mb-4">שימוש במשאבים</h3>
          <LineChart
            width={400}
            height={200}
            data={metrics?.resourceHistory || []}
          >
            <XAxis dataKey="time" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Line type="monotone" dataKey="cpu" name="CPU" stroke="#8884d8" />
            <Line type="monotone" dataKey="memory" name="Memory" stroke="#82ca9d" />
          </LineChart>
        </div>

        <div className="bg-gray-50 p-4 rounded-lg">
          <h3 className="font-semibold mb-4">ביצועי מערכת</h3>
          <LineChart
            width={400}
            height={200}
            data={metrics?.performanceHistory || []}
          >
            <XAxis dataKey="time" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Line type="monotone" dataKey="responseTime" name="Response Time" stroke="#8884d8" />
            <Line type="monotone" dataKey="requests" name="Requests" stroke="#82ca9d" />
          </LineChart>
        </div>
      </div>

      {/* Services Status */}
      <div className="mb-6">
        <h3 className="font-semibold mb-4">סטטוס שירותים</h3>
        <div className="grid grid-cols-3 gap-4">
          {Object.entries(healthStatus).map(([service, status]) => (
            <ServiceCard
              key={service}
              service={service}
              status={status}
              isSelected={selectedService === service}
              onClick={() => setSelectedService(service)}
            />
          ))}
        </div>
      </div>

      {/* Active Requests */}
      <div className="bg-gray-50 p-4 rounded-lg">
        <h3 className="font-semibold mb-4">בקשות פעילות</h3>
        <div className="space-y-2">
          {metrics?.activeRequests.map((request) => (
            <RequestCard key={request.id} request={request} />
          ))}
          {metrics?.activeRequests.length === 0 && (
            <p className="text-gray-500 text-center py-4">אין בקשות פעילות</p>
          )}
        </div>
      </div>
    </div>
  );
};

const HealthCard = ({ title, value, status, detail }) => {
  const statusColors = {
    healthy: 'text-green-500',
    warning: 'text-yellow-500',
    critical: 'text-red-500'
  };

  return (
    <div className="bg-gray-50 p-4 rounded-lg">
      <div className="flex justify-between items-center mb-2">
        <span className="text-gray-600">{title}</span>
        <div className={statusColors[status]}>
          {status === 'healthy' && (
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
          )}
          {status === 'warning' && (
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          )}
          {status === 'critical' && (
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          )}
        </div>
      </div>
      <div className="text-2xl font-bold mb-1">{value}</div>
      <div className="text-sm text-gray-500">{detail}</div>
    </div>
  );
};

const ServiceCard = ({ service, status, isSelected, onClick }) => {
  const statusColors = {
    healthy: 'border-green-500 bg-green-50',
    warning: 'border-yellow-500 bg-yellow-50',
    critical: 'border-red-500 bg-red-50'
  };

  return (
    <div
      className={`p-4 rounded-lg border cursor-pointer ${statusColors[status.health]} ${
        isSelected ? 'ring-2 ring-blue-500' : ''
      }`}
      onClick={onClick}
    >
      <div className="flex justify-between items-center">
        <h4 className="font-medium">{service}</h4>
        <span className="text-sm">
          {status.uptime}
        </span>
      </div>
      <div className="text-sm mt-2">
        <div>Latency: {status.latency}ms</div>
        <div>Load: {status.load}</div>
      </div>
    </div>
  );
};

const RequestCard = ({ request }) => (
  <div className="bg-white p-3 rounded border">
    <div className="flex justify-between items-start">
      <div>
        <div className="font-medium">{request.endpoint}</div>
        <div className="text-sm text-gray-500">
          {request.method} • {request.duration}ms
        </div>
      </div>
      <div className="text-sm">
        {new Date(request.startTime).toLocaleTimeString()}
      </div>
    </div>
  </div>
);

const getHealthStatus = (value, warningThreshold, criticalThreshold, inverse = false) => {
  if (!value) return 'healthy';
  
  if (inverse) {
    if (value >= criticalThreshold) return 'critical';
    if (value >= warningThreshold) return 'warning';
    return 'healthy';
  }
  
  if (value >= criticalThreshold) return 'critical';
  if (value >= warningThreshold) return 'warning';
  return 'healthy';
};

export default SystemMonitoring;