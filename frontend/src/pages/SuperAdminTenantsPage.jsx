import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { 
  Building2, Search, Filter, MoreVertical, 
  CheckCircle2, XCircle, ArrowUpRight, ExternalLink,
  ShieldAlert, Settings2
} from 'lucide-react';
import { superadminAPI } from '../services/api';
import { LoadingSpinner, StatusBadge } from '../components/UI';
import { toast } from 'react-hot-toast';

export default function SuperAdminTenantsPage() {
  const [tenants, setTenants] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    loadTenants();
  }, []);

  const loadTenants = async () => {
    try {
      const res = await superadminAPI.listTenants();
      setTenants(res.data);
    } catch (err) {
      toast.error('Failed to load clinic list');
    } finally {
      setLoading(false);
    }
  };

  const toggleTenantStatus = async (tenantId, currentStatus) => {
    try {
      await superadminAPI.updateTenant(tenantId, { is_active: !currentStatus });
      setTenants(prev => prev.map(t => t.id === tenantId ? { ...t, is_active: !currentStatus } : t));
      toast.success(`Clinic ${!currentStatus ? 'enabled' : 'disabled'} successfully`);
    } catch (err) {
      toast.error('Failed to update clinic status');
    }
  };

  const filteredTenants = tenants.filter(t => 
    t.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    t.email.toLowerCase().includes(searchTerm.toLowerCase()) or
    t.slug.toLowerCase().includes(searchTerm.toLowerCase())
  );

  if (loading) return <LoadingSpinner />;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-surface-800">Clinic Management</h1>
          <p className="text-surface-400 mt-1">Manage all registered hospital and clinic tenants.</p>
        </div>
      </div>

      {/* Filters */}
      <div className="glass-card p-4 flex flex-col md:row items-center gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-surface-400" />
          <input
            type="text"
            placeholder="Search by clinic name, email or slug..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2 rounded-xl border border-surface-200 focus:border-primary-500 focus:ring-2 focus:ring-primary-500/20"
          />
        </div>
        <button className="flex items-center gap-2 px-4 py-2 border border-surface-200 rounded-xl text-surface-600 hover:bg-surface-50">
          <Filter className="w-4 h-4" />
          <span>Filters</span>
        </button>
      </div>

      {/* Tenant Table */}
      <div className="glass-card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="bg-surface-50 border-b border-surface-100">
                <th className="px-6 py-4 text-left text-xs font-semibold text-surface-500 uppercase">Hospital / Clinic</th>
                <th className="px-6 py-4 text-left text-xs font-semibold text-surface-500 uppercase">Plan</th>
                <th className="px-6 py-4 text-left text-xs font-semibold text-surface-500 uppercase">Stats</th>
                <th className="px-6 py-4 text-left text-xs font-semibold text-surface-500 uppercase">Revenue</th>
                <th className="px-6 py-4 text-left text-xs font-semibold text-surface-500 uppercase">Status</th>
                <th className="px-6 py-4 text-right text-xs font-semibold text-surface-500 uppercase">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-surface-100">
              {filteredTenants.map((t) => (
                <tr key={t.id} className="hover:bg-surface-50/50 transition-colors">
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-lg bg-primary-50 text-primary-600 flex items-center justify-center font-bold">
                        {t.name.charAt(0)}
                      </div>
                      <div>
                        <p className="text-sm font-semibold text-surface-800">{t.name}</p>
                        <p className="text-xs text-surface-400">{t.email}</p>
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <span className="inline-block px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider bg-violet-100 text-violet-700">
                      {t.subscription_plan}
                    </span>
                  </td>
                  <td className="px-6 py-4">
                    <div className="text-xs space-y-1">
                      <p><span className="text-surface-400">Users:</span> <span className="font-medium">{t.user_count}</span></p>
                      <p><span className="text-surface-400">Patients:</span> <span className="font-medium">{t.patient_count}</span></p>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <p className="text-sm font-bold text-emerald-600">₹{t.total_revenue.toLocaleString()}</p>
                    <p className="text-[10px] text-surface-400">{t.bill_count} bills generated</p>
                  </td>
                  <td className="px-6 py-4">
                    <button 
                      onClick={() => toggleTenantStatus(t.id, t.is_active)}
                      className="transition-transform active:scale-95"
                    >
                      {t.is_active ? (
                        <div className="flex items-center gap-1.5 text-emerald-600 bg-emerald-50 px-2 py-1 rounded-lg border border-emerald-100">
                          <CheckCircle2 className="w-4 h-4" />
                          <span className="text-xs font-medium">Active</span>
                        </div>
                      ) : (
                        <div className="flex items-center gap-1.5 text-red-600 bg-red-50 px-2 py-1 rounded-lg border border-red-100">
                          <XCircle className="w-4 h-4" />
                          <span className="text-xs font-medium">Disabled</span>
                        </div>
                      )}
                    </button>
                  </td>
                  <td className="px-6 py-4 text-right">
                    <div className="flex items-center justify-end gap-2">
                       <button className="p-2 text-surface-400 hover:text-primary-600 hover:bg-primary-50 rounded-lg transition-all" title="View Details">
                         <ExternalLink className="w-4 h-4" />
                       </button>
                       <button className="p-2 text-surface-400 hover:text-violet-600 hover:bg-violet-50 rounded-lg transition-all" title="Clinic Settings">
                         <Settings2 className="w-4 h-4" />
                       </button>
                    </div>
                  </td>
                </tr>
              ))}
              {filteredTenants.length === 0 && (
                <tr>
                  <td colSpan={6} className="px-6 py-12 text-center text-surface-400">
                    No clinics found matching your search.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
