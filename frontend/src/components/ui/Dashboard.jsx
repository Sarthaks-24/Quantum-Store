import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { motion } from 'framer-motion';
import { 
  Files,
  FolderOpen,
  Image,
  FileText,
  Video,
  Music,
  Database,
  TrendingUp,
  Clock,
  HardDrive
} from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { fetchSummary, fetchRecentFiles, fetchFiles, computeWeeklyActivity, normalizeWeeklyActivity } from '../../api';
import PreviewModal from './PreviewModal';

const COLORS = ['#7c3aed', '#06b6d4', '#f59e0b', '#10b981', '#ef4444', '#8b5cf6'];

// Extracted StatCard Component
const StatCard = React.memo(({ stat, index }) => (
  <motion.div
    initial={{ y: 20, opacity: 0 }}
    animate={{ y: 0, opacity: 1 }}
    transition={{ delay: index * 0.1 }}
    className="stat-card"
  >
    <div className="flex items-start justify-between mb-4">
      <div className={`p-3 rounded-xl bg-${stat.color}-500/20`}>
        <stat.icon className={`text-${stat.color}-400`} size={24} />
      </div>
      <span className="text-green-400 text-sm font-medium">{stat.change}</span>
    </div>
    <h3 className="text-white/60 text-sm mb-1">{stat.title}</h3>
    <p className="text-3xl font-bold">{stat.value}</p>
  </motion.div>
));
StatCard.displayName = 'StatCard';

// Extracted FileCard Component
const FileCard = React.memo(({ file, index, formatSize, onSelect }) => {
  const getFileIcon = (type) => {
    switch (type) {
      case 'image': return Image;
      case 'pdf': return FileText;
      case 'video': return Video;
      case 'audio': return Music;
      case 'json': return Database;
      default: return Files;
    }
  };

  const Icon = getFileIcon(file.classification?.type);

  const handleClick = useCallback(() => {
    onSelect(file);
  }, [file, onSelect]);

  const handleKeyDown = useCallback((e) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      onSelect(file);
    }
  }, [file, onSelect]);

  return (
    <motion.div
      initial={{ scale: 0.9, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      transition={{ delay: 0.5 + index * 0.05 }}
      whileHover={{ scale: 1.02 }}
      onClick={handleClick}
      onKeyDown={handleKeyDown}
      className="glass-card-hover p-4 cursor-pointer"
      role="button"
      tabIndex={0}
      aria-label={`View ${file.filename}`}
    >
      <div className="flex items-start gap-3">
        <div className="p-2 bg-accent-indigo/20 rounded-lg">
          <Icon size={20} className="text-accent-indigo" />
        </div>
        <div className="flex-1 min-w-0">
          <h4 className="font-medium truncate">{file.filename || 'Unnamed'}</h4>
          <p className="text-sm text-white/60 truncate">
            {file.classification?.category || 'Uncategorized'}
          </p>
          <p className="text-xs text-white/40 mt-1">
            {formatSize(file.size || 0)}
          </p>
        </div>
      </div>
    </motion.div>
  );
});
FileCard.displayName = 'FileCard';

