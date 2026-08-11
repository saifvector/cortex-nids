import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Bell, CheckCheck, Trash2, ShieldAlert, X, ChevronRight } from 'lucide-react';
import { SOCNotification, notificationStore } from '../services/notificationStore';
import { RiskBadge } from './RiskBadge';

interface NotificationDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  notifications: SOCNotification[];
  onSelectNotification?: (notif: SOCNotification) => void;
}

export const NotificationDrawer: React.FC<NotificationDrawerProps> = ({
  isOpen,
  onClose,
  notifications,
  onSelectNotification,
}) => {
  if (!isOpen) return null;

  const unreadCount = notifications.filter((n) => !n.read).length;

  const handleMarkAllRead = () => {
    notificationStore.markAllAsRead();
  };

  const handleClearAll = () => {
    notificationStore.clearAll();
  };

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-50 flex justify-end">
        {/* Backdrop */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          onClick={onClose}
          className="fixed inset-0 bg-black/60 backdrop-blur-sm"
        />

        {/* Drawer Panel */}
        <motion.div
          initial={{ x: '100%' }}
          animate={{ x: 0 }}
          exit={{ x: '100%' }}
          transition={{ type: 'spring', stiffness: 350, damping: 30 }}
          className="relative w-full max-w-md h-full bg-[#04070E]/95 border-l border-white/10 p-6 flex flex-col justify-between z-10 shadow-2xl backdrop-blur-xl"
        >
          <div className="flex flex-col h-full space-y-4">
            {/* Header */}
            <div className="flex items-center justify-between border-b border-white/10 pb-4">
              <div className="flex items-center space-x-2">
                <div className="p-2 rounded-xl bg-blue-500/10 border border-blue-500/20 text-cyan-400">
                  <Bell className="w-5 h-5" />
                </div>
                <div>
                  <h2 className="text-base font-bold text-white font-display">SOC Security Alerts</h2>
                  <p className="text-[11px] text-slate-400 font-mono">
                    {unreadCount > 0 ? `${unreadCount} Unread Security Incident(s)` : 'All System Alerts Read'}
                  </p>
                </div>
              </div>

              <button
                onClick={onClose}
                className="p-1.5 rounded-lg bg-white/[0.04] text-slate-400 hover:text-white border border-white/10"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Quick Actions Bar */}
            <div className="flex items-center justify-between text-xs font-mono">
              <button
                onClick={handleMarkAllRead}
                disabled={notifications.length === 0}
                className="text-cyan-400 hover:text-cyan-300 disabled:opacity-40 flex items-center gap-1 font-semibold"
              >
                <CheckCheck className="w-3.5 h-3.5" /> Mark All Read
              </button>

              <button
                onClick={handleClearAll}
                disabled={notifications.length === 0}
                className="text-rose-400 hover:text-rose-300 disabled:opacity-40 flex items-center gap-1 font-semibold"
              >
                <Trash2 className="w-3.5 h-3.5" /> Clear All
              </button>
            </div>

            {/* Notification Items List */}
            <div className="flex-1 overflow-y-auto space-y-3 pr-1">
              {notifications.length === 0 ? (
                <div className="py-20 text-center text-slate-500 text-xs font-mono space-y-2">
                  <ShieldAlert className="w-10 h-10 mx-auto opacity-30 text-blue-400" />
                  <p>No security alert notifications received yet.</p>
                </div>
              ) : (
                notifications.map((notif) => (
                  <div
                    key={notif.id}
                    onClick={() => {
                      notificationStore.markAsRead(notif.id);
                      if (onSelectNotification) onSelectNotification(notif);
                    }}
                    className={`p-3.5 rounded-xl border transition-all cursor-pointer space-y-2 ${
                      notif.read
                        ? 'bg-[#0B1220]/40 border-white/5 opacity-70'
                        : 'bg-white/[0.04] border-blue-500/30 shadow-[0_0_15px_rgba(59,130,246,0.15)]'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-white text-xs flex items-center gap-1.5">
                        {!notif.read && <span className="w-2 h-2 rounded-full bg-cyan-400 animate-ping"></span>}
                        {notif.title}
                      </span>
                      <RiskBadge level={notif.risk_level} score={notif.risk_score} />
                    </div>

                    <p className="text-[11px] text-slate-300 font-sans">{notif.message}</p>

                    <div className="flex items-center justify-between text-[10px] font-mono text-slate-400 pt-1 border-t border-white/5">
                      <span>{notif.timestamp}</span>
                      <span className="text-cyan-400 flex items-center gap-0.5">
                        Inspect <ChevronRight className="w-3 h-3" />
                      </span>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  );
};
