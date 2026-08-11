import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, BarChart, Bar, Legend
} from 'recharts';
import {
  Database, ShieldAlert, Activity, Award, Clock, Calendar, Filter, Sparkles, AlertTriangle
} from 'lucide-react';
import { apiService } from '../services/api';
import { KpiCard } from '../components/KpiCard';
import { LoadingSpinner } from '../components/LoadingSpinner';

export const HistoricalAnalytics: React.FC = () => {
  const [timeRange, setTimeRange] = useState<string>('all');
  const [summary, setSummary] = useState<any>(null);
  const [trends, setTrends] = useState<any[]>([]);
  const [topAttacks, setTopAttacks] = useState<any[]>([]);
  const [severity, setSeverity] = useState<Record<string, number>>({ Critical: 0, High: 0, Medium: 0, Low: 0 });
  const [loading, setLoading] = useState<boolean>(true);

  const fetchHistoricalData = async () => {
    setLoading(true);
    try {
      const [sumRes, trRes, topRes, sevRes] = await Promise.all([
        apiService.getHistoricalSummary().catch(() => null),
        apiService.getHistoricalTrends(timeRange).catch(() => []),
        apiService.getHistoricalTopAttacks(10).catch(() => []),
        apiService.getHistoricalSeverity().catch(() => ({ Critical: 0, High: 0, Medium: 0, Low: 0 })),
      ]);
      setSummary(sumRes);
      setTrends(trRes);
      setTopAttacks(topRes);
      setSeverity(sevRes);
    } catch (err) {
      console.error('Error fetching historical analytics:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHistoricalData();
  }, [timeRange]);

  if (loading && !summary) {
    return <LoadingSpinner label="Loading Permanent SQLite Historical Analytics..." size="lg" />;
  }

  // Severity Distribution Pie Data
  const severityPieData = [
    { name: 'Critical', value: severity.Critical || 0, color: '#F43F5E' },
    { name: 'High', value: severity.High || 0, color: '#F97316' },
    { name: 'Medium', value: severity.Medium || 0, color: '#F59E0B' },
    { name: 'Low', value: severity.Low || 0, color: '#10B981' },
  ];

  // Top Attacks Pie Data (Top 5)
  const topAttacksPieColors = ['#3B82F6', '#8B5CF6', '#EC4899', '#F43F5E', '#10B981', '#F59E0B', '#6366F1'];
  const attackPieData = topAttacks.slice(0, 6).map((item, idx) => ({
    name: item.attack_type,
    value: item.count,
    color: topAttacksPieColors[idx % topAttacksPieColors.length],
  }));

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, ease: [0.16, 1, 0.3, 1] }}
      className="space-y-6"
    >
      {/* Header & Range Filters */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <span className="px-3 py-1 rounded-full bg-purple-500/15 text-purple-400 border border-purple-500/30 text-xs font-mono font-semibold flex items-center gap-1.5">
              <Database className="w-3.5 h-3.5 text-purple-400" /> SQLITE ALERTS.DB HISTORY
            </span>
          </div>
          <h1 className="text-xl md:text-2xl font-display font-extrabold text-white tracking-tight mt-1.5">
            Historical Threat & Telemetry Analytics
          </h1>
          <p className="text-xs text-slate-400 font-sans">
            Permanent database historical records, multi-window threat trends, and categorical severity distribution.
          </p>
        </div>

        {/* Time Range Filter Buttons */}
        <div className="flex items-center space-x-1 bg-white/[0.04] border border-white/10 p-1 rounded-xl">
          {[
            { id: '24h', label: 'Last 24 Hours' },
            { id: '7d', label: 'Last 7 Days' },
            { id: '30d', label: 'Last 30 Days' },
            { id: 'all', label: 'All Time' },
          ].map((btn) => (
            <button
              key={btn.id}
              onClick={() => setTimeRange(btn.id)}
              className={`px-3 py-1.5 rounded-lg text-xs font-mono transition-all ${
                timeRange === btn.id
                  ? 'bg-purple-600 text-white font-bold shadow-[0_0_15px_rgba(147,51,234,0.3)]'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              {btn.label}
            </button>
          ))}
        </div>
      </div>

      {/* KPI Cards Row (Permanent Historical Totals) */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        <KpiCard
          title="Total Flows Ever"
          value={summary?.total_flows_ever?.toLocaleString() ?? '0'}
          subtitle="All-time ingested network flows"
          icon={<Database className="w-5 h-5 text-purple-400" />}
          statusColor="purple"
          trend="Permanent Storage"
        />
        <KpiCard
          title="Total Attacks Ever"
          value={summary?.total_attacks_ever?.toLocaleString() ?? '0'}
          subtitle="All-time detected intrusions"
          icon={<ShieldAlert className="w-5 h-5 text-rose-400" />}
          statusColor="rose"
          trend="Cumulative Attacks"
        />
        <KpiCard
          title="Total Benign Ever"
          value={summary?.total_benign_ever?.toLocaleString() ?? '0'}
          subtitle="All-time clean traffic flows"
          icon={<Activity className="w-5 h-5 text-emerald-400" />}
          statusColor="emerald"
          trend="Normal Traffic"
        />
        <KpiCard
          title="Avg Confidence Ever"
          value={summary?.average_confidence_ever ? `${(summary.average_confidence_ever * 100).toFixed(2)}%` : '0.00%'}
          subtitle="All-time classifier mean"
          icon={<Award className="w-5 h-5 text-cyan-400" />}
          statusColor="cyan"
          trend="All-Time Precision"
        />
        <KpiCard
          title="Avg Latency Ever"
          value={summary?.average_latency_ever ? `${summary.average_latency_ever.toFixed(3)} ms` : '0.000 ms'}
          subtitle="All-time inference speed"
          icon={<Clock className="w-5 h-5 text-amber-400" />}
          statusColor="amber"
          trend="Historical Speed"
        />
      </div>

      {/* Charts Section: Attack Trend Line & Severity Breakdown */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Attack Trend Area Chart */}
        <div className="lg:col-span-2 liquid-glass-card p-6 rounded-2xl">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-xs font-mono font-semibold text-slate-200 uppercase tracking-wider">
                Historical Threat Volume & Attack Trend
              </h2>
              <p className="text-[11px] text-slate-400">Time-series flow aggregation from alerts.db</p>
            </div>
            <span className="text-[11px] font-mono text-purple-400 flex items-center gap-1">
              <Calendar className="w-3.5 h-3.5" /> Filter: {timeRange.toUpperCase()}
            </span>
          </div>

          <div className="h-72">
            {trends.length === 0 ? (
              <div className="h-full flex items-center justify-center text-slate-400 text-xs font-mono">
                No historical trend data points found for selected filter.
              </div>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={trends} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <defs>
                    <linearGradient id="colorHistBenign" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#10B981" stopOpacity={0.4} />
                      <stop offset="95%" stopColor="#10B981" stopOpacity={0} />
                    </linearGradient>
                    <linearGradient id="colorHistAttacks" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#F43F5E" stopOpacity={0.5} />
                      <stop offset="95%" stopColor="#F43F5E" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.08)" />
                  <XAxis dataKey="time" stroke="#64748B" fontSize={10} tickLine={false} />
                  <YAxis stroke="#64748B" fontSize={10} tickLine={false} />
                  <Tooltip contentStyle={{ backgroundColor: '#0B1220', borderColor: 'rgba(255,255,255,0.15)', borderRadius: '12px', fontSize: '12px' }} />
                  <Legend wrapperStyle={{ fontSize: '11px', fontFamily: 'monospace' }} />
                  <Area type="monotone" dataKey="benign" stroke="#10B981" fillOpacity={1} fill="url(#colorHistBenign)" name="Benign Traffic" />
                  <Area type="monotone" dataKey="attacks" stroke="#F43F5E" fillOpacity={1} fill="url(#colorHistAttacks)" name="Attacks Detected" />
                </AreaChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>

        {/* Severity Breakdown Donut */}
        <div className="liquid-glass-card p-6 rounded-2xl flex flex-col justify-between">
          <div>
            <h2 className="text-xs font-mono font-semibold text-slate-200 uppercase tracking-wider mb-1">
              Historical Severity Distribution
            </h2>
            <p className="text-[11px] text-slate-400 mb-4">Risk level classification breakdown</p>
          </div>

          <div className="h-60">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={severityPieData}
                  cx="50%"
                  cy="50%"
                  innerRadius={50}
                  outerRadius={75}
                  paddingAngle={4}
                  dataKey="value"
                >
                  {severityPieData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} stroke="rgba(13,20,36,0.8)" />
                  ))}
                </Pie>
                <Tooltip contentStyle={{ backgroundColor: '#0B1220', borderColor: 'rgba(255,255,255,0.15)', borderRadius: '12px', fontSize: '12px' }} />
              </PieChart>
            </ResponsiveContainer>
          </div>

          <div className="grid grid-cols-2 gap-2 pt-3 border-t border-white/10 text-[11px] font-mono">
            {severityPieData.map((r) => (
              <div key={r.name} className="flex items-center justify-between">
                <div className="flex items-center space-x-1.5">
                  <span className="w-2 h-2 rounded-full" style={{ backgroundColor: r.color }}></span>
                  <span className="text-slate-400">{r.name}</span>
                </div>
                <span className="text-white font-bold">{r.value.toLocaleString()}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Top Attack Categories Table & Distribution Pie */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Top Attacks Table */}
        <div className="lg:col-span-2 liquid-glass-card p-6 rounded-2xl">
          <h2 className="text-xs font-mono font-semibold text-slate-200 uppercase tracking-wider mb-4">
            Top Ranked Attack Categories (SQLite Permanent Database)
          </h2>

          <div className="overflow-x-auto">
            {topAttacks.length === 0 ? (
              <div className="p-8 text-center text-slate-400 text-xs font-mono">
                No attack records stored in alerts.db yet.
              </div>
            ) : (
              <table className="w-full text-left text-xs font-mono text-slate-300">
                <thead className="bg-white/[0.02] text-slate-400 uppercase text-[10px] tracking-wider border-b border-white/10">
                  <tr>
                    <th className="p-3">Rank</th>
                    <th className="p-3">Attack Category</th>
                    <th className="p-3">Total Occurrences</th>
                    <th className="p-3">Avg Confidence</th>
                    <th className="p-3">Avg Risk Score</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/5">
                  {topAttacks.map((item, idx) => (
                    <tr key={item.attack_type} className="hover:bg-white/[0.04] transition-colors">
                      <td className="p-3 font-semibold text-slate-400">#{idx + 1}</td>
                      <td className="p-3 font-bold text-white flex items-center gap-2">
                        {item.attack_type !== 'BENIGN' && (
                          <AlertTriangle className="w-3.5 h-3.5 text-rose-400" />
                        )}
                        {item.attack_type}
                      </td>
                      <td className="p-3 font-mono font-bold text-cyan-400">
                        {item.count.toLocaleString()}
                      </td>
                      <td className="p-3 text-emerald-400">
                        {(item.average_confidence * 100).toFixed(2)}%
                      </td>
                      <td className="p-3 text-amber-400">
                        {item.average_risk_score} / 100
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>

        {/* Attack Category Distribution Pie Chart */}
        <div className="liquid-glass-card p-6 rounded-2xl flex flex-col justify-between">
          <div>
            <h2 className="text-xs font-mono font-semibold text-slate-200 uppercase tracking-wider mb-1">
              Category Distribution
            </h2>
            <p className="text-[11px] text-slate-400 mb-4">Breakdown of top detected categories</p>
          </div>

          <div className="h-60">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={attackPieData}
                  cx="50%"
                  cy="50%"
                  innerRadius={0}
                  outerRadius={75}
                  dataKey="value"
                >
                  {attackPieData.map((entry, index) => (
                    <Cell key={`attack-cell-${index}`} fill={entry.color} stroke="rgba(13,20,36,0.8)" />
                  ))}
                </Pie>
                <Tooltip contentStyle={{ backgroundColor: '#0B1220', borderColor: 'rgba(255,255,255,0.15)', borderRadius: '12px', fontSize: '12px' }} />
              </PieChart>
            </ResponsiveContainer>
          </div>

          <div className="space-y-1.5 pt-3 border-t border-white/10 text-[11px] font-mono">
            {attackPieData.map((a) => (
              <div key={a.name} className="flex items-center justify-between">
                <div className="flex items-center space-x-1.5">
                  <span className="w-2 h-2 rounded-full" style={{ backgroundColor: a.color }}></span>
                  <span className="text-slate-400 truncate max-w-[140px]">{a.name}</span>
                </div>
                <span className="text-white font-bold">{a.value.toLocaleString()}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </motion.div>
  );
};