const Dashboard = () => {
  const [summary, setSummary] = useState(null);
  const [recentFiles, setRecentFiles] = useState([]);
  const [selectedFile, setSelectedFile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activityData, setActivityData] = useState([]);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = useCallback(async () => {
    setLoading(true);
    try {
      const [summaryData, filesData, allFiles] = await Promise.all([
        fetchSummary(),
        fetchRecentFiles(100),
        fetchFiles()
      ]);
      setSummary(summaryData);
      // Sort by newest first and take only last 10
      const sortedFiles = [...filesData].sort((a, b) => {
        const dateA = new Date(a.uploaded_at || 0);
        const dateB = new Date(b.uploaded_at || 0);
        return dateB - dateA;
      });
      setRecentFiles(sortedFiles.slice(0, 10));
      
      // Compute weekly activity from all files and normalize
      const weeklyData = normalizeWeeklyActivity(computeWeeklyActivity(allFiles));
      setActivityData(weeklyData);
    } catch (error) {
      console.error('Failed to load dashboard data:', error);
      // Fallback to static data for weekly activity
      setActivityData([
        { name: 'Mon', uploads: 0 },
        { name: 'Tue', uploads: 0 },
        { name: 'Wed', uploads: 0 },
        { name: 'Thu', uploads: 0 },
        { name: 'Fri', uploads: 0 },
        { name: 'Sat', uploads: 0 },
        { name: 'Sun', uploads: 0 }
      ]);
    } finally {
      setLoading(false);
    }
  }, []);

  // Format file size
  const formatSize = useCallback((bytes) => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  }, []);

  const handleFileSelect = useCallback((file) => {
    setSelectedFile(file);
  }, []);

  const handleClosePreview = useCallback(() => {
    setSelectedFile(null);
  }, []);

  // Stats cards data (memoized)
  const stats = useMemo(() => [
    {
      title: 'Total Files',
      value: summary?.totalFiles || 0,
      icon: Files,
      color: 'indigo',
      change: '+12%'
    },
    {
      title: 'Storage Used',
      value: summary ? formatSize(summary.totalSize) : '0 B',
      icon: HardDrive,
      color: 'teal',
      change: '+8%'
    },
    {
      title: 'Images',
      value: summary?.totalImages || 0,
      icon: Image,
      color: 'amber',
      change: '+15%'
    },
    {
      title: 'Documents',
      value: (summary?.totalPDFs || 0) + (summary?.totalJSON || 0),
      icon: FileText,
      color: 'green',
      change: '+5%'
    }
  ], [summary, formatSize]);

  // Chart data (memoized)
  const typeDistribution = useMemo(() => 
    summary?.byType ? Object.entries(summary.byType).map(([name, value]) => ({
      name: name.charAt(0).toUpperCase() + name.slice(1),
      value
    })) : [],
    [summary]
  );

  return (
    <main className="flex-1 p-6 overflow-y-auto scrollbar-hide">
      {/* Top Bar */}
      <motion.div
        initial={{ y: -20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        className="glass-card rounded-2xl p-4 mb-6 flex items-center justify-between"
      >
        <div>
            <h2 className="text-2xl font-bold">Welcome back!</h2>
            <p className="text-white/60 text-sm mt-1">Here's what's happening with your files</p>
          </div>
          <div className="flex items-center gap-4">
            <div className="glass-card px-4 py-2 rounded-xl">
              <span className="text-sm text-white/80">Last sync: 2 min ago</span>
            </div>
          </div>
        </motion.div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-6">
          {stats.map((stat, index) => (
            <StatCard key={stat.title} stat={stat} index={index} />
          ))}
        </div>

        {/* Charts Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
          {/* Activity Chart */}
          <motion.div
            initial={{ scale: 0.95, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ delay: 0.2 }}
            className="glass-card p-6 rounded-2xl"
          >
            <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <TrendingUp size={20} className="text-accent-teal" />
              Weekly Activity
            </h3>
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={activityData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#ffffff20" />
                <XAxis dataKey="name" stroke="#ffffff60" />
                <YAxis stroke="#ffffff60" />
                <Tooltip
                  contentStyle={{
                    background: 'rgba(15, 23, 42, 0.9)',
                    border: '1px solid rgba(255,255,255,0.1)',
                    borderRadius: '12px',
                    backdropFilter: 'blur(10px)'
                  }}
                />
                <Bar dataKey="uploads" fill="#7c3aed" radius={[8, 8, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </motion.div>

          {/* Type Distribution */}
          <motion.div
            initial={{ scale: 0.95, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ delay: 0.3 }}
            className="glass-card p-6 rounded-2xl"
          >
            <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <Database size={20} className="text-accent-indigo" />
              File Types
            </h3>
            <ResponsiveContainer width="100%" height={250}>
              <PieChart>
                <Pie
                  data={typeDistribution}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {typeDistribution.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{
                    background: 'rgba(15, 23, 42, 0.9)',
                    border: '1px solid rgba(255,255,255,0.1)',
                    borderRadius: '12px'
                  }}
                />
              </PieChart>
            </ResponsiveContainer>
          </motion.div>
        </div>

        {/* Recent Files */}
        <motion.div
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.4 }}
          className="glass-card p-6 rounded-2xl"
        >
          <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <Clock size={20} className="text-accent-teal" />
            Recent Uploads
          </h3>

          {loading ? (
            <div className="text-center py-8 text-white/60">Loading...</div>
          ) : recentFiles.length === 0 ? (
            <div className="text-center py-8">
              <FolderOpen size={48} className="mx-auto text-white/30 mb-3" />
              <p className="text-white/60">No files yet. Upload your first file!</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {recentFiles.map((file, index) => (
                <FileCard
                  key={file.id || index}
                  file={file}
                  index={index}
                  formatSize={formatSize}
                  onSelect={handleFileSelect}
                />
              ))}
            </div>
          )}
        </motion.div>

      {/* Preview Modal */}
      {selectedFile && (
        <PreviewModal
          file={selectedFile}
          onClose={handleClosePreview}
        />
      )}
    </main>
  );
};

export default Dashboard;
