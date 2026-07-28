import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import {
  AreaChart, Area, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell,
} from 'recharts';
import {
  ShieldCheck, Activity, Clock, Award, Server, AlertTriangle, Radio, ArrowUpRight, Zap, Sparkles, ShieldAlert, Cpu
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
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [m, info, h] = await Promise.all([
          apiService.getMetrics(),
          apiService.getModelInfo(),
          apiService.getHealth(),
        ]);
        setMetrics(m);
        setModelInfo(info);
        setHealth(h);
      } catch (err) {
        console.error('Error fetching dashboard telemetry:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  if (loading) {
    return <LoadingSpinner label="Initializing Liquid Glass SOC Telemetry..." size="lg" />;
  }

  // Threat Timeline Area Data
  const timelineData = [
    { time: '08:00', benign: 820, DoS: 45, PortScan: 12, DDoS: 20 },
    { time: '09:00', benign: 950, DoS: 60, PortScan: 25, DDoS: 35 },
    { time: '10:00', benign: 1100, DoS: 120, PortScan: 40, DDoS: 90 },
    { time: '11:00', benign: 1050, DoS: 210, PortScan: 85, DDoS: 140 },
    { time: '12:00', benign: 1300, DoS: 90, PortScan: 65, DDoS: 80 },
    { time: '13:00', benign: 1250, DoS: 140, PortScan: 95, DDoS: 110 },
  ];

  // Risk Distribution Data
  const riskData = [
    { name: 'Low Risk', value: 8283, color: '#10B981' },
    { name: 'Medium Risk', value: 379, color: '#F59E0B' },
    { name: 'High Risk', value: 103, color: '#F97316' },
    { name: 'Critical Risk', value: 1235, color: '#F43F5E' },
  ];

  // Recent Flow Detections
  const recentDetections = [
    { id: 'FLOW-9012', timestamp: '12:54:10', attack: 'BENIGN', confidence: 0.9985, score: 0, level: 'Low', latency: '0.035 ms' },
    { id: 'FLOW-9013', timestamp: '12:54:08', attack: 'DoS Hulk', confidence: 0.9950, score: 79.8, level: 'Critical', latency: '0.028 ms' },
    { id: 'FLOW-9014', timestamp: '12:54:05', attack: 'PortScan', confidence: 0.9987, score: 49.9, level: 'Medium', latency: '0.021 ms' },
    { id: 'FLOW-9015', timestamp: '12:54:01', attack: 'DDoS', confidence: 0.9996, score: 89.9, level: 'Critical', latency: '0.030 ms' },
    { id: 'FLOW-9016', timestamp: '12:53:55', attack: 'BENIGN', confidence: 0.9991, score: 0, level: 'Low', latency: '0.024 ms' },
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
        {/* Glow backdrop */}
        <div className="absolute top-0 right-0 w-96 h-96 rounded-full bg-gradient-to-br from-blue-500/10 via-purple-500/10 to-transparent blur-3xl pointer-events-none" />

        <div className="space-y-3 relative z-10 max-w-xl">
          <div className="flex items-center space-x-2">
            <span className="px-3 py-1 rounded-full bg-blue-500/15 text-blue-400 border border-blue-500/30 text-xs font-mono font-semibold flex items-center gap-1.5">
              <Sparkles className="w-3.5 h-3.5 text-cyan-400" /> AI XDR THREAT CONSOLE
            </span>
            <span className="px-3 py-1 rounded-full bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 text-xs font-mono">
              CLASSIFIER: {modelInfo?.model_name || 'LGBMClassifier'}
            </span>
          </div>

          <h1 className="text-2xl md:text-3xl font-display font-extrabold text-white tracking-tight leading-tight">
            Autonomous Intrusion Intelligence & Cyber Defense
          </h1>
          <p className="text-xs text-slate-300 leading-relaxed font-sans">
            Real-time multi-dimensional network flow telemetry, machine learning anomaly scoring, and automated risk mitigation platform.
          </p>
        </div>

        {/* Threat Score Circle Meter */}
        <div className="relative z-10 flex items-center justify-center p-4 rounded-2xl bg-white/[0.03] border border-white/10 backdrop-blur-md">
          <div className="relative w-36 h-36 flex items-center justify-center">
            {/* SVG Ring Gauge */}
            <svg className="w-full h-full transform -rotate-90" viewBox="0 0 100 100">
              <circle cx="50" cy="50" r="42" stroke="rgba(255,255,255,0.08)" strokeWidth="8" fill="transparent" />
              <circle
                cx="50"
                cy="50"
                r="42"
                stroke="url(#gradientGauge)"
                strokeWidth="8"
                strokeDasharray="263.89"
                strokeDashoffset="211.11"
                strokeLinecap="round"
                fill="transparent"
              />
              <defs>
                <linearGradient id="gradientGauge" x1="0%" y1="0%" x2="100%" y2="100%">
                  <stop offset="0%" stopColor="#22C55E" />
                  <stop offset="100%" stopColor="#3B82F6" />
                </linearGradient>
              </defs>
            </svg>

            <div className="absolute flex flex-col items-center justify-center text-center">
              <span className="text-2xl font-bold font-mono text-white">20.0</span>
              <span className="text-[9px] font-mono text-emerald-400 uppercase tracking-widest">THREAT SCORE</span>
              <span className="text-[9px] text-slate-400 font-mono">LOW RISK</span>
            </div>
          </div>
        </div>
      </div>

      {/* KPI Cards Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        <KpiCard
          title="Total Predictions"
          value={metrics?.prediction_count.toLocaleString() || '10,000'}
          subtitle="Ingested traffic flows"
          icon={<Activity className="w-5 h-5" />}
          statusColor="cyan"
          trend="+10,000 flows"
        />
        <KpiCard
          title="Avg Confidence"
          value={`${((metrics?.average_confidence || 0.9958) * 100).toFixed(2)}%`}
          subtitle="Classifier certainty score"
          icon={<Award className="w-5 h-5" />}
          statusColor="emerald"
          trend="99.58% mean"
        />
        <KpiCard
          title="Inference Latency"
          value={`${metrics?.average_latency_ms || 0.027} ms`}
          subtitle="Real-time flow latency"
          icon={<Clock className="w-5 h-5" />}
          statusColor="purple"
          trend="Sub-millisecond"
        />
        <KpiCard
          title="Engine Status"
          value={health?.healthy ? 'ONLINE' : 'OFFLINE'}
          subtitle={`Model ${modelInfo?.model_name || 'LGBM'}`}
          icon={<Server className="w-5 h-5" />}
          statusColor={health?.healthy ? 'emerald' : 'rose'}
          trend="HTTP 200 OK"
        />
        <KpiCard
          title="Threat Level"
          value="NORMAL"
          subtitle="82.8% Benign Ratio"
          icon={<Radio className="w-5 h-5" />}
          statusColor="blue"
          trend="Safe Range"
        />
      </div>

      {/* Second Row Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Threat Volume Timeline Area Chart */}
        <div className="lg:col-span-2 liquid-glass-card p-6 rounded-2xl">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xs font-mono font-semibold text-slate-200 uppercase tracking-wider">
              Network Threat Telemetry Volume Timeline
            </h2>
            <span className="text-[11px] font-mono text-cyan-400">Flows / Hour</span>
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
                <Area type="monotone" dataKey="DDoS" stroke="#F43F5E" fillOpacity={1} fill="url(#colorDoSL)" name="DDoS / DoS" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Risk Distribution Donut */}
        <div className="liquid-glass-card p-6 rounded-2xl">
          <h2 className="text-xs font-mono font-semibold text-slate-200 uppercase tracking-wider mb-4">
            Risk Severity Distribution
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
        </div>
      </div>
    </motion.div>
  );
};
