import React, { useState, useEffect } from 'react';

const AgentSettings = ({ agentId }) => {
  const [settings, setSettings] = useState({
    name: '',
    description: '',
    model: 'gpt-4',
    responseTemplate: '',
    knowledgeUpdateInterval: 24,
    alertPriority: 'medium',
    allowedCategories: []
  });

  useEffect(() => {
    fetchSettings();
  }, [agentId]);

  const fetchSettings = async () => {
    const response = await fetch(`/api/v1/agents/${agentId}/settings`);
    const data = await response.json();
    setSettings(data);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    await fetch(`/api/v1/agents/${agentId}/settings`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(settings)
    });
  };

  return (
    <div className="p-6 bg-white rounded-lg shadow">
      <h2 className="text-xl font-bold mb-6">הגדרות סוכן</h2>
      
      <form onSubmit={handleSubmit} className="space-y-6">
        <div>
          <label className="block text-sm font-medium mb-2">שם</label>
          <input
            type="text"
            value={settings.name}
            onChange={(e) => setSettings({...settings, name: e.target.value})}
            className="w-full p-2 border rounded"
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-2">תיאור</label>
          <textarea
            value={settings.description}
            onChange={(e) => setSettings({...settings, description: e.target.value})}
            className="w-full p-2 border rounded h-24"
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-2">מודל</label>
          <select
            value={settings.model}
            onChange={(e) => setSettings({...settings, model: e.target.value})}
            className="w-full p-2 border rounded"
          >
            <option value="gpt-4">GPT-4</option>
            <option value="gpt-3.5-turbo">GPT-3.5 Turbo</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium mb-2">תבנית תשובה</label>
          <textarea
            value={settings.responseTemplate}
            onChange={(e) => setSettings({...settings, responseTemplate: e.target.value})}
            className="w-full p-2 border rounded h-32 font-mono"
            placeholder="תבנית עבור תשובות הסוכן..."
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-2">מרווח עדכון ידע (שעות)</label>
          <input
            type="number"
            value={settings.knowledgeUpdateInterval}
            onChange={(e) => setSettings({...settings, knowledgeUpdateInterval: parseInt(e.target.value)})}
            className="w-full p-2 border rounded"
            min="1"
            max="72"
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-2">עדיפות התראות</label>
          <select
            value={settings.alertPriority}
            onChange={(e) => setSettings({...settings, alertPriority: e.target.value})}
            className="w-full p-2 border rounded"
          >
            <option value="low">נמוכה</option>
            <option value="medium">בינונית</option>
            <option value="high">גבוהה</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium mb-2">קטגוריות מותרות</label>
          <div className="space-y-2">
            {['הוצאה לפועל', 'גביית חובות', 'עיקולים', 'פשיטת רגל'].map(category => (
              <label key={category} className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  checked={settings.allowedCategories.includes(category)}
                  onChange={(e) => {
                    const newCategories = e.target.checked
                      ? [...settings.allowedCategories, category]
                      : settings.allowedCategories.filter(c => c !== category);
                    setSettings({...settings, allowedCategories: newCategories});
                  }}
                  className="form-checkbox"
                />
                <span>{category}</span>
              </label>
            ))}
          </div>
        </div>

        <div className="flex justify-end space-x-4">
          <button
            type="button"
            onClick={() => fetchSettings()}
            className="px-4 py-2 text-gray-600 border rounded hover:bg-gray-50"
          >
            בטל
          </button>
          <button
            type="submit"
            className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
          >
            שמור
          </button>
        </div>
      </form>
    </div>
  );
};

export default AgentSettings;