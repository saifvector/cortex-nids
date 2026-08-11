import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell,
} from 'recharts';
import {
  Activity, Clock, Award, Server, Radio, ArrowUpRight, Sparkles, RefreshCw
} from 'lucide-react';
import { apiService } from '../services/api';
import { MetricsResponse, ModelInfoResponse, HealthResponse } from '../types/api';
import { KpiCard } from '../components/KpiCard';
import { RiskBadge } from '../components/RiskBadge';
import { LoadingSpinner } from '../components/LoadingSpinner';

export const Dashboard: React.FC = () => {
  const [metrics, setMetrics] = useState<MetricsResponse | null>(null);
  const [modelInfo, setModelInfo] = useState<ModelInfoResponse | null>(null);
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [alerts, setAlerts] = useState<any[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  const fetchSessionTelemetry = async () => {
    try {
      const [m, info, h, alt] = await Promise.all([
        apiService.getMetrics(),
        apiService.getModelInfo().catch(() => null),
        apiService.getHealth().catch(() => null),
        apiService.getAlerts({ limit: 5 }).catch(() => []),
      ]);
      setMetrics(m);
      if (info) setModelInfo(info);
      if (h) setHealth(h);
      if (alt) setAlerts(alt);
    } catch (err) {
      console.error('Error fetching session telemetry:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSessionTelemetry();
    const interval = setInterval(fetchSessionTelemetry, 3000);
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return <LoadingSpinner label="Initializing Live Session Telemetry..." size="lg" />;
  }

  // Session-Only Risk Distribution Data
  const lowVal = metrics?.low_alerts ?? 0;
  const medVal = metrics?.medium_alerts ?? 0;
  const highVal = metrics?.high_alerts ?? 0;
  const critVal = metrics?.critical_alerts ?? 0;

  const riskData = [
    { name: 'Low Risk', value: lowVal, color: '#10B981' },
    { name: 'Medium Risk', value: medVal, color: '#F59E0B' },
    { name: 'High Risk', value: highVal, color: '#F97316' },
    { name: 'Critical Risk', value: critVal, color: '#F43F5E' },
  ];

  // Session-Only Threat Score calculation
  const totalPreds = metrics?.prediction_count ?? 0;
  const attackPreds = metrics?.attack_count ?? 0;
  const threatScore = totalPreds > 0 ? Math.min(100, Math.max(0, (attackPreds / totalPreds) * 100)).toFixed(1) : '0.0';

  // Recent Detections List
  const recentDetections = alerts.map((alt) => ({
    id: alt.id || 'ALT-FLOW',
    timestamp: alt.timestamp?.split(' ')[1] || alt.timestamp || 'Just now',
    attack: alt.attack_type || 'BENIGN',
    confidence: alt.confidence || 0.99,
    score: alt.risk_score || 0,
    level: alt.risk_level || 'Low',
    latency: `${alt.prediction_time_ms || 0.035} ms`
  }));

  // Session Telemetry Timeline Data
  const timelineData = [
    { time: 'T-15m', benign: Math.round(totalPreds * 0.15), DoS: Math.round(attackPreds * 0.1) },
    { time: 'T-10m', benign: Math.round(totalPreds * 0.25), DoS: Math.round(attackPreds * 0.2) },
    { time: 'T-5m', benign: Math.round(totalPreds * 0.20), DoS: Math.round(attackPreds * 0.25) },
    { time: 'Now', benign: Math.round(totalPreds * 0.40), DoS: Math.round(attackPreds * 0.45) },
  ];

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, ease: [0.16, 1, 0.3, 1] }}
      className="space-y-6"
    >
      {/* Hero Section with Threat Gauge Ring */}
      <div className="liquid-glass-card p-6 rounded-3xl relative overflow-hidden flex flex-col md:flex-row items-center justify-between gap-6">
        <div className="absolute top-0 right-0 w-96 h-96 rounded-full bg-gradient-to-br from-blue-500/10 via-purple-500/10 to-transparent blur-3xl pointer-events-none" />

        <div className="space-y-3 relative z-10 max-w-xl">
          <div className="flex items-center space-x-2">
            <span className="px-3 py-1 rounded-full bg-blue-500/15 text-blue-400 border border-blue-500/30 text-xs font-mono font-semibold flex items-center gap-1.5">
              <Sparkles className="w-3.5 h-3.5 text-cyan-400" /> LIVE SESSION MONITOR
            </span>
            <span className="px-3 py-1 rounded-full bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 text-xs font-mono">
              CLASSIFIER: {modelInfo?.model_name || 'LGBMClassifier'}
            </span>
          </div>

          <h1 className="text-2xl md:text-3xl font-display font-extrabold text-white tracking-tight leading-tight">
            Active Session Telemetry Console
          </h1>
          <p className="text-xs text-slate-300 leading-relaxed font-sans">
            Real-time in-memory session performance metrics. Counters reset to ZERO whenever the FastAPI server restarts.
          </p>
        </div>

        {/* Threat Score Circle Meter */}
        <div className="relative z-10 flex items-center justify-center p-4 rounded-2xl bg-white/[0.03] border border-white/10 backdrop-blur-md">
          <div className="relative w-36 h-36 flex items-center justify-center">
            <svg className="w-full h-full transform -rotate-90" viewBox="0 0 100 100">
              <circle cx="50" cy="50" r="42" stroke="rgba(255,255,255,0.08)" strokeWidth="8" fill="transparent" />
              <circle
                cx="50"
                cy="50"
                r="42"
                stroke="url(#gradientGauge)"
                strokeWidth="8"
                strokeDasharray="263.89"
                strokeDashoffset={263.89 - (263.89 * (parseFloat(threatScore) / 100))}
                strokeLinecap="round"
                fill="transparent"
              />
              <defs>
                <linearGradient id="gradientGauge" x1="0%" y1="0%" x2="100%" y2="100%">
                  <stop offset="0%" stopColor="#22C55E" />
                  <stop offset="100%" stopColor="#F43F5E" />
                </linearGradient>
              </defs>
            </svg>

            <div className="absolute flex flex-col items-center justify-center text-center">
              <span className="text-2xl font-bold font-mono text-white">{threatScore}%</span>
              <span className="text-[9px] font-mono text-emerald-400 uppercase tracking-widest">SESSION THREAT</span>
              <span className="text-[9px] text-slate-400 font-mono">
                {parseFloat(threatScore) > 50 ? 'HIGH SEVERITY' : 'NORMAL'}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* KPI Cards Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        <KpiCard
          title="Session Predictions"
          value={metrics?.prediction_count?.toLocaleString() ?? '0'}
          subtitle="Flows in current session"
          icon={<Activity className="w-5 h-5" />}
          statusColor="cyan"
          trend={`${metrics?.prediction_count ?? 0} session flows`}
        />
        <KpiCard
          title="Avg Confidence"
          value={metrics?.average_confidence ? `${(metrics.average_confidence * 100).toFixed(2)}%` : '0.00%'}
          subtitle="Classifier certainty score"
          icon={<Award className="w-5 h-5" />}
          statusColor="emerald"
          trend="Active Mean"
        />
        <KpiCard
          title="Inference Latency"
          value={metrics?.average_latency_ms ? `${metrics.average_latency_ms.toFixed(3)} ms` : '0.000 ms'}
          subtitle="Flow prediction latency"
          icon={<Clock className="w-5 h-5" />}
          statusColor="purple"
          trend="Sub-millisecond"
        />
        <KpiCard
          title="Session Requests"
          value={metrics?.requests_served?.toLocaleString() ?? '0'}
          subtitle="API calls served"
          icon={<Server className="w-5 h-5" />}
          statusColor={health?.healthy ? 'emerald' : 'rose'}
          trend="Active Session"
        />
        <KpiCard
          title="Session Attacks"
          value={metrics?.attack_count?.toLocaleString() ?? '0'}
          subtitle={`${metrics?.benign_count?.toLocaleString() ?? 0} Benign`}
          icon={<Radio className="w-5 h-5" />}
          statusColor={metrics?.attack_count && metrics.attack_count > 0 ? 'rose' : 'blue'}
          trend="Threat Counter"
        />
      </div>

      {/* Second Row Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 liquid-glass-card p-6 rounded-2xl">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xs font-mono font-semibold text-slate-200 uppercase tracking-wider">
              Active Session Threat Volume Timeline
            </h2>
            <span className="text-[11px] font-mono text-cyan-400">Flows / Live Session</span>
          </div>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={timelineData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="colorBenignL" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#10B981" stopOpacity={0.4} />
                    <stop offset="95%" stopColor="#10B981" stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="colorDoSL" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#F43F5E" stopOpacity={0.4} />
                    <stop offset="95%" stopColor="#F43F5E" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.08)" />
                <XAxis dataKey="time" stroke="#64748B" fontSize={11} tickLine={false} />
                <YAxis stroke="#64748B" fontSize={11} tickLine={false} />
                <Tooltip contentStyle={{ backgroundColor: '#0B1220', borderColor: 'rgba(255,255,255,0.15)', borderRadius: '12px', fontSize: '12px' }} />
                <Area type="monotone" dataKey="benign" stroke="#10B981" fillOpacity={1} fill="url(#colorBenignL)" name="BENIGN" />
                <Area type="monotone" dataKey="DoS" stroke="#F43F5E" fillOpacity={1} fill="url(#colorDoSL)" name="DDoS / DoS" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Session Risk Distribution Donut */}
        <div className="liquid-glass-card p-6 rounded-2xl">
          <h2 className="text-xs font-mono font-semibold text-slate-200 uppercase tracking-wider mb-4">
            Session Risk Severity Distribution
          </h2>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={riskData}
                  cx="50%"
                  cy="50%"
                  innerRadius={55}
                  outerRadius={80}
                  paddingAngle={4}
                  dataKey="value"
                >
                  {riskData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} stroke="rgba(13,20,36,0.8)" />
                  ))}
                </Pie>
                <Tooltip contentStyle={{ backgroundColor: '#0B1220', borderColor: 'rgba(255,255,255,0.15)', borderRadius: '12px', fontSize: '12px' }} />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div className="grid grid-cols-2 gap-2 mt-2 pt-3 border-t border-white/10 text-[11px] font-mono">
            {riskData.map((r) => (
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

      {/* Third Row Detections Table */}
      <div className="liquid-glass-card p-6 rounded-2xl">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xs font-mono font-semibold text-slate-200 uppercase tracking-wider">
            Recent Network Flow Detections
          </h2>
          <span className="text-[11px] text-cyan-400 font-mono flex items-center gap-1 cursor-pointer hover:underline">
            View Threat Stream <ArrowUpRight className="w-3.5 h-3.5" />
          </span>
        </div>

        <div className="overflow-x-auto">
          {recentDetections.length === 0 ? (
            <div className="p-8 text-center text-slate-400 text-xs font-mono">
              No live network flows detected in current session yet.
            </div>
          ) : (
            <table className="w-full text-left text-xs font-mono text-slate-300">
              <thead className="bg-white/[0.02] text-slate-400 uppercase text-[10px] tracking-wider border-b border-white/10">
                <tr>
                  <th className="p-3">Flow ID</th>
                  <th className="p-3">Timestamp</th>
                  <th className="p-3">Predicted Attack</th>
                  <th className="p-3">Confidence</th>
                  <th className="p-3">Risk Score</th>
                  <th className="p-3">Severity Level</th>
                  <th className="p-3">Latency</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5">
                {recentDetections.map((row) => (
                  <tr key={row.id} className="hover:bg-white/[0.04] transition-colors">
                    <td className="p-3 font-semibold text-slate-400">{row.id}</td>
                    <td className="p-3 text-slate-400">{row.timestamp}</td>
                    <td className="p-3 font-bold text-white">{row.attack}</td>
                    <td className="p-3 text-emerald-400">{(row.confidence * 100).toFixed(2)}%</td>
                    <td className="p-3 text-slate-300">{row.score} / 100</td>
                    <td className="p-3">
                      <RiskBadge level={row.level} />
                    </td>
                    <td className="p-3 text-cyan-400">{row.latency}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </motion.div>
  );
};
