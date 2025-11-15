import React from 'react';
import { motion } from 'framer-motion';
import { useNavigate, useLocation } from 'react-router-dom';
import { LayoutDashboard, Files, Upload } from 'lucide-react';

const Layout = ({ children }) => {
  const navigate = useNavigate();
  const location = useLocation();

  const sidebar = [
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard, path: '/dashboard' },
    { id: 'files', label: 'Files', icon: Files, path: '/files' },
  ];

  return (
    <div className="min-h-screen flex bg-gradient-dark">
      {/* Sidebar */}
      <motion.aside
        initial={{ x: -300, opacity: 0 }}
        animate={{ x: 0, opacity: 1 }}
        className="w-64 p-6 glass-card m-4 rounded-3xl"
      >
        <div className="mb-8">
          <h1 className="text-2xl font-bold bg-gradient-to-r from-accent-indigo to-accent-teal bg-clip-text text-transparent">
            QuantumStore
          </h1>
          <p className="text-sm text-white/60 mt-1">File Intelligence</p>
        </div>

        <nav className="space-y-2">
          {sidebar.map((item) => (
            <button
              key={item.id}
              onClick={() => navigate(item.path)}
              className={location.pathname === item.path ? 'sidebar-item-active w-full' : 'sidebar-item w-full'}
              aria-label={item.label}
              aria-current={location.pathname === item.path ? 'page' : undefined}
            >
              <item.icon size={20} />
              <span>{item.label}</span>
            </button>
          ))}
        </nav>

        <div className="mt-auto pt-8">
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            className="btn-primary w-full flex items-center justify-center gap-2"
            onClick={() => navigate('/upload')}
          >
            <Upload size={20} />
            Upload Files
          </motion.button>
        </div>
      </motion.aside>

      {/* Main Content */}
      {children}
    </div>
  );
};

export default Layout;
