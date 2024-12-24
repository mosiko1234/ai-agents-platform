import React, { useState, useEffect } from 'react';
import { LineChart, XAxis, YAxis, Tooltip, Legend, Line, BarChart, Bar, PieChart, Pie } from 'recharts';

const AnalyticsReports = () => {
  const [timeframe, setTimeframe] = useState('30d');
  const [selectedReport, setSelectedReport] = useState('overview');
  const [reportData, setReportData] = useState(null);
  const [isExporting, setIsExporting] = useState(false);

  useEffect(() => {
    fetchReportData();
  }, [timeframe, selectedReport]);

  const fetchReportData = async () => {
    const response = await fetch(
      `/api/v1/analytics/${selectedReport}?timeframe=${timeframe}`
    );
    const data = await response.json();
    setReportData(data);
  };

  const exportReport = async () => {
    setIsExporting(true);
    try {
      const response = await fetch(
        `/api/v1/analytics/${selectedReport}/export?timeframe=${timeframe}`
      );
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `report-${selectedReport}-${timeframe}.xlsx`;
      a.click();
    } finally {
      setIsExporting(false);
    }
  };

  return (
    <div className="bg-white rounded-lg shadow p-6">
      {/* Header & Controls */}
      <div className="flex justify-between items-center mb-6">
        <div>
          <h2 className="text-xl font-bold">אנליטיקס ודוחות</h2>
          <p className="text-gray-500">ניתוח ביצועים ומגמות</p>
        </div>
        <div className="flex gap-4">
          <select
            value={timeframe}
            onChange={(e) => setTimeframe(e.target.value)}
            className="border rounded p-2"
          >
            <option value="7d">7 ימים</option>
            <option value="30d">30 ימים</option>
            <option value="90d">90 ימים</option>
            <option value="1y">שנה</option>
          </select>
          <button
            onClick={exportReport}
            disabled={isExporting}
            className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50"
          >
            {isExporting ? 'מייצא...' : 'ייצא לאקסל'}
          </button>
        </div>
      </div>

      {/* Report Navigation */}
      <div className="flex gap-4 mb-6 border-b">
        <ReportTab
          id="overview"
          label="סקירה כללית"
          selected={selectedReport === 'overview'}
          onClick={setSelectedReport}
        />
        <ReportTab
          id="agents"
          label="ביצועי סוכנים"
          selected={selectedReport === 'agents'}
          onClick={setSelectedReport}
        />
        <ReportTab
          id="queries"
          label="ניתוח שאלות"
          selected={selectedReport === 'queries'}
          onClick={setSelectedReport}
        />
        <ReportTab
          id="usage"
          label="דפוסי שימוש"
          selected={selectedReport === 'usage'}
          onClick={setSelectedReport}
        />
      </div>

      {/* Report Content */}
      {reportData ? (
        <div className="space-y-6">
          {selectedReport === 'overview' && (
            <OverviewReport data={reportData} />
          )}
          {selectedReport === 'agents' && (
            <AgentsReport data={reportData} />
          )}
          {selectedReport === 'queries' && (
            <QueriesReport data={reportData} />
          )}
          {selectedReport === 'usage' && (
            <UsageReport data={reportData} />
          )}
        </div>
      ) : (
        <div className="text-center py-12">
          <p className="text-gray-500">טוען נתונים...</p>
        </div>
      )}
    </div>
  );
};

const ReportTab = ({ id, label, selected, onClick }) => (
  <button
    onClick={() => onClick(id)}
    className={`pb-2 px-4 ${
      selected
        ? 'border-b-2 border-blue-500 text-blue-500'
        : 'text-gray-500 hover:text-gray-700'
    }`}
  >
    {label}
  </button>
);

const OverviewReport = ({ data }) => (
  <div>
    {/* KPI Summary */}
    <div className="grid grid-cols-4 gap-4 mb-6">
      <KpiCard
        title="סה״כ פניות"
        value={data.totalQueries}
        change={data.queriesChange}
      />
      <KpiCard
        title="דיוק ממוצע"
        value={`${data.avgAccuracy}%`}
        change={data.accuracyChange}
      />
      <KpiCard
        title="זמן תגובה"
        value={`${data.avgResponseTime}ms`}
        change={data.responseTimeChange}
        invertChange
      />
      <KpiCard
        title="משתמשים פעילים"
        value={data.activeUsers}
        change={data.usersChange}
      />
    </div>

    {/* Usage Trend */}
    <div className="bg-gray-50 p-4 rounded-lg mb-6">
      <h3 className="font-semibold mb-4">מגמת שימוש</h3>
      <LineChart
        width={800}
        height={300}
        data={data.usageTrend}
        margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
      >
        <XAxis dataKey="date" />
        <YAxis />
        <Tooltip />
        <Legend />
        <Line type="monotone" dataKey="queries" name="פניות" stroke="#8884d8" />
        <Line type="monotone" dataKey="users" name="משתמשים" stroke="#82ca9d" />
      </LineChart>
    </div>
  </div>
);

