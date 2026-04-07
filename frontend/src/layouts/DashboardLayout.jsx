import { Outlet } from 'react-router-dom';
import Sidebar from '../components/Sidebar';
import { Toaster } from 'react-hot-toast';

export default function DashboardLayout() {
  return (
    <div className="min-h-screen bg-surface-50">
      <Toaster
        position="top-right"
        toastOptions={{
          style: {
            borderRadius: '12px',
            background: '#1e293b',
            color: '#f8fafc',
            fontSize: '14px',
          },
          duration: 3000,
        }}
      />
      <Sidebar />
      <main className="ml-[272px] transition-all duration-300 min-h-screen">
        <div className="p-8">
          <Outlet />
        </div>
      </main>
    </div>
  );
}
