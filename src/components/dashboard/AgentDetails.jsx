import React, { useState, useEffect } from 'react';
import { LineChart, XAxis, YAxis, Tooltip, Legend, Line } from 'recharts';

const AgentDetails = ({ agentId }) => {
  const [agent, setAgent] = useState(null);
  const [performance, setPerformance] = useState([]);
  const [interactions, setInteractions] = useState([]);

  useEffect(() => {
    if (agentId) {
      fetchAgentData();
      fetchPerformance();
      fetchInteractions();
    }
  }, [agentId]);

  const fetchAgentData = async () => {
    const response = await fetch(`/api/v1/agents/${agentId}`);
    const data = await response.json();
    setAgent(data);
  };

  const fetchPerformance = async () => {
    const response = await fetch(`/api/v1/agents/${agentId}/performance`);
    const data = await response.json();
    setPerformance(data);
  };

  const fetchInteractions = async () => {
    const response = await fetch(`/api/v1/agents/${agentId}/interactions`);
    const data = await response.json();
    setInteractions(data);
  };

  if (!agent) return <div>Loading...</div>;

  return (
    <div className="p-6 bg-gray-50">
      {/* Header */}
      <header className="flex justify-between items-center mb-6">
        <div>
          <h2 className="text-2xl font-bold">{agent.name}</h2>
          <p className="text-gray-600">{agent.description}</p>
        </div>
        <div className="flex gap-2">
          <button 
            className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600"
            onClick={() => agent.status === 'active' ? deactivateAgent() : activateAgent()}
          >
            {agent.status === 'active' ? 'השבת' : 'הפעל'}
          </button>
          <button 
            className="px-4 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600"
            onClick={() => updateKnowledge()}
          >
            עדכן ידע
          </button>
        </div>
      </header>

      {/* Stats Grid */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        <StatsBox 
          title="דיוק"
          value={`${(agent.accuracy * 100).toFixed(1)}%`}
          trend={agent.accuracyTrend}
        />
        <StatsBox 
          title="זמן תגובה"
          value={`${agent.responseTime.toFixed(2)}s`}
          trend={agent.responseTrend}
        />
        <StatsBox 
          title="פניות היום"
          value={agent.requestsToday}
          trend={agent.requestsTrend}
        />
      </div>

      {/* Performance Chart */}
      <div className="bg-white rounded-lg shadow p-4 mb-6">
        <h3 className="text-lg font-semibold mb-4">ביצועים לאורך זמן</h3>
        <LineChart
          width={800}
          height={300}
          data={performance}
          margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
        >
          <XAxis dataKey="date" />
          <YAxis />
          <Tooltip />
          <Legend />
          <Line type="monotone" dataKey="accuracy" stroke="#8884d8" name="דיוק" />
          <Line type="monotone" dataKey="responseTime" stroke="#82ca9d" name="זמן תגובה" />
        </LineChart>
      </div>

      {/* Recent Interactions */}
      <div className="bg-white rounded-lg shadow p-4">
        <h3 className="text-lg font-semibold mb-4">אינטראקציות אחרונות</h3>
        <div className="space-y-4">
          {interactions.map((interaction) => (
            <InteractionCard key={interaction.id} interaction={interaction} />
          ))}
        </div>
      </div>
    </div>
  );
};

const StatsBox = ({ title, value, trend }) => {
  const getTrendIcon = () => {
    if (trend > 0) {
      return (
        <svg className="w-4 h-4 text-green-500" viewBox="0 0 20 20" fill="currentColor">
          <path fillRule="evenodd" d="M12 7a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0V8.414l-4.293 4.293a1 1 0 01-1.414 0L8 10.414l-4.293 4.293a1 1 0 01-1.414-1.414l5-5a1 1 0 011.414 0L11 10.586 14.586 7H12z" clipRule="evenodd" />
        </svg>
      );
    }
    return (
      <svg className="w-4 h-4 text-red-500" viewBox="0 0 20 20" fill="currentColor">
        <path fillRule="evenodd" d="M12 13a1 1 0 110 2h-5a1 1 0 01-1-1v-5a1 1 0 112 0v2.586l4.293-4.293a1 1 0 011.414 0L16 9.586V7a1 1 0 112 0v5a1 1 0 01-1 1h-5z" clipRule="evenodd" />
      </svg>
    );
  };

  return (
    <div className="bg-white rounded-lg shadow p-4">
      <div className="flex justify-between items-center mb-2">
        <h4 className="text-gray-600">{title}</h4>
        {getTrendIcon()}
      </div>
      <p className="text-2xl font-bold">{value}</p>
    </div>
  );
};

const InteractionCard = ({ interaction }) => (
  <div className="border rounded-lg p-4">
    <div className="flex justify-between items-start mb-2">
      <h4 className="font-medium">{interaction.query}</h4>
      <span className="text-sm text-gray-500">
        {new Date(interaction.timestamp).toLocaleString()}
      </span>
    </div>
    <p className="text-gray-700 mb-2">{interaction.response}</p>
    <div className="flex justify-between items-center text-sm text-gray-500">
      <span>דיוק: {interaction.accuracy * 100}%</span>
      <span>זמן תגובה: {interaction.responseTime}s</span>
    </div>
  </div>
);

export default AgentDetails;