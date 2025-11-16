import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Layout from './components/ui/Layout';
import Dashboard from './components/ui/Dashboard';
import Files from './components/ui/Files';
import Upload from './components/ui/Upload';
import GroupsExplorer from './components/groups/GroupsExplorer';
import './styles/globals.css';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        <Route path="/dashboard" element={<Layout><Dashboard /></Layout>} />
        <Route path="/files" element={<Layout><Files /></Layout>} />
        <Route path="/upload" element={<Layout><Upload /></Layout>} />
        <Route path="/groups" element={<Layout><GroupsExplorer /></Layout>} />
      </Routes>
    </Router>
  );
}

export default App;
