import React, { useState, useEffect } from 'react';

const UserManagement = () => {
  const [users, setUsers] = useState([]);
  const [roles, setRoles] = useState([]);
  const [selectedUser, setSelectedUser] = useState(null);
  const [isEditing, setIsEditing] = useState(false);

  useEffect(() => {
    fetchUsers();
    fetchRoles();
  }, []);

  const fetchUsers = async () => {
    const response = await fetch('/api/v1/users');
    setUsers(await response.json());
  };

  const fetchRoles = async () => {
    const response = await fetch('/api/v1/roles');
    setRoles(await response.json());
  };

  const handleSave = async (userData) => {
    await fetch(`/api/v1/users/${userData.id || ''}`, {
      method: userData.id ? 'PUT' : 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(userData)
    });
    fetchUsers();
    setIsEditing(false);
    setSelectedUser(null);
  };

  return (
    <div className="p-6 bg-white rounded-lg shadow">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-xl font-bold">ניהול משתמשים</h2>
        <button
          onClick={() => {
            setSelectedUser({});
            setIsEditing(true);
          }}
          className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
        >
          משתמש חדש
        </button>
      </div>

      <div className="grid grid-cols-3 gap-6">
        {/* Users List */}
        <div className="col-span-1 border-l">
          <div className="space-y-2">
            {users.map((user) => (
              <UserListItem
                key={user.id}
                user={user}
                selected={selectedUser?.id === user.id}
                onClick={() => setSelectedUser(user)}
              />
            ))}
          </div>
        </div>

        {/* User Details */}
        <div className="col-span-2 pr-6">
          {selectedUser && !isEditing ? (
            <UserDetails
              user={selectedUser}
              onEdit={() => setIsEditing(true)}
              roles={roles}
            />
          ) : isEditing ? (
            <UserForm
              user={selectedUser}
              roles={roles}
              onSave={handleSave}
              onCancel={() => {
                setIsEditing(false);
                setSelectedUser(null);
              }}
            />
          ) : (
            <div className="text-center text-gray-500 py-8">
              בחר משתמש או צור משתמש חדש
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

const UserListItem = ({ user, selected, onClick }) => (
  <div
    className={`p-3 rounded cursor-pointer ${
      selected ? 'bg-blue-50 border-blue-500' : 'hover:bg-gray-50'
    }`}
    onClick={onClick}
  >
    <div className="flex items-center space-x-3">
      <div className="flex-1">
        <h3 className="font-medium">{user.name}</h3>
        <p className="text-sm text-gray-500">{user.email}</p>
      </div>
      <span className={`px-2 py-1 rounded text-sm ${
        user.active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
      }`}>
        {user.active ? 'פעיל' : 'לא פעיל'}
      </span>
    </div>
  </div>
);

const UserDetails = ({ user, onEdit, roles }) => (
  <div>
    <div className="flex justify-between items-start mb-6">
      <div>
        <h3 className="text-xl font-medium">{user.name}</h3>
        <p className="text-gray-500">{user.email}</p>
      </div>
      <button
        onClick={onEdit}
        className="px-4 py-2 text-blue-500 border border-blue-500 rounded hover:bg-blue-50"
      >
        ערוך
      </button>
    </div>

    <div className="grid grid-cols-2 gap-4">
      <DetailField label="תפקיד" value={user.role} />
      <DetailField label="סטטוס" value={user.active ? 'פעיל' : 'לא פעיל'} />
      <DetailField label="תאריך הצטרפות" value={new Date(user.created_at).toLocaleDateString()} />
      <DetailField label="כניסה אחרונה" value={new Date(user.last_login).toLocaleDateString()} />
    </div>

    <div className="mt-6">
      <h4 className="font-medium mb-2">הרשאות</h4>
      <div className="grid grid-cols-2 gap-2">
        {user.permissions.map((permission) => (
          <div key={permission} className="px-2 py-1 bg-gray-100 rounded text-sm">
            {permission}
          </div>
        ))}
      </div>
    </div>
  </div>
);

const UserForm = ({ user, roles, onSave, onCancel }) => {
  const [formData, setFormData] = useState(user || {
    name: '',
    email: '',
    role: '',
    active: true,
    permissions: []
  });

  return (
    <form onSubmit={(e) => {
      e.preventDefault();
      onSave(formData);
    }}>
      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium mb-1">שם</label>
          <input
            type="text"
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            className="w-full p-2 border rounded"
            required
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">אימייל</label>
          <input
            type="email"
            value={formData.email}
            onChange={(e) => setFormData({ ...formData, email: e.target.value })}
            className="w-full p-2 border rounded"
            required
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">תפקיד</label>
          <select
            value={formData.role}
            onChange={(e) => setFormData({ ...formData, role: e.target.value })}
            className="w-full p-2 border rounded"
            required
          >
            <option value="">בחר תפקיד</option>
            {roles.map((role) => (
              <option key={role.id} value={role.id}>{role.name}</option>
            ))}
          </select>
        </div>

        <div>
          <label className="flex items-center">
            <input
              type="checkbox"
              checked={formData.active}
              onChange={(e) => setFormData({ ...formData, active: e.target.checked })}
              className="ml-2"
            />
            <span>משתמש פעיל</span>
          </label>
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">הרשאות</label>
          <div className="space-y-2">
            {['read', 'write', 'admin'].map((permission) => (
              <label key={permission} className="flex items-center">
                <input
                  type="checkbox"
                  checked={formData.permissions.includes(permission)}
                  onChange={(e) => {
                    const updatedPermissions = e.target.checked
                      ? [...formData.permissions, permission]
                      : formData.permissions.filter(p => p !== permission);
                    setFormData({ ...formData, permissions: updatedPermissions });
                  }}
                  className="ml-2"
                />
                <span>{permission}</span>
              </label>
            ))}
          </div>
        </div>
      </div>

      <div className="mt-6 flex justify-end space-x-4">
        <button
          type="button"
          onClick={onCancel}
          className="px-4 py-2 text-gray-600 border rounded hover:bg-gray-50"
        >
          ביטול
        </button>
        <button
          type="submit"
          className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
        >
          שמור
        </button>
      </div>
    </form>
  );
};

const DetailField = ({ label, value }) => (
  <div>
    <label className="text-sm text-gray-500">{label}</label>
    <p className="font-medium">{value}</p>
  </div>
);

export default UserManagement;