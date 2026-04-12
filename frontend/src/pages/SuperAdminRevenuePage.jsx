import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { superadminAPI } from '../services/api';
import { LoadingSpinner } from '../components/UI';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import { TrendingUp, DollarSign, Activity } from 'lucide-react';
import { toast } from 'react-hot-toast';

export default function SuperAdminRevenuePage() {
  const [tenants, setTenants] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadTenants();
  }, []);

  const loadTenants = async () => {
    try {
      const res = await superadminAPI.listTenants();
      // Sort by highest revenue
      const sorted = res.data.sort((a, b) => b.total_revenue - a.total_revenue);
      setTenants(sorted);
    } catch (err) {
      toast.error('Failed to load clinic list');
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <LoadingSpinner />;

  const totalRevenue = tenants.reduce((acc, t) => acc + t.total_revenue, 0);
  const activeTenants = tenants.filter(t => t.total_revenue > 0).length;

  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-surface-800">Revenue Analytics</h1>
          <p className="text-surface-400 mt-1">Platform-wide clinic billing performance and comparisons.</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="glass-card p-6 border-violet-100">
          <div className="flex items-center gap-4 mb-4">
            <div className="w-12 h-12 rounded-xl bg-violet-100 text-violet-600 flex items-center justify-center">
               <DollarSign className="w-6 h-6" />
            </div>
            <div>
               <p className="text-xs font-bold text-surface-400 uppercase tracking-widest">Global Revenue</p>
               <p className="text-3xl font-bold text-surface-800">₹{totalRevenue.toLocaleString()}</p>
            </div>
          </div>
        </div>
        
        <div className="glass-card p-6 border-emerald-100">
          <div className="flex items-center gap-4 mb-4">
            <div className="w-12 h-12 rounded-xl bg-emerald-100 text-emerald-600 flex items-center justify-center">
               <TrendingUp className="w-6 h-6" />
            </div>
            <div>
               <p className="text-xs font-bold text-surface-400 uppercase tracking-widest">Revenue Generating Clinics</p>
               <p className="text-3xl font-bold text-surface-800">{activeTenants}</p>
            </div>
          </div>
        </div>

        <div className="glass-card p-6 border-primary-100">
          <div className="flex items-center gap-4 mb-4">
            <div className="w-12 h-12 rounded-xl bg-primary-100 text-primary-600 flex items-center justify-center">
               <Activity className="w-6 h-6" />
            </div>
            <div>
               <p className="text-xs font-bold text-surface-400 uppercase tracking-widest">Avg Revenue Per Clinic</p>
               <p className="text-3xl font-bold text-surface-800">₹{activeTenants > 0 ? Math.round(totalRevenue / activeTenants).toLocaleString() : 0}</p>
            </div>
          </div>
        </div>
      </div>

      <div className="glass-card p-6">
        <h2 className="text-lg font-bold text-surface-800 mb-6">Top 10 Clinic Revenue Leaderboard</h2>
        <div className="h-[400px] w-full">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={tenants.slice(0, 10)} margin={{ top: 20, right: 30, left: 20, bottom: 60 }}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
              <XAxis 
                dataKey="name" 
                tick={{ fill: '#64748b', fontSize: 12, fontWeight: 500 }} 
                axisLine={false} 
                tickLine={false} 
                angle={-45}
                textAnchor="end"
              />
              <YAxis 
                tickFormatter={(val) => `₹${val.toLocaleString()}`} 
                tick={{ fill: '#64748b', fontSize: 12, fontWeight: 600 }} 
                axisLine={false} 
                tickLine={false} 
              />
              <Tooltip 
                cursor={{ fill: '#f8fafc' }}
                contentStyle={{ borderRadius: '12px', border: '1px solid #e2e8f0', boxShadow: '0 10px 15px -3px rgb(0 0 0 / 0.1)' }}
                formatter={(value) => [`₹${value.toLocaleString()}`, 'Total Revenue']}
              />
              <Bar dataKey="total_revenue" radius={[8, 8, 0, 0]} maxBarSize={60}>
                {tenants.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={index === 0 ? '#10b981' : '#8b5cf6'} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </motion.div>
  );
}
