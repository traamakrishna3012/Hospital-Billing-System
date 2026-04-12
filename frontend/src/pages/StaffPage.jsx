import { useState, useEffect, useCallback } from 'react';
import { motion } from 'framer-motion';
import { UserCog, Plus, Pencil, Trash2 } from 'lucide-react';
import toast from 'react-hot-toast';
import { userAPI } from '../services/api';
import { useAuthStore } from '../store/authStore';
import { Pagination, Modal, EmptyState, LoadingSpinner, StatusBadge } from '../components/UI';

export default function StaffPage() {
  const [users, setUsers] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [loading, setLoading] = useState(true);
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState(null);
  const [form, setForm] = useState({ email: '', full_name: '', phone: '', password: '', role: 'staff' });
  const currentUser = useAuthStore((s) => s.user);

  const loadUsers = useCallback(async () => {
    setLoading(true);
    try {
      const { data } = await userAPI.list({ page, page_size: 20 });
      setUsers(data.items);
      setTotal(data.total);
      setTotalPages(data.total_pages);
    } catch (err) {
      toast.error('Failed to load staff');
    } finally {
      setLoading(false);
    }
  }, [page]);

  useEffect(() => { loadUsers(); }, [loadUsers]);

  const openCreate = () => {
    setEditing(null);
    setForm({ email: '', full_name: '', phone: '', password: '', role: 'staff' });
    setModalOpen(true);
  };

  const openEdit = (user) => {
    setEditing(user);
    setForm({ full_name: user.full_name, phone: user.phone || '', role: user.role });
    setModalOpen(true);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (editing) {
        await userAPI.update(editing.id, { full_name: form.full_name, phone: form.phone, role: form.role });
        toast.success('User updated');
      } else {
        await userAPI.create(form);
        toast.success('Staff user created');
      }
      setModalOpen(false);
      loadUsers();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Operation failed');
    }
  };

  const handleDelete = async (id) => {
    if (!confirm('Remove this staff member?')) return;
    try {
      await userAPI.delete(id);
      toast.success('User removed');
      loadUsers();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to delete');
    }
  };

  return (
    <div className="space-y-6 max-w-4xl">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-surface-800">Staff Management</h1>
          <p className="text-surface-400 mt-1">{total} team members</p>
        </div>
        <button onClick={openCreate} className="btn-primary flex items-center gap-2">
          <Plus className="w-4 h-4" /> Add Staff
        </button>
      </div>

      {loading ? (
        <LoadingSpinner />
      ) : users.length === 0 ? (
        <EmptyState icon={UserCog} title="No staff members" description="Add staff members to manage your clinic." action={<button onClick={openCreate} className="btn-primary">Add Staff</button>} />
      ) : (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="glass-card overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="bg-surface-50">
                  {['Name', 'Email', 'Role', 'Status', 'Actions'].map((h) => (
                    <th key={h} className="px-6 py-3 text-left text-xs font-semibold text-surface-500 uppercase tracking-wider">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-surface-100">
                {users.map((user) => (
                  <tr key={user.id} className="hover:bg-surface-50/50">
                    <td className="px-6 py-4">
                      <p className="text-sm font-medium text-surface-800">{user.full_name}</p>
                      {user.phone && <p className="text-xs text-surface-400">{user.phone}</p>}
                    </td>
                    <td className="px-6 py-4 text-sm text-surface-600">{user.email}</td>
                    <td className="px-6 py-4"><StatusBadge status={user.role} /></td>
                    <td className="px-6 py-4"><StatusBadge status={user.is_active ? 'active' : 'inactive'} /></td>
                    <td className="px-6 py-4">
                      {user.id !== currentUser?.id && (
                        <div className="flex gap-1">
                          <button onClick={() => openEdit(user)} className="btn-ghost p-2"><Pencil className="w-4 h-4 text-surface-500" /></button>
                          <button onClick={() => handleDelete(user.id)} className="btn-ghost p-2"><Trash2 className="w-4 h-4 text-red-400" /></button>
                        </div>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="px-6 py-3 border-t border-surface-100 flex justify-end">
            <Pagination page={page} totalPages={totalPages} onPageChange={setPage} />
          </div>
        </motion.div>
      )}

      <Modal isOpen={modalOpen} onClose={() => setModalOpen(false)} title={editing ? 'Edit Staff' : 'Add Staff'}>
        <form onSubmit={handleSubmit} className="space-y-4">
          {!editing && (
            <div>
              <label className="label-text">Email *</label>
              <input type="email" required value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} className="input-field" />
            </div>
          )}
          <div>
            <label className="label-text">Full Name *</label>
            <input required value={form.full_name} onChange={(e) => setForm({ ...form, full_name: e.target.value })} className="input-field" />
          </div>
          <div>
            <label className="label-text">Phone</label>
            <input value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} className="input-field" />
          </div>
          {!editing && (
            <div>
              <label className="label-text">Password *</label>
              <input type="password" required minLength={8} value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} className="input-field" />
            </div>
          )}
          <div>
            <label className="label-text">Role</label>
            <select value={form.role} onChange={(e) => setForm({ ...form, role: e.target.value })} className="input-field">
              <option value="staff">Staff / Receptionist</option>
              <option value="admin">Admin</option>
              <option value="doctor">Consulting Doctor</option>
            </select>
          </div>
          <div className="flex justify-end gap-3 pt-2">
            <button type="button" onClick={() => setModalOpen(false)} className="btn-secondary">Cancel</button>
            <button type="submit" className="btn-primary">{editing ? 'Update' : 'Create'}</button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
