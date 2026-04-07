import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  Receipt, Plus, Eye, Download, Mail, Trash2, Filter,
} from 'lucide-react';
import toast from 'react-hot-toast';
import { format } from 'date-fns';
import { billAPI, patientAPI, doctorAPI, testAPI } from '../services/api';
import {
  SearchInput, Pagination, Modal, EmptyState,
  LoadingSpinner, StatusBadge,
} from '../components/UI';

export default function BillingPage() {
  const [bills, setBills] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [loading, setLoading] = useState(true);

  // Create Bill Modal State
  const [createModal, setCreateModal] = useState(false);
  const [detailModal, setDetailModal] = useState(false);
  const [selectedBill, setSelectedBill] = useState(null);

  // Form Data
  const [patients, setPatients] = useState([]);
  const [doctors, setDoctors] = useState([]);
  const [tests, setTests] = useState([]);
  const [billForm, setBillForm] = useState({
    patient_id: '',
    doctor_id: '',
    items: [{ description: '', unit_price: '', quantity: 1, medical_test_id: '' }],
    tax_percent: '',
    discount_percent: '0',
    payment_mode: 'cash',
    status: 'paid',
    notes: '',
  });

  const loadBills = useCallback(async () => {
    setLoading(true);
    try {
      const { data } = await billAPI.list({ page, page_size: 15, search, status: statusFilter });
      setBills(data.items);
      setTotal(data.total);
      setTotalPages(data.total_pages);
    } catch (err) {
      toast.error('Failed to load bills');
    } finally {
      setLoading(false);
    }
  }, [page, search, statusFilter]);

  useEffect(() => { loadBills(); }, [loadBills]);
  useEffect(() => { setPage(1); }, [search, statusFilter]);

  const openCreateModal = async () => {
    try {
      const [pRes, dRes, tRes] = await Promise.all([
        patientAPI.list({ page_size: 100 }),
        doctorAPI.list({ page_size: 100 }),
        testAPI.list({ page_size: 100 }),
      ]);
      setPatients(pRes.data.items);
      setDoctors(dRes.data.items);
      setTests(tRes.data.items);
      setBillForm({
        patient_id: '', doctor_id: '',
        items: [{ description: '', unit_price: '', quantity: 1, medical_test_id: '' }],
        tax_percent: '', discount_percent: '0', payment_mode: 'cash', status: 'paid', notes: '',
      });
      setCreateModal(true);
    } catch (err) {
      toast.error('Failed to load form data');
    }
  };

  const addItem = () => {
    setBillForm({
      ...billForm,
      items: [...billForm.items, { description: '', unit_price: '', quantity: 1, medical_test_id: '' }],
    });
  };

  const removeItem = (index) => {
    if (billForm.items.length <= 1) return;
    setBillForm({
      ...billForm,
      items: billForm.items.filter((_, i) => i !== index),
    });
  };

  const updateItem = (index, field, value) => {
    const newItems = [...billForm.items];
    newItems[index] = { ...newItems[index], [field]: value };

    // Auto-fill from test selection
    if (field === 'medical_test_id' && value) {
      const test = tests.find((t) => t.id === value);
      if (test) {
        newItems[index].description = test.name;
        newItems[index].unit_price = String(test.price);
      }
    }
    setBillForm({ ...billForm, items: newItems });
  };

  const calcSubtotal = () => {
    return billForm.items.reduce((sum, item) => {
      return sum + (parseFloat(item.unit_price) || 0) * (parseInt(item.quantity) || 1);
    }, 0);
  };

  const handleCreateBill = async (e) => {
    e.preventDefault();
    const payload = {
      patient_id: billForm.patient_id,
      doctor_id: billForm.doctor_id || null,
      items: billForm.items.map((item) => ({
        description: item.description,
        unit_price: parseFloat(item.unit_price),
        quantity: parseInt(item.quantity),
        medical_test_id: item.medical_test_id || null,
      })),
      tax_percent: billForm.tax_percent ? parseFloat(billForm.tax_percent) : null,
      discount_percent: parseFloat(billForm.discount_percent) || 0,
      payment_mode: billForm.payment_mode,
      status: billForm.status,
      notes: billForm.notes || null,
    };

    try {
      await billAPI.create(payload);
      toast.success('Bill created successfully!');
      setCreateModal(false);
      loadBills();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to create bill');
    }
  };

  const viewBill = async (id) => {
    try {
      const { data } = await billAPI.get(id);
      setSelectedBill(data);
      setDetailModal(true);
    } catch (err) {
      toast.error('Failed to load bill');
    }
  };

  const downloadPDF = async (id) => {
    try {
      const response = await billAPI.downloadPDF(id);
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.download = `receipt-${id}.pdf`;
      link.click();
      window.URL.revokeObjectURL(url);
      toast.success('PDF downloaded');
    } catch (err) {
      toast.error('Failed to download PDF');
    }
  };

  const sendEmail = async (id) => {
    try {
      await billAPI.sendEmail(id);
      toast.success('Receipt sent to patient');
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to send email');
    }
  };

  const deleteBill = async (id) => {
    if (!confirm('Delete this bill?')) return;
    try {
      await billAPI.delete(id);
      toast.success('Bill deleted');
      loadBills();
    } catch (err) {
      toast.error('Failed to delete');
    }
  };

  const subtotal = calcSubtotal();
  const discountAmt = subtotal * (parseFloat(billForm.discount_percent) || 0) / 100;
  const afterDiscount = subtotal - discountAmt;
  const taxAmt = afterDiscount * (parseFloat(billForm.tax_percent) || 18) / 100;
  const grandTotal = afterDiscount + taxAmt;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-surface-800">Billing</h1>
          <p className="text-surface-400 mt-1">{total} bills generated</p>
        </div>
        <button onClick={openCreateModal} className="btn-primary flex items-center gap-2">
          <Plus className="w-4 h-4" /> Create Bill
        </button>
      </div>

      <div className="flex items-center gap-4">
        <SearchInput value={search} onChange={setSearch} placeholder="Search bill number or patient..." />
        <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)} className="input-field w-40">
          <option value="">All Status</option>
          <option value="paid">Paid</option>
          <option value="unpaid">Unpaid</option>
          <option value="cancelled">Cancelled</option>
        </select>
      </div>

      {loading ? (
        <LoadingSpinner />
      ) : bills.length === 0 ? (
        <EmptyState
          icon={Receipt}
          title="No bills found"
          description="Create your first bill to start generating invoices."
          action={<button onClick={openCreateModal} className="btn-primary">Create Bill</button>}
        />
      ) : (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="glass-card overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="bg-surface-50">
                  {['Bill No.', 'Patient', 'Doctor', 'Total', 'Status', 'Payment', 'Date', 'Actions'].map((h) => (
                    <th key={h} className="px-5 py-3 text-left text-xs font-semibold text-surface-500 uppercase tracking-wider">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-surface-100">
                {bills.map((bill) => (
                  <tr key={bill.id} className="hover:bg-surface-50/50 transition-colors">
                    <td className="px-5 py-4 text-sm font-medium text-primary-600">{bill.bill_number}</td>
                    <td className="px-5 py-4 text-sm text-surface-700">{bill.patient?.name || 'N/A'}</td>
                    <td className="px-5 py-4 text-sm text-surface-600">{bill.doctor?.name ? `Dr. ${bill.doctor.name}` : '—'}</td>
                    <td className="px-5 py-4 text-sm font-semibold text-surface-800">₹{Number(bill.total).toLocaleString()}</td>
                    <td className="px-5 py-4"><StatusBadge status={bill.status} /></td>
                    <td className="px-5 py-4 text-sm text-surface-500 uppercase">{bill.payment_mode}</td>
                    <td className="px-5 py-4 text-sm text-surface-400">
                      {bill.created_at ? format(new Date(bill.created_at), 'dd MMM yy') : '-'}
                    </td>
                    <td className="px-5 py-4">
                      <div className="flex items-center gap-0.5">
                        <button onClick={() => viewBill(bill.id)} className="btn-ghost p-1.5" title="View"><Eye className="w-4 h-4 text-surface-500" /></button>
                        <button onClick={() => downloadPDF(bill.id)} className="btn-ghost p-1.5" title="Download PDF"><Download className="w-4 h-4 text-primary-500" /></button>
                        <button onClick={() => sendEmail(bill.id)} className="btn-ghost p-1.5" title="Email Receipt"><Mail className="w-4 h-4 text-emerald-500" /></button>
                        <button onClick={() => deleteBill(bill.id)} className="btn-ghost p-1.5" title="Delete"><Trash2 className="w-4 h-4 text-red-400" /></button>
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

      {/* ── Create Bill Modal ──────────────────────────────── */}
      <Modal isOpen={createModal} onClose={() => setCreateModal(false)} title="Create New Bill" size="xl">
        <form onSubmit={handleCreateBill} className="space-y-5">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="label-text">Patient *</label>
              <select required value={billForm.patient_id} onChange={(e) => setBillForm({ ...billForm, patient_id: e.target.value })} className="input-field">
                <option value="">Select Patient</option>
                {patients.map((p) => <option key={p.id} value={p.id}>{p.name} — {p.phone}</option>)}
              </select>
            </div>
            <div>
              <label className="label-text">Doctor</label>
              <select value={billForm.doctor_id} onChange={(e) => setBillForm({ ...billForm, doctor_id: e.target.value })} className="input-field">
                <option value="">Select Doctor (optional)</option>
                {doctors.map((d) => <option key={d.id} value={d.id}>Dr. {d.name} — ₹{d.consultation_fee}</option>)}
              </select>
            </div>
          </div>

          {/* Line Items */}
          <div>
            <div className="flex items-center justify-between mb-3">
              <label className="label-text mb-0">Bill Items *</label>
              <button type="button" onClick={addItem} className="text-sm text-primary-600 font-medium hover:text-primary-700">+ Add Item</button>
            </div>
            <div className="space-y-3">
              {billForm.items.map((item, i) => (
                <div key={i} className="flex gap-3 items-end p-3 bg-surface-50 rounded-xl">
                  <div className="flex-1">
                    <label className="text-xs text-surface-400">Select Test or Type</label>
                    <select value={item.medical_test_id} onChange={(e) => updateItem(i, 'medical_test_id', e.target.value)} className="input-field text-sm py-2">
                      <option value="">Custom Item</option>
                      {tests.map((t) => <option key={t.id} value={t.id}>{t.name} — ₹{t.price}</option>)}
                    </select>
                  </div>
                  <div className="flex-1">
                    <label className="text-xs text-surface-400">Description</label>
                    <input required value={item.description} onChange={(e) => updateItem(i, 'description', e.target.value)} className="input-field text-sm py-2" />
                  </div>
                  <div className="w-28">
                    <label className="text-xs text-surface-400">Price</label>
                    <input type="number" required min="0" step="0.01" value={item.unit_price} onChange={(e) => updateItem(i, 'unit_price', e.target.value)} className="input-field text-sm py-2" />
                  </div>
                  <div className="w-20">
                    <label className="text-xs text-surface-400">Qty</label>
                    <input type="number" min="1" value={item.quantity} onChange={(e) => updateItem(i, 'quantity', e.target.value)} className="input-field text-sm py-2" />
                  </div>
                  <button type="button" onClick={() => removeItem(i)} className="btn-ghost p-2 text-red-400 mb-0.5">
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              ))}
            </div>
          </div>

          {/* Payment Details */}
          <div className="grid grid-cols-4 gap-4">
            <div>
              <label className="label-text">Tax (%)</label>
              <input type="number" min="0" max="100" step="0.01" value={billForm.tax_percent} onChange={(e) => setBillForm({ ...billForm, tax_percent: e.target.value })} className="input-field" placeholder="18" />
            </div>
            <div>
              <label className="label-text">Discount (%)</label>
              <input type="number" min="0" max="100" step="0.01" value={billForm.discount_percent} onChange={(e) => setBillForm({ ...billForm, discount_percent: e.target.value })} className="input-field" />
            </div>
            <div>
              <label className="label-text">Payment Mode</label>
              <select value={billForm.payment_mode} onChange={(e) => setBillForm({ ...billForm, payment_mode: e.target.value })} className="input-field">
                <option value="cash">Cash</option>
                <option value="card">Card</option>
                <option value="upi">UPI</option>
                <option value="online">Online</option>
              </select>
            </div>
            <div>
              <label className="label-text">Status</label>
              <select value={billForm.status} onChange={(e) => setBillForm({ ...billForm, status: e.target.value })} className="input-field">
                <option value="paid">Paid</option>
                <option value="unpaid">Unpaid</option>
              </select>
            </div>
          </div>

          <div>
            <label className="label-text">Notes</label>
            <textarea value={billForm.notes} onChange={(e) => setBillForm({ ...billForm, notes: e.target.value })} className="input-field resize-none" rows={2} />
          </div>

          {/* Totals Preview */}
          <div className="bg-surface-50 rounded-xl p-4 space-y-2 text-sm">
            <div className="flex justify-between"><span className="text-surface-500">Subtotal</span><span className="font-medium">₹{subtotal.toLocaleString()}</span></div>
            {discountAmt > 0 && <div className="flex justify-between text-emerald-600"><span>Discount ({billForm.discount_percent}%)</span><span>- ₹{discountAmt.toFixed(2)}</span></div>}
            <div className="flex justify-between"><span className="text-surface-500">GST ({billForm.tax_percent || 18}%)</span><span>₹{taxAmt.toFixed(2)}</span></div>
            <div className="flex justify-between pt-2 border-t border-surface-200 text-base font-bold text-surface-800">
              <span>Grand Total</span><span>₹{grandTotal.toFixed(2)}</span>
            </div>
          </div>

          <div className="flex justify-end gap-3 pt-2">
            <button type="button" onClick={() => setCreateModal(false)} className="btn-secondary">Cancel</button>
            <button type="submit" className="btn-primary">Create Bill</button>
          </div>
        </form>
      </Modal>

      {/* ── Bill Detail Modal ──────────────────────────────── */}
      <Modal isOpen={detailModal} onClose={() => setDetailModal(false)} title={`Bill #${selectedBill?.bill_number || ''}`} size="lg">
        {selectedBill && (
          <div className="space-y-6">
            <div className="grid grid-cols-2 gap-6">
              <div>
                <p className="text-xs text-surface-400 mb-1">Patient</p>
                <p className="font-semibold text-surface-800">{selectedBill.patient?.name}</p>
                <p className="text-sm text-surface-500">{selectedBill.patient?.phone}</p>
              </div>
              <div>
                <p className="text-xs text-surface-400 mb-1">Doctor</p>
                <p className="font-semibold text-surface-800">{selectedBill.doctor?.name ? `Dr. ${selectedBill.doctor.name}` : 'N/A'}</p>
              </div>
            </div>

            <div className="overflow-x-auto border border-surface-200 rounded-xl">
              <table className="w-full">
                <thead>
                  <tr className="bg-surface-50">
                    <th className="px-4 py-2 text-xs text-left font-semibold text-surface-500">#</th>
                    <th className="px-4 py-2 text-xs text-left font-semibold text-surface-500">Description</th>
                    <th className="px-4 py-2 text-xs text-right font-semibold text-surface-500">Qty</th>
                    <th className="px-4 py-2 text-xs text-right font-semibold text-surface-500">Price</th>
                    <th className="px-4 py-2 text-xs text-right font-semibold text-surface-500">Total</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-surface-100">
                  {selectedBill.items?.map((item, i) => (
                    <tr key={item.id}>
                      <td className="px-4 py-2 text-sm text-surface-500">{i + 1}</td>
                      <td className="px-4 py-2 text-sm text-surface-800">{item.description}</td>
                      <td className="px-4 py-2 text-sm text-right">{item.quantity}</td>
                      <td className="px-4 py-2 text-sm text-right">₹{Number(item.unit_price).toLocaleString()}</td>
                      <td className="px-4 py-2 text-sm text-right font-medium">₹{Number(item.total).toLocaleString()}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="bg-surface-50 rounded-xl p-4 space-y-2 text-sm">
              <div className="flex justify-between"><span>Subtotal</span><span>₹{Number(selectedBill.subtotal).toLocaleString()}</span></div>
              {selectedBill.discount_amount > 0 && (
                <div className="flex justify-between text-emerald-600"><span>Discount ({selectedBill.discount_percent}%)</span><span>- ₹{Number(selectedBill.discount_amount).toLocaleString()}</span></div>
              )}
              <div className="flex justify-between"><span>GST ({selectedBill.tax_percent}%)</span><span>₹{Number(selectedBill.tax_amount).toLocaleString()}</span></div>
              <div className="flex justify-between pt-2 border-t border-surface-200 text-lg font-bold">
                <span>Total</span><span className="text-primary-600">₹{Number(selectedBill.total).toLocaleString()}</span>
              </div>
            </div>

            <div className="flex gap-3">
              <button onClick={() => downloadPDF(selectedBill.id)} className="btn-primary flex items-center gap-2">
                <Download className="w-4 h-4" /> Download PDF
              </button>
              <button onClick={() => sendEmail(selectedBill.id)} className="btn-secondary flex items-center gap-2">
                <Mail className="w-4 h-4" /> Send Receipt
              </button>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
}
