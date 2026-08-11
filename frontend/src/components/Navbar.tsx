import React, { useEffect, useState } from 'react';
import { Search, RefreshCw, CheckCircle2, AlertCircle, Clock, Bell, Zap } from 'lucide-react';
import { apiService } from '../services/api';
import { HealthResponse } from '../types/api';
import { notificationStore, SOCNotification } from '../services/notificationStore';
import { NotificationDrawer } from './NotificationDrawer';

export const Navbar: React.FC = () => {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [currentTime, setCurrentTime] = useState(new Date().toLocaleTimeString());

  // Notifications State
  const [notifications, setNotifications] = useState<SOCNotification[]>([]);
  const [isNotifOpen, setIsNotifOpen] = useState<boolean>(false);

  const checkHealth = async () => {
    try {
      const res = await apiService.getHealth();
      setHealth(res);
    } catch {
      setHealth({ healthy: false, version: '1.0.0', model_loaded: false, prediction_engine_status: 'offline' });
    }
  };

  // Global Refresh Handler (Refreshes Health + Triggers Page Re-fetch)
  const handleGlobalRefresh = async () => {
    setLoading(true);
    try {
      await checkHealth();
      await notificationStore.fetchRecentCriticalAlerts();
      // Dispatch global window refresh event for active page components
      window.dispatchEvent(new CustomEvent('cortex-nids-refresh', { detail: { timestamp: Date.now() } }));
    } catch (err) {
      console.error('Global refresh error:', err);
    } finally {
      setTimeout(() => setLoading(false), 500);
    }
  };

  useEffect(() => {
    checkHealth();

    // Subscribe to NotificationStore
    const unsubscribe = notificationStore.subscribe((notifs) => {
      setNotifications([...notifs]);
    });

    const healthInterval = setInterval(checkHealth, 30000);
    const clockInterval = setInterval(() => setCurrentTime(new Date().toLocaleTimeString()), 1000);

    return () => {
      unsubscribe();
      clearInterval(healthInterval);
      clearInterval(clockInterval);
    };
  }, []);

  const unreadCount = notificationStore.getUnreadCount();

  return (
    <header className="h-16 px-6 pt-4 pb-2 sticky top-0 z-20 flex items-center justify-between">
      {/* Search Input */}
      <div className="flex items-center space-x-3 w-80">
        <div className="relative w-full">
          <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
          <input
            type="text"
            placeholder="Search IP, flow hash, or rule... (⌘K)"
            className="w-full bg-white/[0.04] border border-white/10 rounded-xl pl-10 pr-4 py-2 text-xs text-slate-200 placeholder-slate-500 focus:border-blue-500/50 focus:outline-none focus:ring-1 focus:ring-blue-500/30 transition-all backdrop-blur-md"
          />
        </div>
      </div>

      {/* Right Controls */}
      <div className="flex items-center space-x-4 text-xs">
        {/* Clock */}
        <div className="hidden sm:flex items-center space-x-2 px-3 py-1.5 rounded-xl bg-white/[0.04] border border-white/10 text-slate-300 font-mono text-[11px]">
          <Clock className="w-3.5 h-3.5 text-cyan-400" />
          <span>{currentTime}</span>
        </div>

        {/* Backend Health Badge */}
        <div className="flex items-center space-x-2 px-3.5 py-1.5 rounded-xl bg-white/[0.04] border border-white/10">
          {health?.healthy ? (
            <>
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
              <span className="text-slate-300 font-mono text-[11px]">
                ML ENGINE: <strong className="text-emerald-400">ONLINE</strong>
              </span>
            </>
          ) : (
            <>
              <AlertCircle className="w-3.5 h-3.5 text-rose-400" />
              <span className="text-slate-300 font-mono text-[11px]">
                ML ENGINE: <strong className="text-rose-400">OFFLINE</strong>
              </span>
            </>
          )}
        </div>

        {/* Notifications Button */}
        <button
          onClick={() => setIsNotifOpen(true)}
          className="relative p-2 rounded-xl bg-white/[0.04] border border-white/10 text-slate-400 hover:text-white transition-colors"
          title="Open Notifications Panel"
        >
          <Bell className="w-4 h-4" />
          {unreadCount > 0 && (
            <span className="absolute -top-1 -right-1 px-1.5 py-0.5 rounded-full bg-rose-500 text-white font-mono font-bold text-[9px] shadow-[0_0_10px_rgba(244,63,94,0.6)]">
              {unreadCount > 9 ? '9+' : unreadCount}
            </span>
          )}
        </button>

        {/* Refresh Button */}
        <button
          onClick={handleGlobalRefresh}
          disabled={loading}
          className="p-2 rounded-xl bg-white/[0.04] border border-white/10 text-slate-400 hover:text-cyan-400 transition-colors"
          title="Refresh All Page Telemetry & Backend Status"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin text-cyan-400' : ''}`} />
        </button>
      </div>

      {/* Notification Panel Drawer */}
      <NotificationDrawer
        isOpen={isNotifOpen}
        onClose={() => setIsNotifOpen(false)}
        notifications={notifications}
      />
    </header>
  );
};
