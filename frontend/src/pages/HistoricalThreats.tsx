import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Database, Search, Download, Filter, ChevronLeft, ChevronRight, ShieldAlert, RefreshCw, FileSpreadsheet, FileJson
} from 'lucide-react';
import { RiskBadge } from '../components/RiskBadge';
import { apiService } from '../services/api';
import { LoadingSpinner } from '../components/LoadingSpinner';

interface ThreatAlert {
  id: string;
  timestamp: string;
  attack_type: string;
  confidence: number;
  risk_score: number;
  risk_level: 'Low' | 'Medium' | 'High' | 'Critical';
  src_ip: string;
  dst_ip: string;
  protocol: string;
  dst_port: number;
  prediction_time_ms: number;
}

export const HistoricalThreats: React.FC = () => {
  const [alerts, setAlerts] = useState<ThreatAlert[]>([]);
  const [totalCount, setTotalCount] = useState<number>(0);
  const [page, setPage] = useState<number>(1);
  const [totalPages, setTotalPages] = useState<number>(1);
  const [pageSize] = useState<number>(20);
  const [loading, setLoading] = useState<boolean>(true);

  // Filters & Search
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [timeRange, setTimeRange] = useState<string>('all');
  const [riskFilter, setRiskFilter] = useState<string>('All');
  const [attackFilter, setAttackFilter] = useState<string>('All');

  const [selectedAlert, setSelectedAlert] = useState<ThreatAlert | null>(null);

  const fetchThreatArchive = async () => {
    setLoading(true);
    try {
      const res = await apiService.getHistoricalThreats({
        page,
        page_size: pageSize,
        time_range: timeRange,
        risk_level: riskFilter !== 'All' ? riskFilter : undefined,
        attack_type: attackFilter !== 'All' ? attackFilter : undefined,
        search: searchQuery.trim() !== '' ? searchQuery.trim() : undefined,
      });

      if (res && Array.isArray(res.alerts)) {
        setAlerts(res.alerts);
        setTotalCount(res.total || 0);
        setTotalPages(res.total_pages || 1);
      }
    } catch (err) {
      console.error('Error fetching historical threat archive:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchThreatArchive();

    const handleGlobalRefresh = () => {
      fetchThreatArchive();
    };

    window.addEventListener('cortex-nids-refresh', handleGlobalRefresh);

    return () => {
      window.removeEventListener('cortex-nids-refresh', handleGlobalRefresh);
    };
  }, [page, timeRange, riskFilter, attackFilter]);

  // Debounced search trigger
  useEffect(() => {
    const timer = setTimeout(() => {
      setPage(1);
      fetchThreatArchive();
    }, 400);
    return () => clearTimeout(timer);
  }, [searchQuery]);

  const handleExportCsv = () => {
    const url = apiService.getExportHistoricalCsvUrl({
      time_range: timeRange,
      risk_level: riskFilter !== 'All' ? riskFilter : undefined,
      attack_type: attackFilter !== 'All' ? attackFilter : undefined,
      search: searchQuery.trim() !== '' ? searchQuery.trim() : undefined,
    });
    window.open(url, '_blank');
  };

  const handleExportJson = () => {
    const url = apiService.getExportHistoricalJsonUrl({
      time_range: timeRange,
      risk_level: riskFilter !== 'All' ? riskFilter : undefined,
      attack_type: attackFilter !== 'All' ? attackFilter : undefined,
      search: searchQuery.trim() !== '' ? searchQuery.trim() : undefined,
    });
    window.open(url, '_blank');
  };

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <span className="px-3 py-1 rounded-full bg-purple-500/15 text-purple-400 border border-purple-500/30 text-xs font-mono font-semibold flex items-center gap-1.5">
              <Database className="w-3.5 h-3.5 text-purple-400" /> PERMANENT ARCHIVE
            </span>
          </div>
          <h1 className="text-xl md:text-2xl font-display font-extrabold text-white tracking-tight mt-1.5">
            Historical Threat Alert Archive
          </h1>
          <p className="text-xs text-slate-400 font-sans">
            Filter, search, audit, and export permanent network intrusion alert logs stored in SQLite <code className="text-purple-400 font-mono">alerts.db</code>.
          </p>
        </div>

        {/* Export Actions */}
        <div className="flex items-center space-x-2">
          <button
            onClick={handleExportCsv}
            className="px-3.5 py-2 rounded-xl bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 hover:bg-emerald-500/20 text-xs font-semibold flex items-center gap-1.5 transition-all"
          >
            <FileSpreadsheet className="w-4 h-4 text-emerald-400" />
            <span>Export CSV</span>
          </button>

          <button
            onClick={handleExportJson}
            className="px-3.5 py-2 rounded-xl bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 hover:bg-cyan-500/20 text-xs font-semibold flex items-center gap-1.5 transition-all"
          >
            <FileJson className="w-4 h-4 text-cyan-400" />
            <span>Export JSON</span>
          </button>
        </div>
      </div>

      {/* Filter & Search Bar */}
      <div className="liquid-glass-card p-4 rounded-2xl space-y-4">
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3">
          {/* Search Box */}
          <div className="relative">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search IP, ID, or attack..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full bg-white/[0.03] border border-white/10 rounded-xl pl-9 pr-3 py-2 text-xs font-mono text-white placeholder-slate-500 focus:outline-none focus:border-purple-500 transition-colors"
            />
          </div>

          {/* Time Range Filter */}
          <select
            value={timeRange}
            onChange={(e) => { setTimeRange(e.target.value); setPage(1); }}
            className="bg-[#0B1220] border border-white/10 rounded-xl px-3 py-2 text-xs font-mono text-slate-300 focus:outline-none focus:border-purple-500"
          >
            <option value="all">Time: All History</option>
            <option value="24h">Time: Last 24 Hours</option>
            <option value="7d">Time: Last 7 Days</option>
            <option value="30d">Time: Last 30 Days</option>
          </select>

          {/* Severity Level Filter */}
          <select
            value={riskFilter}
            onChange={(e) => { setRiskFilter(e.target.value); setPage(1); }}
            className="bg-[#0B1220] border border-white/10 rounded-xl px-3 py-2 text-xs font-mono text-slate-300 focus:outline-none focus:border-purple-500"
          >
            <option value="All">Severity: All Levels</option>
            <option value="Critical">Critical Severity</option>
            <option value="High">High Severity</option>
            <option value="Medium">Medium Severity</option>
            <option value="Low">Low Severity</option>
          </select>

          {/* Category Filter */}
          <select
            value={attackFilter}
            onChange={(e) => { setAttackFilter(e.target.value); setPage(1); }}
            className="bg-[#0B1220] border border-white/10 rounded-xl px-3 py-2 text-xs font-mono text-slate-300 focus:outline-none focus:border-purple-500"
          >
            <option value="All">Category: All Attacks</option>
            <option value="BENIGN">BENIGN (Clean)</option>
            <option value="DoS Hulk">DoS Hulk</option>
            <option value="DDoS">DDoS</option>
            <option value="PortScan">PortScan</option>
            <option value="DoS GoldenEye">DoS GoldenEye</option>
            <option value="Bot">Botnet</option>
          </select>
        </div>
      </div>

      {/* Main Historical Table */}
      <div className="liquid-glass-card p-6 rounded-2xl space-y-4">
        <div className="flex items-center justify-between text-xs font-mono text-slate-400">
          <span>
            Total Historical Records Matching: <strong className="text-purple-400">{totalCount.toLocaleString()}</strong>
          </span>
          <span>
            Page <strong className="text-white">{page}</strong> of <strong className="text-white">{totalPages}</strong>
          </span>
        </div>

        <div className="overflow-x-auto">
          {loading ? (
            <div className="p-8 text-center text-slate-400 text-xs font-mono flex items-center justify-center gap-2">
              <RefreshCw className="w-4 h-4 animate-spin text-purple-400" />
              Querying permanent alerts.db database...
            </div>
          ) : alerts.length === 0 ? (
            <div className="p-8 text-center text-slate-400 text-xs font-mono">
              No historical threat alerts match your filter parameters.
            </div>
          ) : (
            <table className="w-full text-left text-xs font-mono text-slate-300">
              <thead className="bg-white/[0.02] text-slate-400 uppercase text-[10px] tracking-wider border-b border-white/10">
                <tr>
                  <th className="p-3">Alert ID</th>
                  <th className="p-3">Timestamp</th>
                  <th className="p-3">Source IP</th>
                  <th className="p-3">Dest Port</th>
                  <th className="p-3">Predicted Attack</th>
                  <th className="p-3">Confidence</th>
                  <th className="p-3">Risk Level</th>
                  <th className="p-3">Latency</th>
                  <th className="p-3 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5">
                {alerts.map((alt) => (
                  <tr key={alt.id} className="hover:bg-white/[0.04] transition-colors">
                    <td className="p-3 text-purple-300 font-semibold">{alt.id}</td>
                    <td className="p-3 text-slate-400">{alt.timestamp}</td>
                    <td className="p-3 text-slate-200">{alt.src_ip || '192.168.1.1'}</td>
                    <td className="p-3 text-slate-400">{alt.dst_port || 80}</td>
                    <td className="p-3 font-bold text-white">{alt.attack_type}</td>
                    <td className="p-3 text-emerald-400">{(alt.confidence * 100).toFixed(2)}%</td>
                    <td className="p-3">
                      <RiskBadge level={alt.risk_level} score={alt.risk_score} />
                    </td>
                    <td className="p-3 text-cyan-400">{alt.prediction_time_ms} ms</td>
                    <td className="p-3 text-right">
                      <button
                        onClick={() => setSelectedAlert(alt)}
                        className="px-2.5 py-1 rounded-lg bg-purple-500/10 text-purple-400 border border-purple-500/20 hover:bg-purple-500/20 text-[11px]"
                      >
                        Inspect
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        {/* Pagination Bar */}
        <div className="flex items-center justify-between pt-3 border-t border-white/10 text-xs font-mono">
          <button
            disabled={page <= 1}
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            className="px-3 py-1.5 rounded-lg bg-white/[0.04] border border-white/10 text-slate-300 hover:bg-white/10 disabled:opacity-40 disabled:cursor-not-allowed flex items-center gap-1"
          >
            <ChevronLeft className="w-4 h-4" /> Previous
          </button>

          <span className="text-slate-400">
            Page {page} / {totalPages}
          </span>

          <button
            disabled={page >= totalPages}
            onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
            className="px-3 py-1.5 rounded-lg bg-white/[0.04] border border-white/10 text-slate-300 hover:bg-white/10 disabled:opacity-40 disabled:cursor-not-allowed flex items-center gap-1"
          >
            Next <ChevronRight className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Inspect Modal Drawer */}
      {selectedAlert && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-md flex items-center justify-center z-50 p-4">
          <motion.div
            initial={{ scale: 0.95, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            className="liquid-glass-card p-6 rounded-2xl max-w-lg w-full space-y-4"
          >
            <div className="flex items-center justify-between border-b border-white/10 pb-3">
              <div className="flex items-center space-x-2">
                <ShieldAlert className="w-5 h-5 text-purple-400" />
                <h3 className="font-bold text-white text-base">Historical Alert: {selectedAlert.id}</h3>
              </div>
              <button
                onClick={() => setSelectedAlert(null)}
                className="text-slate-400 hover:text-white text-sm"
              >
                ✕
              </button>
            </div>

            <div className="space-y-3 font-mono text-xs text-slate-300">
              <div className="flex justify-between p-2.5 rounded-xl bg-[#04070E]/60 border border-white/10">
                <span className="text-slate-400">Timestamp Logged</span>
                <span className="font-bold text-white">{selectedAlert.timestamp}</span>
              </div>
              <div className="flex justify-between p-2.5 rounded-xl bg-[#04070E]/60 border border-white/10">
                <span className="text-slate-400">Predicted Category</span>
                <span className="font-bold text-white">{selectedAlert.attack_type}</span>
              </div>
              <div className="flex justify-between p-2.5 rounded-xl bg-[#04070E]/60 border border-white/10">
                <span className="text-slate-400">Risk Severity Level</span>
                <RiskBadge level={selectedAlert.risk_level} score={selectedAlert.risk_score} />
              </div>
              <div className="flex justify-between p-2.5 rounded-xl bg-[#04070E]/60 border border-white/10">
                <span className="text-slate-400">Classification Confidence</span>
                <span className="text-emerald-400 font-bold">{(selectedAlert.confidence * 100).toFixed(2)}%</span>
              </div>
              <div className="flex justify-between p-2.5 rounded-xl bg-[#04070E]/60 border border-white/10">
                <span className="text-slate-400">Inference Latency</span>
                <span className="text-cyan-400">{selectedAlert.prediction_time_ms} ms</span>
              </div>
              <div className="flex justify-between p-2.5 rounded-xl bg-[#04070E]/60 border border-white/10">
                <span className="text-slate-400">Source Host IP</span>
                <span className="text-slate-200">{selectedAlert.src_ip || '192.168.1.1'}</span>
              </div>
              <div className="flex justify-between p-2.5 rounded-xl bg-[#04070E]/60 border border-white/10">
                <span className="text-slate-400">Target Port</span>
                <span className="text-slate-200">{selectedAlert.dst_port || 80}</span>
              </div>
            </div>

            <div className="pt-3 flex justify-end">
              <button
                onClick={() => setSelectedAlert(null)}
                className="px-4 py-2 rounded-xl bg-purple-600 hover:bg-purple-500 text-white font-bold text-xs"
              >
                Close Record
              </button>
            </div>
          </motion.div>
        </div>
      )}
    </div>
  );
};
