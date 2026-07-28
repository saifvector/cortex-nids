import React from 'react';
import { motion } from 'framer-motion';
import { BarChart3, TrendingUp, ShieldAlert, PieChart as PieIcon } from 'lucide-react';
import {
  AreaChart, Area, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell,
} from 'recharts';

export const Analytics: React.FC = () => {
  const trendData = [
    { time: '00:00', benign: 920, attack: 45 },
    { time: '04:00', benign: 850, attack: 30 },
    { time: '08:00', benign: 1400, attack: 280 },
    { time: '12:00', benign: 1850, attack: 410 },
    { time: '16:00', benign: 1600, attack: 320 },
    { time: '20:00', benign: 1100, attack: 110 },
  ];

  const attackClassesData = [
    { name: 'DoS Hulk', count: 674, fill: '#F59E0B' },
    { name: 'DDoS', count: 499, fill: '#EF4444' },
    { name: 'PortScan', count: 390, fill: '#8B5CF6' },
    { name: 'DoS GoldenEye', count: 42, fill: '#3B82F6' },
    { name: 'DoS Slowloris', count: 28, fill: '#06B6D4' },
    { name: 'FTP-Patator', count: 23, fill: '#10B981' },
    { name: 'Bot', count: 12, fill: '#EC4899' },
  ];

  const riskPieData = [
    { name: 'Low Risk', value: 8283, color: '#22C55E' },
    { name: 'Medium Risk', value: 379, color: '#F59E0B' },
    { name: 'High Risk', value: 103, color: '#F97316' },
    { name: 'Critical Risk', value: 1235, color: '#EF4444' },
  ];

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="space-y-6"
    >
      <div>
        <h1 className="text-xl font-bold text-white flex items-center gap-2">
          <BarChart3 className="w-5 h-5 text-blue-400" />
          Intrusion Detection Analytics & Threat Intelligence
        </h1>
        <p className="text-xs text-slate-400 mt-1">
          Historical attack trends, hourly traffic volume, and severity distribution breakdown.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Threat Trend Area Chart */}
        <div className="soc-card p-5 border border-[#1E2C42]">
          <h2 className="text-xs font-semibold text-slate-300 uppercase tracking-wider mb-4 flex items-center gap-2">
            <TrendingUp className="w-4 h-4 text-blue-400" /> 24-Hour Traffic & Anomaly Trend
          </h2>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={trendData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="colorBenignA" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#22C55E" stopOpacity={0.4} />
                    <stop offset="95%" stopColor="#22C55E" stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="colorAttackA" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#EF4444" stopOpacity={0.4} />
                    <stop offset="95%" stopColor="#EF4444" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#1E2C42" />
                <XAxis dataKey="time" stroke="#64748B" fontSize={11} tickLine={false} />
                <YAxis stroke="#64748B" fontSize={11} tickLine={false} />
                <Tooltip contentStyle={{ backgroundColor: '#131D2E', borderColor: '#1E2C42', borderRadius: '8px', fontSize: '12px' }} />
                <Area type="monotone" dataKey="benign" stroke="#22C55E" fillOpacity={1} fill="url(#colorBenignA)" name="Normal Traffic" />
                <Area type="monotone" dataKey="attack" stroke="#EF4444" fillOpacity={1} fill="url(#colorAttackA)" name="Attack Detections" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Top Attack Classes Bar Chart */}
        <div className="soc-card p-5 border border-[#1E2C42]">
          <h2 className="text-xs font-semibold text-slate-300 uppercase tracking-wider mb-4 flex items-center gap-2">
            <ShieldAlert className="w-4 h-4 text-amber-400" /> Top Attack Classes Volume
          </h2>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={attackClassesData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1E2C42" />
                <XAxis dataKey="name" stroke="#64748B" fontSize={10} tickLine={false} />
                <YAxis stroke="#64748B" fontSize={11} tickLine={false} />
                <Tooltip contentStyle={{ backgroundColor: '#131D2E', borderColor: '#1E2C42', borderRadius: '8px', fontSize: '12px' }} />
                <Bar dataKey="count" fill="#3B82F6" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </motion.div>
  );
};
