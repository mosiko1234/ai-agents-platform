import React, { useState, useEffect } from 'react';

const KnowledgeManagement = () => {
  const [activeTab, setActiveTab] = useState('documents');
  const [documents, setDocuments] = useState([]);
  const [categories, setCategories] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('all');

  useEffect(() => {
    fetchData();
  }, [activeTab, selectedCategory]);

  const fetchData = async () => {
    const response = await fetch(
      `/api/v1/knowledge/${activeTab}?category=${selectedCategory}`
    );
    setDocuments(await response.json());

    const categoriesRes = await fetch('/api/v1/knowledge/categories');
    setCategories(await categoriesRes.json());
  };

  return (
    <div className="bg-white rounded-lg shadow p-6">
      {/* Header with Search */}
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-xl font-bold">ניהול מאגר ידע משפטי</h2>
        <div className="flex gap-4">
          <input
            type="text"
            placeholder="חיפוש..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="border rounded p-2 w-64"
          />
          <button
            onClick={() => setActiveTab('upload')}
            className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
          >
            העלאת מסמך
          </button>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="border-b mb-6">
        <nav className="flex gap-6">
          {[
            { id: 'documents', label: 'מסמכים' },
            { id: 'precedents', label: 'תקדימים' },
            { id: 'laws', label: 'חוקים ותקנות' }
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`pb-2 px-1 ${
                activeTab === tab.id
                  ? 'border-b-2 border-blue-500 text-blue-500'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Category Filter */}
      <div className="mb-6">
        <select
          value={selectedCategory}
          onChange={(e) => setSelectedCategory(e.target.value)}
          className="border rounded p-2"
        >
          <option value="all">כל הקטגוריות</option>
          {categories.map((category) => (
            <option key={category.id} value={category.id}>
              {category.name}
            </option>
          ))}
        </select>
      </div>

      {/* Content Area */}
      {activeTab === 'upload' ? (
        <UploadForm onSuccess={fetchData} />
      ) : (
        <div className="grid grid-cols-1 gap-4">
          {documents
            .filter((doc) => 
              doc.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
              doc.content.toLowerCase().includes(searchTerm.toLowerCase())
            )
            .map((document) => (
              <DocumentCard
                key={document.id}
                document={document}
                onUpdate={fetchData}
              />
            ))}
        </div>
      )}
    </div>
  );
};

const UploadForm = ({ onSuccess }) => {
  const [file, setFile] = useState(null);
  const [metadata, setMetadata] = useState({
    title: '',
    category: '',
    description: '',
    tags: []
  });

  const handleSubmit = async (e) => {
    e.preventDefault();
    const formData = new FormData();
    formData.append('file', file);
    formData.append('metadata', JSON.stringify(metadata));

    await fetch('/api/v1/knowledge/upload', {
      method: 'POST',
      body: formData
    });

    onSuccess();
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label className="block text-sm font-medium mb-1">כותרת</label>
        <input
          type="text"
          value={metadata.title}
          onChange={(e) => setMetadata({ ...metadata, title: e.target.value })}
          className="w-full p-2 border rounded"
          required
        />
      </div>

      <div>
        <label className="block text-sm font-medium mb-1">קטגוריה</label>
        <input
          type="text"
          value={metadata.category}
          onChange={(e) => setMetadata({ ...metadata, category: e.target.value })}
          className="w-full p-2 border rounded"
          required
        />
      </div>

      <div>
        <label className="block text-sm font-medium mb-1">תיאור</label>
        <textarea
          value={metadata.description}
          onChange={(e) => setMetadata({ ...metadata, description: e.target.value })}
          className="w-full p-2 border rounded h-24"
        />
      </div>

      <div>
        <label className="block text-sm font-medium mb-1">תגיות</label>
        <input
          type="text"
          value={metadata.tags.join(', ')}
          onChange={(e) => setMetadata({ 
            ...metadata, 
            tags: e.target.value.split(',').map(tag => tag.trim()) 
          })}
          className="w-full p-2 border rounded"
          placeholder="הפרד תגיות עם פסיקים"
        />
      </div>

      <div>
        <label className="block text-sm font-medium mb-1">קובץ</label>
        <input
          type="file"
          onChange={(e) => setFile(e.target.files[0])}
          className="w-full"
          required
        />
      </div>

      <div className="flex justify-end">
        <button
          type="submit"
          className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
        >
          העלה מסמך
        </button>
      </div>
    </form>
  );
};

const DocumentCard = ({ document, onUpdate }) => {
  const [isExpanded, setIsExpanded] = useState(false);

  const handleDelete = async () => {
    if (window.confirm('האם אתה בטוח שברצונך למחוק מסמך זה?')) {
      await fetch(`/api/v1/knowledge/${document.id}`, { method: 'DELETE' });
      onUpdate();
    }
  };

  return (
    <div className="border rounded-lg p-4">
      <div className="flex justify-between items-start">
        <div>
          <h3 className="font-medium">{document.title}</h3>
          <p className="text-sm text-gray-500">
            קטגוריה: {document.category} • עודכן: {new Date(document.updated_at).toLocaleDateString()}
          </p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="p-1 text-gray-500 hover:text-gray-700"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d={
                isExpanded 
                  ? "M5 15l7-7 7 7"
                  : "M19 9l-7 7-7-7"
              } />
            </svg>
          </button>
          <button
            onClick={handleDelete}
            className="p-1 text-red-500 hover:text-red-700"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
            </svg>
          </button>
        </div>
      </div>

      {isExpanded && (
        <div className="mt-4">
          <p className="text-gray-600 mb-2">{document.description}</p>
          <div className="flex flex-wrap gap-2">
            {document.tags.map((tag, index) => (
              <span key={index} className="px-2 py-1 bg-gray-100 rounded text-sm">
                {tag}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default KnowledgeManagement;