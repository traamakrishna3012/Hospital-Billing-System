import { useState, useEffect, useCallback } from 'react';
import { motion } from 'framer-motion';
import { FlaskConical, Plus, Pencil, Trash2, Tag } from 'lucide-react';
import toast from 'react-hot-toast';
import { testAPI } from '../services/api';
import { SearchInput, Pagination, Modal, EmptyState, LoadingSpinner } from '../components/UI';

export default function TestsPage() {
  const [tests, setTests] = useState([]);
  const [categories, setCategories] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [search, setSearch] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('');
  const [loading, setLoading] = useState(true);
  const [modalOpen, setModalOpen] = useState(false);
  const [catModalOpen, setCatModalOpen] = useState(false);
  const [editing, setEditing] = useState(null);
  const [form, setForm] = useState({ name: '', description: '', price: '', code: '', category_id: '' });
  const [catForm, setCatForm] = useState({ name: '', description: '' });

  const loadTests = useCallback(async () => {
    setLoading(true);
    try {
      const [testsRes, catsRes] = await Promise.all([
        testAPI.list({ page, page_size: 15, search, category_id: categoryFilter || undefined, active_only: false }),
        testAPI.listCategories(),
      ]);
      setTests(testsRes.data.items);
      setTotal(testsRes.data.total);
      setTotalPages(testsRes.data.total_pages);
      setCategories(catsRes.data);
    } catch (err) {
      toast.error('Failed to load tests');
    } finally {
      setLoading(false);
    }
  }, [page, search, categoryFilter]);

  useEffect(() => { loadTests(); }, [loadTests]);
  useEffect(() => { setPage(1); }, [search, categoryFilter]);

  const openCreate = () => {
    setEditing(null);
    setForm({ name: '', description: '', price: '', code: '', category_id: '' });
    setModalOpen(true);
  };

  const openEdit = (test) => {
    setEditing(test);
    setForm({
      name: test.name, description: test.description || '',
      price: String(test.price), code: test.code || '',
      category_id: test.category_id || '',
    });
    setModalOpen(true);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const payload = {
      ...form,
      price: parseFloat(form.price),
      category_id: form.category_id || null,
    };
    try {
      if (editing) {
        await testAPI.update(editing.id, payload);
        toast.success('Test updated');
      } else {
        await testAPI.create(payload);
        toast.success('Test added');
      }
      setModalOpen(false);
      loadTests();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Operation failed');
    }
  };

  const handleDelete = async (id) => {
    if (!confirm('Delete this test?')) return;
    try {
      await testAPI.delete(id);
      toast.success('Test deleted');
      loadTests();
    } catch (err) {
      toast.error('Failed to delete');
    }
  };

  const handleCatSubmit = async (e) => {
    e.preventDefault();
    try {
      await testAPI.createCategory(catForm);
      toast.success('Category created');
      setCatModalOpen(false);
      setCatForm({ name: '', description: '' });
      loadTests();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to create category');
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-surface-800">Tests & Services</h1>
          <p className="text-surface-400 mt-1">{total} tests registered</p>
        </div>
        <div className="flex gap-3">
          <button onClick={() => setCatModalOpen(true)} className="btn-secondary flex items-center gap-2">
            <Tag className="w-4 h-4" /> Add Category
          </button>
          <button onClick={openCreate} className="btn-primary flex items-center gap-2">
            <Plus className="w-4 h-4" /> Add Test
          </button>
        </div>
      </div>

      <div className="flex items-center gap-4">
        <SearchInput value={search} onChange={setSearch} placeholder="Search tests..." />
        <select value={categoryFilter} onChange={(e) => setCategoryFilter(e.target.value)} className="input-field w-48">
          <option value="">All Categories</option>
          {categories.map((c) => (
            <option key={c.id} value={c.id}>{c.name}</option>
          ))}
        </select>
      </div>

      {loading ? (
        <LoadingSpinner />
      ) : tests.length === 0 ? (
        <EmptyState
          icon={FlaskConical}
          title="No tests found"
          description="Add medical tests and services to include in billing."
          action={<button onClick={openCreate} className="btn-primary">Add Test</button>}
        />
      ) : (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="glass-card overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="bg-surface-50">
                  {['Test Name', 'Code', 'Category', 'Price (MRP)', 'Status', 'Actions'].map((h) => (
                    <th key={h} className="px-6 py-3 text-left text-xs font-semibold text-surface-500 uppercase tracking-wider">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-surface-100">
                {tests.map((t) => (
                  <tr key={t.id} className="hover:bg-surface-50/50 transition-colors">
                    <td className="px-6 py-4">
                      <p className="text-sm font-medium text-surface-800">{t.name}</p>
                      {t.description && <p className="text-xs text-surface-400 truncate max-w-xs">{t.description}</p>}
                    </td>
                    <td className="px-6 py-4 text-sm text-surface-500 font-mono">{t.code || '—'}</td>
                    <td className="px-6 py-4">
                      {t.category ? (
                        <span className="badge-info">{t.category.name}</span>
                      ) : (
                        <span className="text-sm text-surface-400">—</span>
                      )}
                    </td>
                    <td className="px-6 py-4 text-sm font-semibold text-surface-800">₹{Number(t.price).toLocaleString()}</td>
                    <td className="px-6 py-4">
                      <span className={t.is_active ? 'badge-success' : 'badge-neutral'}>
                        {t.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-1">
                        <button onClick={() => openEdit(t)} className="btn-ghost p-2"><Pencil className="w-4 h-4 text-surface-500" /></button>
                        <button onClick={() => handleDelete(t.id)} className="btn-ghost p-2"><Trash2 className="w-4 h-4 text-red-400" /></button>
                      </div>
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

      {/* Test Modal */}
      <Modal isOpen={modalOpen} onClose={() => setModalOpen(false)} title={editing ? 'Edit Test' : 'Add Test'}>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="label-text">Test Name *</label>
            <input required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} className="input-field" placeholder="e.g., Complete Blood Count" />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="label-text">Price (MRP) *</label>
              <input type="number" required min="0" step="0.01" value={form.price} onChange={(e) => setForm({ ...form, price: e.target.value })} className="input-field" />
            </div>
            <div>
              <label className="label-text">Code</label>
              <input value={form.code} onChange={(e) => setForm({ ...form, code: e.target.value })} className="input-field" placeholder="e.g., CBC001" />
            </div>
          </div>
          <div>
            <label className="label-text">Category</label>
            <select value={form.category_id} onChange={(e) => setForm({ ...form, category_id: e.target.value })} className="input-field">
              <option value="">None</option>
              {categories.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
            </select>
          </div>
          <div>
            <label className="label-text">Description</label>
            <textarea value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} className="input-field resize-none" rows={2} />
          </div>
          <div className="flex justify-end gap-3 pt-2">
            <button type="button" onClick={() => setModalOpen(false)} className="btn-secondary">Cancel</button>
            <button type="submit" className="btn-primary">{editing ? 'Update' : 'Add'} Test</button>
          </div>
        </form>
      </Modal>

      {/* Category Modal */}
      <Modal isOpen={catModalOpen} onClose={() => setCatModalOpen(false)} title="Add Category" size="sm">
        <form onSubmit={handleCatSubmit} className="space-y-4">
          <div>
            <label className="label-text">Category Name *</label>
            <input required value={catForm.name} onChange={(e) => setCatForm({ ...catForm, name: e.target.value })} className="input-field" placeholder="e.g., Lab, Scan, Consultation" />
          </div>
          <div>
            <label className="label-text">Description</label>
            <textarea value={catForm.description} onChange={(e) => setCatForm({ ...catForm, description: e.target.value })} className="input-field resize-none" rows={2} />
          </div>
          <div className="flex justify-end gap-3">
            <button type="button" onClick={() => setCatModalOpen(false)} className="btn-secondary">Cancel</button>
            <button type="submit" className="btn-primary">Create Category</button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
