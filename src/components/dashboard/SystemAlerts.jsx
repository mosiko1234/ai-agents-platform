import React, { useState, useEffect } from 'react';

const SystemAlerts = () => {
  const [alerts, setAlerts] = useState([]);
  const [selectedFilter, setSelectedFilter] = useState('all');

  useEffect(() => {
    fetchAlerts();
    const interval = setInterval(fetchAlerts, 30000);
    return () => clearInterval(interval);
  }, [selectedFilter]);

  const fetchAlerts = async () => {
    const response = await fetch(`/api/v1/alerts?filter=${selectedFilter}`);
    const data = await response.json();
    setAlerts(data);
  };

  const markAsRead = async (alertId) => {
    await fetch(`/api/v1/alerts/${alertId}/read`, { method: 'POST' });
    fetchAlerts();
  };

  const markAllAsRead = async () => {
    await fetch('/api/v1/alerts/read-all', { method: 'POST' });
    fetchAlerts();
  };

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-xl font-bold">התראות מערכת</h2>
        <div className="flex gap-4">
          <select
            value={selectedFilter}
            onChange={(e) => setSelectedFilter(e.target.value)}
            className="border rounded p-2"
          >
            <option value="all">הכל</option>
            <option value="unread">לא נקרא</option>
            <option value="critical">קריטי</option>
            <option value="warning">אזהרה</option>
            <option value="info">מידע</option>
          </select>
          <button
            onClick={markAllAsRead}
            className="px-4 py-2 text-gray-600 border rounded hover:bg-gray-50"
          >
            סמן הכל כנקרא
          </button>
        </div>
      </div>

      <div className="space-y-4">
        {alerts.map((alert) => (
          <AlertCard 
            key={alert.id} 
            alert={alert} 
            onMarkRead={markAsRead}
          />
        ))}
        {alerts.length === 0 && (
          <div className="text-center text-gray-500 py-8">
            אין התראות חדשות
          </div>
        )}
      </div>
    </div>
  );
};

const AlertCard = ({ alert, onMarkRead }) => {
  const severityStyles = {
    critical: 'border-red-500 bg-red-50',
    warning: 'border-yellow-500 bg-yellow-50',
    info: 'border-blue-500 bg-blue-50'
  };

  const severityIcons = {
    critical: (
      <svg className="w-6 h-6 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
      </svg>
    ),
    warning: (
      <svg className="w-6 h-6 text-yellow-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    ),
    info: (
      <svg className="w-6 h-6 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    )
  };

  return (
    <div className={`p-4 border-r-4 rounded-lg ${severityStyles[alert.severity]} ${!alert.read ? 'border-r-4' : ''}`}>
      <div className="flex items-start gap-4">
        {severityIcons[alert.severity]}
        <div className="flex-1">
          <div className="flex justify-between items-start">
            <h3 className="font-semibold">{alert.title}</h3>
            <span className="text-sm text-gray-500">
              {new Date(alert.timestamp).toLocaleString()}
            </span>
          </div>
          <p className="mt-1">{alert.message}</p>
          {alert.details && (
            <pre className="mt-2 text-sm bg-black bg-opacity-5 p-2 rounded">
              {JSON.stringify(alert.details, null, 2)}
            </pre>
          )}
          <div className="mt-2 flex justify-between items-center">
            <div className="flex gap-2">
              <span className="text-sm text-gray-500">
                {alert.source} • {alert.category}
              </span>
            </div>
            {!alert.read && (
              <button
                onClick={() => onMarkRead(alert.id)}
                className="text-sm text-gray-500 hover:text-gray-700"
              >
                סמן כנקרא
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default SystemAlerts;