const AgentsReport = ({ data }) => (
  <div>
    <div className="grid grid-cols-2 gap-6">
      {/* Agent Performance */}
      <div className="bg-gray-50 p-4 rounded-lg">
        <h3 className="font-semibold mb-4">ביצועי סוכנים</h3>
        <BarChart
          width={400}
          height={300}
          data={data.agentPerformance}
          margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
        >
          <XAxis dataKey="name" />
          <YAxis />
          <Tooltip />
          <Legend />
          <Bar dataKey="accuracy" name="דיוק" fill="#8884d8" />
          <Bar dataKey="speed" name="מהירות" fill="#82ca9d" />
        </BarChart>
      </div>

      {/* Query Distribution */}
      <div className="bg-gray-50 p-4 rounded-lg">
        <h3 className="font-semibold mb-4">התפלגות שאלות</h3>
        <PieChart width={400} height={300}>
          <Pie
            data={data.queryDistribution}
            dataKey="value"
            nameKey="name"
            cx="50%"
            cy="50%"
            outerRadius={100}
            fill="#8884d8"
            label
          />
          <Tooltip />
          <Legend />
        </PieChart>
      </div>
    </div>
  </div>
);

const QueriesReport = ({ data }) => (
  <div className="space-y-6">
    {/* Top Queries */}
    <div className="bg-gray-50 p-4 rounded-lg">
      <h3 className="font-semibold mb-4">שאלות נפוצות</h3>
      <div className="space-y-4">
        {data.topQueries.map((query, index) => (
          <div key={index} className="flex justify-between items-center">
            <div>
              <span className="font-medium">{query.text}</span>
              <div className="text-sm text-gray-500">
                קטגוריה: {query.category} • הצלחה: {query.successRate}%
              </div>
            </div>
            <div className="text-lg font-semibold">{query.count}</div>
          </div>
        ))}
      </div>
    </div>

    {/* Query Categories */}
    <div className="grid grid-cols-3 gap-4">
      {data.categories.map((category) => (
        <div key={category.name} className="bg-gray-50 p-4 rounded-lg">
          <h4 className="font-medium">{category.name}</h4>
          <div className="text-2xl font-bold mb-2">{category.count}</div>
          <div className="text-sm text-gray-500">
            הצלחה: {category.successRate}% • זמן ממוצע: {category.avgTime}ms
          </div>
        </div>
      ))}
    </div>
  </div>
);

const UsageReport = ({ data }) => (
  <div className="space-y-6">
    {/* Usage Patterns */}
    <div className="bg-gray-50 p-4 rounded-lg">
      <h3 className="font-semibold mb-4">דפוסי שימוש</h3>
      <div className="grid grid-cols-2 gap-4">
        {/* Usage by Hour */}
        <div>
          <h4 className="text-sm font-medium mb-2">שימוש לפי שעות</h4>
          <BarChart
            width={400}
            height={200}
            data={data.usageByHour}
          >
            <XAxis dataKey="hour" />
            <YAxis />
            <Tooltip />
            <Bar dataKey="queries" fill="#8884d8" />
          </BarChart>
        </div>

        {/* Usage by Day */}
        <div>
          <h4 className="text-sm font-medium mb-2">שימוש לפי ימים</h4>
          <BarChart
            width={400}
            height={200}
            data={data.usageByDay}
          >
            <XAxis dataKey="day" />
            <YAxis />
            <Tooltip />
            <Bar dataKey="queries" fill="#82ca9d" />
          </BarChart>
        </div>
      </div>
    </div>
  </div>
);

const KpiCard = ({ title, value, change, invertChange = false }) => (
  <div className="bg-gray-50 p-4 rounded-lg">
    <div className="text-sm text-gray-500 mb-1">{title}</div>
    <div className="text-2xl font-bold mb-2">{value}</div>
    <div className={`text-sm flex items-center ${
      change === 0 ? 'text-gray-500' :
      (invertChange ? (change < 0) : (change > 0)) ? 'text-green-500' : 'text-red-500'
    }`}>
      {change !== 0 && (
        <svg className="w-4 h-4 mr-1" viewBox="0 0 20 20" fill="currentColor">
          <path fillRule="evenodd" d={
            (invertChange ? (change < 0) : (change > 0))
              ? "M5.293 7.707a1 1 0 010-1.414l4-4a1 1 0 011.414 0l4 4a1 1 0 01-1.414 1.414L11 5.414V17a1 1 0 11-2 0V5.414L6.707 7.707a1 1 0 01-1.414 0z"
              : "M14.707 12.293a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 111.414-1.414L9 14.586V3a1 1 0 012 0v11.586l2.293-2.293a1 1 0 011.414 0z"
          } clipRule="evenodd" />
        </svg>
      )}
      {Math.abs(change)}%
    </div>
  </div>
);

export default AnalyticsReports;