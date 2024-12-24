import React, { useState, useEffect } from 'react';
import { LineChart, XAxis, YAxis, Tooltip, Legend, Line } from 'recharts';

const SystemHistory = () => {
  const [history, setHistory] = useState([]);
  const [filters, setFilters] = useState({
    dateRange: '30d',
    eventType: 'all',
    agentId: 'all',
    severity: 'all'
  });
  const [stats, setStats] = useState(null);
  const [selectedEvent, setSelectedEvent] = useState(null);

  useEffect(() => {
    fetchHistory();
  }, [filters]);

  const fetchHistory = async () => {
    const response = await fetch(
      `/api/v1/system/history?${new URLSearchParams(filters)}`
    );
    const data = await response.json();
    setHistory(data.events);
    setStats(data.stats);
  };

  return (
    <div className="bg-white rounded-lg shadow p-6">
      {/* Header & Filters */}
      <div className="flex justify-between items-start mb-6">
        <div>
          <h2 className="text-xl font-bold">היסטוריית מערכת</h2>
          <p className="text-gray-500">צפייה בפעילות והתראות מערכת</p>
        </div>
        <div className="flex gap-4">
          <select
            value={filters.dateRange}
            onChange={(e) => setFilters({ ...filters, dateRange: e.target.value })}
            className="border rounded p-2"
          >
            <option value="24h">24 שעות אחרונות</option>
            <option value="7d">שבוע אחרון</option>
            <option value="30d">30 ימים אחרונים</option>
            <option value="custom">טווח מותאם</option>
          </select>
          <select
            value={filters.eventType}
            onChange={(e) => setFilters({ ...filters, eventType: e.target.value })}
            className="border rounded p-2"
          >
            <option value="all">כל סוגי האירועים</option>
            <option value="system">אירועי מערכת</option>
            <option value="agent">אירועי סוכן</option>
            <option value="security">אירועי אבטחה</option>
          </select>
          <select
            value={filters.severity}
            onChange={(e) => setFilters({ ...filters, severity: e.target.value })}
            className="border rounded p-2"
          >
            <option value="all">כל רמות החומרה</option>
            <option value="info">מידע</option>
            <option value="warning">אזהרה</option>
            <option value="error">שגיאה</option>
            <option value="critical">קריטי</option>
          </select>
        </div>
      </div>

      {/* Statistics Overview */}
      {stats && (
        <div className="grid grid-cols-4 gap-4 mb-6">
          <StatCard
            title="סה״כ אירועים"
            value={stats.totalEvents}
            trend={stats.eventsTrend}
          />
          <StatCard
            title="שגיאות"
            value={stats.errorCount}
            trend={stats.errorsTrend}
            trendColor={stats.errorsTrend > 0 ? 'red' : 'green'}
          />
          <StatCard
            title="זמן תגובה ממוצע"
            value={`${stats.avgResponseTime}ms`}
            trend={stats.responseTrend}
          />
          <StatCard
            title="שיעור הצלחה"
            value={`${stats.successRate}%`}
            trend={stats.successTrend}
          />
        </div>
      )}

      {/* Activity Timeline */}
      <div className="mb-6">
        <h3 className="font-semibold mb-4">פעילות לאורך זמן</h3>
        <LineChart
          width={800}
          height={200}
          data={stats?.timeline || []}
          margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
        >
          <XAxis dataKey="time" />
          <YAxis />
          <Tooltip />
          <Legend />
          <Line type="monotone" dataKey="events" name="אירועים" stroke="#8884d8" />
          <Line type="monotone" dataKey="errors" name="שגיאות" stroke="#ff4d4f" />
        </LineChart>
      </div>

      {/* Events List */}
      <div className="space-y-4">
        {history.map((event) => (
          <EventCard
            key={event.id}
            event={event}
            isSelected={selectedEvent?.id === event.id}
            onClick={() => setSelectedEvent(event)}
          />
        ))}
      </div>

      {/* Event Details Modal */}
      {selectedEvent && (
        <EventDetailsModal
          event={selectedEvent}
          onClose={() => setSelectedEvent(null)}
        />
      )}
    </div>
  );
};

const StatCard = ({ title, value, trend, trendColor = 'blue' }) => (
  <div className="bg-gray-50 p-4 rounded-lg">
    <div className="flex justify-between items-center mb-2">
      <span className="text-gray-600">{title}</span>
      <TrendIndicator value={trend} color={trendColor} />
    </div>
    <div className="text-2xl font-bold">{value}</div>
  </div>
);

const TrendIndicator = ({ value, color }) => {
  if (value === 0) return null;
  
  const colors = {
    red: 'text-red-500',
    green: 'text-green-500',
    blue: 'text-blue-500'
  };

  return (
    <div className={`flex items-center ${colors[color]}`}>
      {value > 0 ? (
        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 15l7-7 7 7" />
        </svg>
      ) : (
        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      )}
      <span className="ml-1">{Math.abs(value)}%</span>
    </div>
  );
};

const EventCard = ({ event, isSelected, onClick }) => {
  const severityColors = {
    info: 'bg-blue-50 border-blue-200',
    warning: 'bg-yellow-50 border-yellow-200',
    error: 'bg-red-50 border-red-200',
    critical: 'bg-red-100 border-red-300'
  };

  return (
    <div
      className={`p-4 rounded-lg border cursor-pointer ${
        severityColors[event.severity]
      } ${isSelected ? 'ring-2 ring-blue-500' : ''}`}
      onClick={onClick}
    >
      <div className="flex justify-between items-start">
        <div>
          <div className="flex items-center gap-2">
            <span className="font-medium">{event.type}</span>
            <span className={`text-sm px-2 py-1 rounded ${
              severityColors[event.severity]
            }`}>
              {event.severity}
            </span>
          </div>
          <p className="text-sm text-gray-600 mt-1">{event.message}</p>
        </div>
        <span className="text-sm text-gray-500">
          {new Date(event.timestamp).toLocaleString()}
        </span>
      </div>
    </div>
  );
};

const EventDetailsModal = ({ event, onClose }) => (
  <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4">
    <div className="bg-white rounded-lg p-6 w-full max-w-2xl">
      <div className="flex justify-between items-start mb-4">
        <h3 className="text-lg font-semibold">פרטי אירוע</h3>
        <button onClick={onClose} className="text-gray-500 hover:text-gray-700">
          <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>
      
      <div className="grid grid-cols-2 gap-4 mb-4">
        <DetailField label="סוג" value={event.type} />
        <DetailField label="חומרה" value={event.severity} />
        <DetailField label="תאריך" value={new Date(event.timestamp).toLocaleString()} />
        <DetailField label="מזהה" value={event.id} />
      </div>

      <div className="mb-4">
        <label className="block text-sm font-medium text-gray-700 mb-1">הודעה</label>
        <p className="text-gray-900">{event.message}</p>
      </div>

      {event.details && (
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-1">פרטים נוספים</label>
          <pre className="bg-gray-50 p-3 rounded text-sm overflow-auto">
            {JSON.stringify(event.details, null, 2)}
          </pre>
        </div>
      )}

      {event.stackTrace && (
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Stack Trace</label>
          <pre className="bg-gray-50 p-3 rounded text-sm overflow-auto">
            {event.stackTrace}
          </pre>
        </div>
      )}
    </div>
  </div>
);

const DetailField = ({ label, value }) => (
  <div>
    <label className="block text-sm font-medium text-gray-700">{label}</label>
    <p className="mt-1">{value}</p>
  </div>
);

export default SystemHistory;