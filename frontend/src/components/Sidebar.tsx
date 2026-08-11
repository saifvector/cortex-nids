import React from 'react';
import { NavLink } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  LayoutDashboard,
  Activity,
  ShieldAlert,
  UploadCloud,
  BarChart3,
  Layers,
  Cpu,
  FileText,
  Settings,
  Shield,
  Sparkles,
  Database
} from 'lucide-react';

export const Sidebar: React.FC = () => {
  const navItems = [
    { to: '/', label: 'Dashboard (Live)', icon: <LayoutDashboard className="w-4 h-4" /> },
    { to: '/live-threats', label: 'Live Threats', icon: <Activity className="w-4 h-4" /> },
    { to: '/historical-threats', label: 'Historical Threats', icon: <Database className="w-4 h-4" /> },
    { to: '/analytics', label: 'Historical Analytics', icon: <BarChart3 className="w-4 h-4" /> },
    { to: '/predict', label: 'Single Prediction', icon: <ShieldAlert className="w-4 h-4" /> },
    { to: '/batch', label: 'Batch Analysis', icon: <UploadCloud className="w-4 h-4" /> },
    { to: '/features', label: 'Feature Importance', icon: <Layers className="w-4 h-4" /> },
    { to: '/model', label: 'Model Insights', icon: <Cpu className="w-4 h-4" /> },
    { to: '/reports', label: 'Reports', icon: <FileText className="w-4 h-4" /> },
    { to: '/settings', label: 'Settings', icon: <Settings className="w-4 h-4" /> },
  ];

  return (
    <aside className="w-64 p-4 h-screen sticky top-0 z-30 flex flex-col">
      {/* Floating Glass Container */}
      <div className="liquid-glass rounded-2xl flex-1 flex flex-col overflow-hidden relative">
        {/* Ambient Top Glow */}
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-32 h-1 bg-gradient-to-r from-transparent via-blue-500 to-transparent blur-[2px]" />

        {/* Brand Header */}
        <div className="p-5 border-b border-white/10 flex items-center space-x-3">
          <div className="p-2.5 rounded-xl bg-gradient-to-br from-blue-500/20 to-purple-500/20 border border-white/20 text-cyan-400 shadow-[0_0_20px_rgba(59,130,246,0.3)]">
            <Shield className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center space-x-1.5">
              <h1 className="font-display font-bold text-white text-sm tracking-wider">CORTEX</h1>
              <Sparkles className="w-3 h-3 text-cyan-400 animate-pulse" />
            </div>
            <p className="text-[10px] text-slate-400 font-mono tracking-widest uppercase">AI XDR PLATFORM</p>
          </div>
        </div>

        {/* Navigation Menu */}
        <nav className="flex-1 p-3 space-y-1.5 overflow-y-auto">
          <div className="px-3 py-2 text-[10px] font-mono font-semibold text-slate-500 uppercase tracking-widest">
            Security Intelligence
          </div>
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                `relative flex items-center space-x-3 px-3.5 py-2.5 rounded-xl text-xs font-medium transition-all duration-200 ${
                  isActive
                    ? 'text-white font-semibold shadow-[0_0_20px_rgba(59,130,246,0.25)]'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-white/5'
                }`
              }
            >
              {({ isActive }) => (
                <>
                  {isActive && (
                    <motion.div
                      layoutId="activeTab"
                      className="absolute inset-0 bg-gradient-to-r from-blue-600/30 to-purple-600/20 rounded-xl border border-white/20"
                      transition={{ type: 'spring', stiffness: 400, damping: 30 }}
                    />
                  )}
                  <span className="relative z-10">{item.icon}</span>
                  <span className="relative z-10 font-sans">{item.label}</span>
                </>
              )}
            </NavLink>
          ))}
        </nav>

        {/* Footer Status Badge */}
        <div className="p-4 border-t border-white/10 bg-white/[0.02]">
          <div className="flex items-center justify-between text-xs">
            <div className="flex items-center space-x-2">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse shadow-[0_0_10px_rgba(16,185,129,0.5)]"></span>
              <span className="text-slate-300 font-mono text-[11px]">SOC Engine Active</span>
            </div>
            <span className="text-[10px] font-mono text-cyan-400 font-semibold">v2.0</span>
          </div>
        </div>
      </div>
    </aside>
  );
};
