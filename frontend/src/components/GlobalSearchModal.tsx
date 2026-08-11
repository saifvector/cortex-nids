import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Search, ShieldAlert, Navigation, ArrowRight, X, RefreshCw, Command } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { apiService } from '../services/api';
import { RiskBadge } from './RiskBadge';

interface GlobalSearchModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const GlobalSearchModal: React.FC<GlobalSearchModalProps> = ({ isOpen, onClose }) => {
  const [query, setQuery] = useState<string>('');
  const [results, setResults] = useState<any>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const navigate = useNavigate();

  // Reset query on open
  useEffect(() => {
    if (isOpen) {
      setQuery('');
      setResults(null);
    }
  }, [isOpen]);

  // Debounced API Search Execution
  useEffect(() => {
    if (!query.trim()) {
      setResults(null);
      setLoading(false);
      return;
    }

    setLoading(true);
    const timer = setTimeout(async () => {
      try {
        const res = await apiService.globalSearch(query.trim());
        setResults(res);
      } catch (err) {
        console.error('Global search API error:', err);
      } finally {
        setLoading(false);
      }
    }, 300);

    return () => clearTimeout(timer);
  }, [query]);

  // Hotkey Esc / Enter handlers
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const alerts = results?.alerts || [];
  const modules = results?.modules || [];
  const hasResults = alerts.length > 0 || modules.length > 0;

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-50 flex items-start justify-center pt-20 px-4">
        {/* Backdrop */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          onClick={onClose}
          className="fixed inset-0 bg-black/70 backdrop-blur-md"
        />

        {/* Search Modal Container */}
        <motion.div
          initial={{ opacity: 0, scale: 0.95, y: -10 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.95, y: -10 }}
          transition={{ duration: 0.2 }}
          className="relative w-full max-w-2xl bg-[#04070E]/95 border border-white/10 rounded-2xl p-6 shadow-2xl z-10 space-y-4 backdrop-blur-xl"
        >
          {/* Top Search Input Field */}
          <div className="relative flex items-center">
            <Search className="w-5 h-5 text-blue-400 absolute left-4 top-1/2 -translate-y-1/2" />
            <input
              autoFocus
              type="text"
              placeholder="Search threat alerts (IP, ID, Attack, Port) or system modules..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              className="w-full bg-white/[0.04] border border-blue-500/30 rounded-xl pl-12 pr-10 py-3 text-sm text-white placeholder-slate-400 font-sans focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 transition-all"
            />
            {query && (
              <button
                onClick={() => setQuery('')}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-white"
              >
                <X className="w-4 h-4" />
              </button>
            )}
          </div>

          {/* Quick Category Hints */}
          {!query && (
            <div className="p-4 rounded-xl bg-white/[0.02] border border-white/5 space-y-2 text-xs font-mono text-slate-400">
              <div className="flex items-center justify-between text-slate-300 font-bold mb-1">
                <span className="flex items-center gap-1.5 text-cyan-400">
                  <Command className="w-3.5 h-3.5" /> Quick System Search
                </span>
                <span className="text-[10px] text-slate-500">Press ESC to close</span>
              </div>
              <p className="text-[11px] text-slate-400">
                Try searching for IPs (<code className="text-purple-400">192.168.1.1</code>), attack types (<code className="text-purple-400">DDoS</code>, <code className="text-purple-400">PortScan</code>), destination ports (<code className="text-purple-400">80</code>), or modules (<code className="text-purple-400">Analytics</code>, <code className="text-purple-400">Reports</code>).
              </p>
            </div>
          )}

          {/* Results Area */}
          {loading && (
            <div className="py-12 text-center text-xs font-mono text-slate-400 flex items-center justify-center gap-2">
              <RefreshCw className="w-4 h-4 animate-spin text-blue-400" />
              Executing global database & module query...
            </div>
          )}

          {!loading && query && !hasResults && (
            <div className="py-12 text-center text-xs font-mono text-slate-400">
              No matching threat alerts or system modules found for "<strong className="text-white">{query}</strong>".
            </div>
          )}

          {!loading && query && hasResults && (
            <div className="space-y-4 max-h-96 overflow-y-auto pr-1">
              {/* System Navigation Modules Section */}
              {modules.length > 0 && (
                <div className="space-y-2">
                  <div className="text-[10px] font-mono font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1">
                    <Navigation className="w-3.5 h-3.5 text-blue-400" /> Application System Modules ({modules.length})
                  </div>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                    {modules.map((m: any) => (
                      <div
                        key={m.path}
                        onClick={() => {
                          navigate(m.path);
                          onClose();
                        }}
                        className="p-3 rounded-xl bg-white/[0.03] border border-white/10 hover:border-blue-500/50 hover:bg-white/[0.06] transition-all cursor-pointer flex items-center justify-between"
                      >
                        <div>
                          <span className="font-bold text-white text-xs block">{m.name}</span>
                          <span className="text-[10px] text-slate-400 font-sans">{m.description}</span>
                        </div>
                        <ArrowRight className="w-3.5 h-3.5 text-cyan-400 shrink-0 ml-2" />
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Database Threat Alerts Section */}
              {alerts.length > 0 && (
                <div className="space-y-2">
                  <div className="text-[10px] font-mono font-bold uppercase tracking-wider text-slate-400 flex items-center justify-between">
                    <span className="flex items-center gap-1">
                      <ShieldAlert className="w-3.5 h-3.5 text-purple-400" /> Threat Alerts in alerts.db ({results.total_alerts})
                    </span>
                    <button
                      onClick={() => {
                        navigate(`/historical-threats?search=${encodeURIComponent(query)}`);
                        onClose();
                      }}
                      className="text-cyan-400 hover:underline text-[10px]"
                    >
                      View All in Archive →
                    </button>
                  </div>

                  <div className="space-y-1.5">
                    {alerts.map((alt: any) => (
                      <div
                        key={alt.id}
                        onClick={() => {
                          navigate(`/historical-threats?search=${encodeURIComponent(alt.id)}`);
                          onClose();
                        }}
                        className="p-3 rounded-xl bg-[#0B1220]/60 border border-white/10 hover:border-purple-500/50 transition-colors cursor-pointer flex items-center justify-between font-mono text-xs"
                      >
                        <div className="flex items-center space-x-3">
                          <span className="font-bold text-purple-300">{alt.id}</span>
                          <span className="text-white font-semibold">{alt.attack_type}</span>
                          <span className="text-slate-400 text-[11px]">{alt.src_ip || '192.168.1.1'}</span>
                        </div>

                        <div className="flex items-center space-x-3">
                          <RiskBadge level={alt.risk_level} score={alt.risk_score} />
                          <span className="text-slate-500 text-[10px] hidden sm:inline">{alt.timestamp}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </motion.div>
      </div>
    </AnimatePresence>
  );
};
