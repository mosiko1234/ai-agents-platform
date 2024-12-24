import React, { useState, useEffect } from 'react';

const SystemConfiguration = () => {
  const [config, setConfig] = useState({
    api: {
      rateLimits: {
        perSecond: 10,
        perMinute: 600,
        perHour: 30000
      },
      timeout: 30000
    },
    agents: {
      maxConcurrent: 5,
      knowledgeUpdateInterval: 24,
      defaultModel: 'gpt-4'
    },
    monitoring: {
      logLevel: 'info',
      retentionDays: 30,
      alertThresholds: {
        errorRate: 0.1,
        responseTime: 5000
      }
    },
    security: {
      tokenExpiry: 24,
      maxLoginAttempts: 5,
      passwordPolicy: {
        minLength: 8,
        requireNumbers: true,
        requireSymbols: true
      }
    }
  });

  const [isEditing, setIsEditing] = useState(false);
  const [editedConfig, setEditedConfig] = useState(config);

  useEffect(() => {
    fetchConfig();
  }, []);

  const fetchConfig = async () => {
    const response = await fetch('/api/v1/system/config');
    const data = await response.json();
    setConfig(data);
    setEditedConfig(data);
  };

  const handleSave = async () => {
    await fetch('/api/v1/system/config', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(editedConfig)
    });
    setConfig(editedConfig);
    setIsEditing(false);
  };

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-xl font-bold">הגדרות מערכת</h2>
        {!isEditing ? (
          <button
            onClick={() => setIsEditing(true)}
            className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
          >
            ערוך הגדרות
          </button>
        ) : (
          <div className="flex gap-2">
            <button
              onClick={() => {
                setEditedConfig(config);
                setIsEditing(false);
              }}
              className="px-4 py-2 border text-gray-600 rounded hover:bg-gray-50"
            >
              בטל
            </button>
            <button
              onClick={handleSave}
              className="px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600"
            >
              שמור שינויים
            </button>
          </div>
        )}
      </div>

      <div className="grid grid-cols-2 gap-6">
        {/* API Configuration */}
        <ConfigSection 
          title="הגדרות API"
          isEditing={isEditing}
          config={editedConfig.api}
          onChange={(value) => setEditedConfig({ ...editedConfig, api: value })}
        />

        {/* Agents Configuration */}
        <ConfigSection 
          title="הגדרות סוכנים"
          isEditing={isEditing}
          config={editedConfig.agents}
          onChange={(value) => setEditedConfig({ ...editedConfig, agents: value })}
        />

        {/* Monitoring Configuration */}
        <ConfigSection 
          title="הגדרות ניטור"
          isEditing={isEditing}
          config={editedConfig.monitoring}
          onChange={(value) => setEditedConfig({ ...editedConfig, monitoring: value })}
        />

        {/* Security Configuration */}
        <ConfigSection 
          title="הגדרות אבטחה"
          isEditing={isEditing}
          config={editedConfig.security}
          onChange={(value) => setEditedConfig({ ...editedConfig, security: value })}
        />
      </div>
    </div>
  );
};

const ConfigSection = ({ title, isEditing, config, onChange }) => {
  const renderValue = (value) => {
    if (typeof value === 'boolean') {
      return value ? 'כן' : 'לא';
    }
    if (typeof value === 'object') {
      return null;
    }
    return value;
  };

  const updateNestedValue = (obj, path, value) => {
    const copy = { ...obj };
    let current = copy;
    const parts = path.split('.');
    const last = parts.pop();
    
    for (const part of parts) {
      current = current[part] = { ...current[part] };
    }
    current[last] = value;
    
    onChange(copy);
  };

  const renderField = (key, value, path = '') => {
    const currentPath = path ? `${path}.${key}` : key;
    
    if (typeof value === 'object' && value !== null) {
      return (
        <div key={key} className="mt-2">
          <h4 className="font-medium text-gray-700 mb-2">{key}</h4>
          <div className="pr-4 space-y-2">
            {Object.entries(value).map(([k, v]) => renderField(k, v, currentPath))}
          </div>
        </div>
      );
    }

    return (
      <div key={key} className="flex justify-between items-center">
        <label className="text-sm text-gray-600">{key}</label>
        {isEditing ? (
          typeof value === 'boolean' ? (
            <select
              value={value.toString()}
              onChange={(e) => updateNestedValue(config, currentPath, e.target.value === 'true')}
              className="border rounded p-1"
            >
              <option value="true">כן</option>
              <option value="false">לא</option>
            </select>
          ) : (
            <input
              type={typeof value === 'number' ? 'number' : 'text'}
              value={value}
              onChange={(e) => {
                const newValue = 
                  typeof value === 'number' ? Number(e.target.value) : e.target.value;
                updateNestedValue(config, currentPath, newValue);
              }}
              className="border rounded p-1 w-32 text-left"
            />
          )
        ) : (
          <span className="text-sm">{renderValue(value)}</span>
        )}
      </div>
    );
  };

  return (
    <div className="border rounded-lg p-4">
      <h3 className="font-semibold mb-4">{title}</h3>
      <div className="space-y-3">
        {Object.entries(config).map(([key, value]) => renderField(key, value))}
      </div>
    </div>
  );
};

export default SystemConfiguration;