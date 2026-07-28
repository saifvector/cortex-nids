import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { Layers, ArrowUpDown, Cpu, Info } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { apiService } from '../services/api';
import { FeatureImportanceResponse } from '../types/api';
import { LoadingSpinner } from '../components/LoadingSpinner';

export const FeatureImportance: React.FC = () => {
  const [data, setData] = useState<FeatureImportanceResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [sortAsc, setSortAsc] = useState<boolean>(false);

  useEffect(() => {
    const fetchFI = async () => {
      try {
        const res = await apiService.getFeatureImportance();
        setData(res);
      } catch (err) {
        console.error('Error fetching feature importances:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchFI();
  }, []);

  if (loading) {
    return <LoadingSpinner label="Fetching Model Feature Importances..." size="lg" />;
  }

  const features = data?.top_features || [];
  const sortedFeatures = [...features].sort((a, b) => sortAsc ? a.importance - b.importance : b.importance - a.importance);
  const chartData = features.slice(0, 10).map((f) => ({
    name: f.feature,
    importance: floatFix(f.importance * 100),
  }));

  function floatFix(val: number) {
    return Math.round(val * 100) / 100;
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="space-y-6"
    >
      <div>
        <h1 className="text-xl font-bold text-white flex items-center gap-2">
          <Layers className="w-5 h-5 text-blue-400" />
          Feature Importance & Explainable AI (XAI)
        </h1>
        <p className="text-xs text-slate-400 mt-1">
          Top features driving model classification decisions for <span className="font-mono text-blue-400">{data?.model_name || 'LGBMClassifier'}</span>.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Horizontal Bar Chart */}
        <div className="soc-card p-5 border border-[#1E2C42]">
          <h2 className="text-xs font-semibold text-slate-300 uppercase tracking-wider mb-4">
            Top 10 Feature Importance Distribution (%)
          </h2>
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData} layout="vertical" margin={{ top: 5, right: 20, left: 100, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1E2C42" />
                <XAxis type="number" stroke="#64748B" fontSize={11} />
                <YAxis dataKey="name" type="category" stroke="#94A3B8" fontSize={10} width={120} tickLine={false} />
                <Tooltip contentStyle={{ backgroundColor: '#131D2E', borderColor: '#1E2C42', borderRadius: '8px', fontSize: '12px' }} />
                <Bar dataKey="importance" fill="#3B82F6" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Interactive Sorting Table */}
        <div className="soc-card p-5 border border-[#1E2C42]">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
              Feature Importance Ranking Table
            </h2>
            <button
              onClick={() => setSortAsc(!sortAsc)}
              className="px-2.5 py-1 rounded bg-[#0B1220] border border-[#1E2C42] text-xs text-slate-400 hover:text-white flex items-center gap-1.5 font-mono"
            >
              <ArrowUpDown className="w-3.5 h-3.5" /> {sortAsc ? 'Sort Desc' : 'Sort Asc'}
            </button>
          </div>

          <div className="overflow-y-auto max-h-80 pr-1">
            <table className="w-full text-left text-xs font-mono text-slate-300">
              <thead className="bg-[#0B1220] text-slate-400 uppercase text-[10px] tracking-wider sticky top-0 border-b border-[#1E2C42]">
                <tr>
                  <th className="p-2.5">Rank</th>
                  <th className="p-2.5">Feature Name</th>
                  <th className="p-2.5 text-right">Normalized Importance</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#1E2C42]/60">
                {sortedFeatures.map((item) => (
                  <tr key={item.feature} className="hover:bg-[#1A273D]/60 transition-colors">
                    <td className="p-2.5 font-bold text-blue-400">#{item.rank}</td>
                    <td className="p-2.5 text-slate-200">{item.feature}</td>
                    <td className="p-2.5 text-right font-bold text-emerald-400">
                      {(item.importance * 100).toFixed(2)}%
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </motion.div>
  );
};
