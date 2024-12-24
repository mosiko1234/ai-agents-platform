import React, { useState, useEffect } from 'react';

const ApiSettings = () => {
  const [settings, setSettings] = useState({
    whatsapp: {
      enabled: false,
      apiKey: '',
      phoneNumberId: '',
      webhookUrl: '',
      status: 'disconnected'
    },
    telegram: {
      enabled: false,
      botToken: '',
      webhookUrl: '',
      status: 'disconnected'
    },
    legalDatabases: {
      nevo: {
        enabled: false,
        apiKey: '',
        status: 'disconnected'
      },
      takdin: {
        enabled: false,
        apiKey: '',
        status: 'disconnected'
      }
    },
    rateLimits: {
      enabled: true,
      requestsPerMinute: 60,
      requestsPerHour: 1000,
      requestsPerDay: 10000
    }
  });

  const [isEditing, setIsEditing] = useState(false);
  const [testResults, setTestResults] = useState({});

  useEffect(() => {
    fetchSettings();
  }, []);

  const fetchSettings = async () => {
    const response = await fetch('/api/v1/settings/api');
    const data = await response.json();
    setSettings(data);
  };

  const saveSettings = async () => {
    await fetch('/api/v1/settings/api', {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(settings)
    });
    setIsEditing(false);
    fetchSettings();
  };

  const testConnection = async (service) => {
    const response = await fetch(`/api/v1/settings/test-connection/${service}`);
    const result = await response.json();
    setTestResults({
      ...testResults,
      [service]: result
    });
  };

  return (
    <div className="bg-white rounded-lg shadow p-6">
      {/* Header */}
      <div className="flex justify-between items-center mb-6">
        <div>
          <h2 className="text-xl font-bold">הגדרות API ואינטגרציות</h2>
          <p className="text-gray-500">ניהול חיבורים למערכות חיצוניות</p>
        </div>
        <div className="flex gap-2">
          {isEditing ? (
            <>
              <button
                onClick={() => {
                  setIsEditing(false);
                  fetchSettings();
                }}
                className="px-4 py-2 border text-gray-600 rounded hover:bg-gray-50"
              >
                ביטול
              </button>
              <button
                onClick={saveSettings}
                className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
              >
                שמור שינויים
              </button>
            </>
          ) : (
            <button
              onClick={() => setIsEditing(true)}
              className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
            >
              ערוך הגדרות
            </button>
          )}
        </div>
      </div>

      {/* Messaging Platforms */}
      <div className="mb-8">
        <h3 className="font-semibold mb-4">פלטפורמות הודעות</h3>
        <div className="grid grid-cols-2 gap-6">
          <IntegrationCard
            title="WhatsApp"
            settings={settings.whatsapp}
            isEditing={isEditing}
            onChange={(value) => setSettings({
              ...settings,
              whatsapp: { ...settings.whatsapp, ...value }
            })}
            onTest={() => testConnection('whatsapp')}
            testResult={testResults.whatsapp}
            fields={[
              { key: 'apiKey', label: 'API Key', type: 'password' },
              { key: 'phoneNumberId', label: 'Phone Number ID', type: 'text' },
              { key: 'webhookUrl', label: 'Webhook URL', type: 'text' }
            ]}
          />

          <IntegrationCard
            title="Telegram"
            settings={settings.telegram}
            isEditing={isEditing}
            onChange={(value) => setSettings({
              ...settings,
              telegram: { ...settings.telegram, ...value }
            })}
            onTest={() => testConnection('telegram')}
            testResult={testResults.telegram}
            fields={[
              { key: 'botToken', label: 'Bot Token', type: 'password' },
              { key: 'webhookUrl', label: 'Webhook URL', type: 'text' }
            ]}
          />
        </div>
      </div>

      {/* Legal Databases */}
      <div className="mb-8">
        <h3 className="font-semibold mb-4">מאגרי מידע משפטיים</h3>
        <div className="grid grid-cols-2 gap-6">
          {Object.entries(settings.legalDatabases).map(([name, config]) => (
            <IntegrationCard
              key={name}
              title={name.charAt(0).toUpperCase() + name.slice(1)}
              settings={config}
              isEditing={isEditing}
              onChange={(value) => setSettings({
                ...settings,
                legalDatabases: {
                  ...settings.legalDatabases,
                  [name]: { ...config, ...value }
                }
              })}
              onTest={() => testConnection(name)}
              testResult={testResults[name]}
              fields={[
                { key: 'apiKey', label: 'API Key', type: 'password' }
              ]}
            />
          ))}
        </div>
      </div>

      {/* Rate Limits */}
      <div>
        <h3 className="font-semibold mb-4">הגבלות קצב פניות</h3>
        <div className="bg-gray-50 p-4 rounded-lg">
          <div className="flex items-center mb-4">
            <input
              type="checkbox"
              checked={settings.rateLimits.enabled}
              onChange={(e) => setSettings({
                ...settings,
                rateLimits: {
                  ...settings.rateLimits,
                  enabled: e.target.checked
                }
              })}
              disabled={!isEditing}
              className="ml-2"
            />
            <span>הפעל הגבלות קצב</span>
          </div>
          
          <div className="grid grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium mb-1">בקשות לדקה</label>
              <input
                type="number"
                value={settings.rateLimits.requestsPerMinute}
                onChange={(e) => setSettings({
                  ...settings,
                  rateLimits: {
                    ...settings.rateLimits,
                    requestsPerMinute: parseInt(e.target.value)
                  }
                })}
                disabled={!isEditing}
                className="w-full p-2 border rounded"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">בקשות לשעה</label>
              <input
                type="number"
                value={settings.rateLimits.requestsPerHour}
                onChange={(e) => setSettings({
                  ...settings,
                  rateLimits: {
                    ...settings.rateLimits,
                    requestsPerHour: parseInt(e.target.value)
                  }
                })}
                disabled={!isEditing}
                className="w-full p-2 border rounded"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">בקשות ליום</label>
              <input
                type="number"
                value={settings.rateLimits.requestsPerDay}
                onChange={(e) => setSettings({
                  ...settings,
                  rateLimits: {
                    ...settings.rateLimits,
                    requestsPerDay: parseInt(e.target.value)
                  }
                })}
                disabled={!isEditing}
                className="w-full p-2 border rounded"
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

const IntegrationCard = ({ 
  title, 
  settings, 
  isEditing, 
  onChange, 
  onTest, 
  testResult,
  fields 
}) => (
  <div className="bg-gray-50 p-4 rounded-lg">
    <div className="flex justify-between items-start mb-4">
      <div>
        <h4 className="font-medium">{title}</h4>
        <div className={`text-sm ${
          settings.status === 'connected' ? 'text-green-500' : 'text-red-500'
        }`}>
          {settings.status}
        </div>
      </div>
      <div className="flex items-center">
        <input
          type="checkbox"
          checked={settings.enabled}
          onChange={(e) => onChange({ enabled: e.target.checked })}
          disabled={!isEditing}
          className="ml-2"
        />
        <span className="text-sm">הפעל</span>
      </div>
    </div>

    <div className="space-y-4">
      {fields.map((field) => (
        <div key={field.key}>
          <label className="block text-sm font-medium mb-1">{field.label}</label>
          <input
            type={field.type}
            value={settings[field.key]}
            onChange={(e) => onChange({ [field.key]: e.target.value })}
            disabled={!isEditing}
            className="w-full p-2 border rounded"
          />
        </div>
      ))}
    </div>

    {testResult && (
      <div className={`mt-4 p-2 rounded text-sm ${
        testResult.success ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
      }`}>
        {testResult.message}
      </div>
    )}

    <button
      onClick={onTest}
      disabled={!settings.enabled}
      className="mt-4 px-4 py-2 text-blue-500 border border-blue-500 rounded hover:bg-blue-50 disabled:opacity-50"
    >
      בדוק חיבור
    </button>
  </div>
);

export default ApiSettings;