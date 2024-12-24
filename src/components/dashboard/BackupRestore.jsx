import React, { useState, useEffect } from 'react';

const BackupRestore = () => {
  const [backups, setBackups] = useState([]);
  const [isCreatingBackup, setIsCreatingBackup] = useState(false);
  const [isRestoring, setIsRestoring] = useState(false);
  const [selectedBackup, setSelectedBackup] = useState(null);
  const [backupConfig, setBackupConfig] = useState({
    includeKnowledge: true,
    includeSettings: true,
    includeHistory: true,
    includeMetrics: false
  });

  useEffect(() => {
    fetchBackups();
  }, []);

  const fetchBackups = async () => {
    const response = await fetch('/api/v1/system/backups');
    const data = await response.json();
    setBackups(data);
  };

  const createBackup = async () => {
    setIsCreatingBackup(true);
    try {
      await fetch('/api/v1/system/backups', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(backupConfig)
      });
      await fetchBackups();
    } finally {
      setIsCreatingBackup(false);
    }
  };

  const restoreBackup = async (backupId) => {
    if (!window.confirm('האם אתה בטוח שברצונך לשחזר גיבוי זה? פעולה זו תחליף את כל הנתונים הקיימים.')) {
      return;
    }

    setIsRestoring(true);
    try {
      await fetch(`/api/v1/system/backups/${backupId}/restore`, {
        method: 'POST'
      });
      window.location.reload();
    } finally {
      setIsRestoring(false);
    }
  };

  return (
    <div className="bg-white rounded-lg shadow p-6">
      {/* Header */}
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-xl font-bold">גיבוי ושחזור מערכת</h2>
        <button
          onClick={createBackup}
          disabled={isCreatingBackup}
          className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50"
        >
          {isCreatingBackup ? 'יוצר גיבוי...' : 'צור גיבוי חדש'}
        </button>
      </div>

      {/* Backup Configuration */}
      <div className="mb-6 p-4 border rounded-lg">
        <h3 className="font-semibold mb-4">הגדרות גיבוי</h3>
        <div className="grid grid-cols-2 gap-4">
          <label className="flex items-center space-x-2">
            <input
              type="checkbox"
              checked={backupConfig.includeKnowledge}
              onChange={(e) => setBackupConfig({
                ...backupConfig,
                includeKnowledge: e.target.checked
              })}
              className="ml-2"
            />
            <span>מאגר ידע</span>
          </label>
          <label className="flex items-center space-x-2">
            <input
              type="checkbox"
              checked={backupConfig.includeSettings}
              onChange={(e) => setBackupConfig({
                ...backupConfig,
                includeSettings: e.target.checked
              })}
              className="ml-2"
            />
            <span>הגדרות מערכת</span>
          </label>
          <label className="flex items-center space-x-2">
            <input
              type="checkbox"
              checked={backupConfig.includeHistory}
              onChange={(e) => setBackupConfig({
                ...backupConfig,
                includeHistory: e.target.checked
              })}
              className="ml-2"
            />
            <span>היסטוריית פעילות</span>
          </label>
          <label className="flex items-center space-x-2">
            <input
              type="checkbox"
              checked={backupConfig.includeMetrics}
              onChange={(e) => setBackupConfig({
                ...backupConfig,
                includeMetrics: e.target.checked
              })}
              className="ml-2"
            />
            <span>מטריקות מערכת</span>
          </label>
        </div>
      </div>

      {/* Backups List */}
      <div className="space-y-4">
        <h3 className="font-semibold">גיבויים קיימים</h3>
        {backups.map((backup) => (
          <BackupItem
            key={backup.id}
            backup={backup}
            onRestore={restoreBackup}
            isRestoring={isRestoring}
            isSelected={selectedBackup?.id === backup.id}
            onSelect={() => setSelectedBackup(backup)}
          />
        ))}
        {backups.length === 0 && (
          <div className="text-center text-gray-500 py-8">
            לא נמצאו גיבויים
          </div>
        )}
      </div>

      {/* Selected Backup Details */}
      {selectedBackup && (
        <div className="mt-6 p-4 border rounded-lg">
          <h3 className="font-semibold mb-4">פרטי גיבוי</h3>
          <div className="grid grid-cols-2 gap-4">
            <DetailField 
              label="מזהה" 
              value={selectedBackup.id} 
            />
            <DetailField 
              label="תאריך יצירה" 
              value={new Date(selectedBackup.created_at).toLocaleString()} 
            />
            <DetailField 
              label="גודל" 
              value={formatSize(selectedBackup.size)} 
            />
            <DetailField 
              label="סוג" 
              value={selectedBackup.type} 
            />
            <div className="col-span-2">
              <h4 className="font-medium mb-2">רכיבים שגובו:</h4>
              <div className="grid grid-cols-2 gap-2">
                {selectedBackup.components.map((component) => (
                  <div 
                    key={component} 
                    className="px-2 py-1 bg-gray-100 rounded text-sm"
                  >
                    {component}
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

const BackupItem = ({ 
  backup, 
  onRestore, 
  isRestoring, 
  isSelected, 
  onSelect 
}) => (
  <div 
    className={`border rounded-lg p-4 cursor-pointer hover:bg-gray-50 ${
      isSelected ? 'border-blue-500 bg-blue-50' : ''
    }`}
    onClick={onSelect}
  >
    <div className="flex justify-between items-center">
      <div>
        <h4 className="font-medium">{backup.type}</h4>
        <p className="text-sm text-gray-500">
          {new Date(backup.created_at).toLocaleString()} • {formatSize(backup.size)}
        </p>
      </div>
      <div className="flex gap-2">
        <button
          onClick={(e) => {
            e.stopPropagation();
            window.open(`/api/v1/system/backups/${backup.id}/download`);
          }}
          className="p-2 text-gray-600 hover:text-gray-800"
        >
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
          </svg>
        </button>
        <button
          onClick={(e) => {
            e.stopPropagation();
            onRestore(backup.id);
          }}
          disabled={isRestoring}
          className="p-2 text-blue-600 hover:text-blue-800 disabled:opacity-50"
        >
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
        </button>
      </div>
    </div>
  </div>
);

const DetailField = ({ label, value }) => (
  <div>
    <label className="text-sm text-gray-500">{label}</label>
    <p className="font-medium">{value}</p>
  </div>
);

const formatSize = (bytes) => {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

export default BackupRestore;