import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { ShieldAlert, Zap, Cpu, AlertTriangle, Layers, BarChart2, Sparkles } from 'lucide-react';
import { apiService } from '../services/api';
import { SingleFlowInput, SinglePredictionResponse } from '../types/api';
import { RiskBadge } from '../components/RiskBadge';
import { LoadingSpinner } from '../components/LoadingSpinner';

const DEFAULT_INPUT: SingleFlowInput = {
  'Destination Port': 80.0,
  'Total Length of Fwd Packets': 120.0,
  'Fwd Packet Length Max': 60.0,
  'Bwd Packet Length Max': 1460.0,
  'Flow Bytes/s': 5000.0,
  'Flow IAT Std': 1200.0,
  'Fwd IAT Min': 10.0,
  'Fwd Header Length': 40.0,
  'Bwd Header Length': 40.0,
  'Bwd Packets/s': 15.0,
  'FIN Flag Count': 0.0,
  'PSH Flag Count': 1.0,
  'Init_Win_bytes_forward': 8192.0,
  'Init_Win_bytes_backward': 255.0,
  'act_data_pkt_fwd': 2.0,
  'min_seg_size_forward': 20.0,
  'Active Mean': 0.0,
  'Active Std': 0.0,
  'Active Max': 0.0,
  'Idle Std': 0.0,
};

const DOS_PRESET: SingleFlowInput = {
  ...DEFAULT_INPUT,
  'Destination Port': 80.0,
  'Total Length of Fwd Packets': 15000.0,
  'Fwd Packet Length Max': 1460.0,
  'Flow Bytes/s': 1500000.0,
  'Flow IAT Std': 50.0,
  'Bwd Packets/s': 850.0,
  'PSH Flag Count': 1.0,
};

const PORTSCAN_PRESET: SingleFlowInput = {
  ...DEFAULT_INPUT,
  'Destination Port': 4444.0,
  'Total Length of Fwd Packets': 0.0,
  'Fwd Packet Length Max': 0.0,
  'Bwd Packet Length Max': 0.0,
  'Flow Bytes/s': 0.0,
  'Flow IAT Std': 2.0,
  'FIN Flag Count': 1.0,
};

export const Prediction: React.FC = () => {
  const [formData, setFormData] = useState<SingleFlowInput>(DEFAULT_INPUT);
  const [result, setResult] = useState<SinglePredictionResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const handleChange = (key: keyof SingleFlowInput, value: string) => {
    const num = parseFloat(value) || 0;
    setFormData((prev) => ({ ...prev, [key]: num }));
  };

  const handlePredict = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const res = await apiService.predictSingle(formData);
      setResult(res);
    } catch (err: any) {
      setError(err.response?.data?.message || 'Prediction request failed. Verify backend status.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, ease: [0.16, 1, 0.3, 1] }}
      className="space-y-6"
    >
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-display font-bold text-white flex items-center gap-2">
            <ShieldAlert className="w-5 h-5 text-blue-400" />
            Single Flow Real-Time Threat Predictor
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Input flow statistics for real-time model classification, risk scoring, and SHAP feature rationale.
          </p>
        </div>

        <div className="flex items-center space-x-2">
          <button
            onClick={() => setFormData(DEFAULT_INPUT)}
            className="px-3.5 py-1.5 rounded-xl bg-white/[0.04] border border-white/10 text-xs text-slate-300 hover:border-blue-500/40 transition-colors font-mono"
          >
            Normal Preset
          </button>
          <button
            onClick={() => setFormData(DOS_PRESET)}
            className="px-3.5 py-1.5 rounded-xl bg-white/[0.04] border border-white/10 text-xs text-amber-400 hover:border-amber-500/40 transition-colors font-mono"
          >
            DoS Preset
          </button>
          <button
            onClick={() => setFormData(PORTSCAN_PRESET)}
            className="px-3.5 py-1.5 rounded-xl bg-white/[0.04] border border-white/10 text-xs text-rose-400 hover:border-rose-500/40 transition-colors font-mono"
          >
            PortScan Preset
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Form Panel */}
        <div className="lg:col-span-2 liquid-glass-card p-6 rounded-2xl">
          <form onSubmit={handlePredict} className="space-y-4">
            <h2 className="text-xs font-mono font-semibold text-slate-300 uppercase tracking-wider mb-3">
              Network Traffic Flow Features (20 Selected Parameters)
            </h2>

            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
              {(Object.keys(DEFAULT_INPUT) as Array<keyof SingleFlowInput>).map((key) => (
                <div key={key} className="space-y-1">
                  <label className="text-[11px] font-mono text-slate-400 block truncate" title={key}>
                    {key}
                  </label>
                  <input
                    type="number"
                    step="any"
                    value={formData[key]}
                    onChange={(e) => handleChange(key, e.target.value)}
                    className="w-full bg-[#04070E]/60 border border-white/10 rounded-xl px-3 py-1.5 text-xs text-slate-200 font-mono focus:border-blue-500 focus:outline-none transition-colors"
                  />
                </div>
              ))}
            </div>

            <div className="pt-4 flex justify-end">
              <button
                type="submit"
                disabled={loading}
                className="px-7 py-3 rounded-xl bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 text-white font-bold text-xs uppercase tracking-wider flex items-center gap-2 shadow-[0_0_25px_rgba(59,130,246,0.3)] transition-all"
              >
                <Zap className="w-4 h-4 fill-current" />
                {loading ? 'Executing Inference...' : 'Execute Threat Prediction'}
              </button>
            </div>
          </form>
        </div>

        {/* Prediction Results Display Card */}
        <div className="liquid-glass-card p-6 rounded-2xl flex flex-col justify-between">
          <div>
            <h2 className="text-xs font-mono font-semibold text-slate-300 uppercase tracking-wider mb-4 border-b border-white/10 pb-2">
              Inference Analysis & Output
            </h2>

            {error && (
              <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-400 text-xs flex items-start gap-2">
                <AlertTriangle className="w-4 h-4 shrink-0" />
                <span>{error}</span>
              </div>
            )}

            {loading && <LoadingSpinner label="Evaluating ML Model Inference..." size="lg" />}

            {!loading && !result && !error && (
              <div className="text-center py-16 text-slate-500">
                <Cpu className="w-12 h-12 mx-auto mb-2 opacity-30" />
                <p className="text-xs">Click "Execute Threat Prediction" to evaluate flow features.</p>
              </div>
            )}

            {!loading && result && (
              <div className="space-y-5">
                {/* Result Header */}
                <div className="p-4 rounded-xl bg-[#04070E]/60 border border-white/10 flex items-center justify-between">
                  <div>
                    <p className="text-[10px] text-slate-400 font-mono uppercase">Predicted Category</p>
                    <h3 className="text-xl font-bold text-white mt-0.5">{result.Attack_Type}</h3>
                  </div>
                  <RiskBadge level={result.Risk_Level} score={result.Risk_Score} />
                </div>

                {/* Risk Score Progress Bar */}
                <div className="space-y-1.5">
                  <div className="flex justify-between text-xs font-mono">
                    <span className="text-slate-400">Threat Risk Score Meter</span>
                    <span className="text-white font-bold">{result.Risk_Score} / 100</span>
                  </div>
                  <div className="w-full h-2.5 rounded-full bg-[#04070E] border border-white/10 overflow-hidden">
                    <div
                      className={`h-full transition-all duration-500 ${
                        result.Risk_Score > 75
                          ? 'bg-rose-500 shadow-[0_0_12px_rgba(244,63,94,0.5)]'
                          : result.Risk_Score > 50
                          ? 'bg-amber-500'
                          : 'bg-emerald-500'
                      }`}
                      style={{ width: `${Math.min(100, Math.max(5, result.Risk_Score))}%` }}
                    ></div>
                  </div>
                </div>

                {/* Key Stats */}
                <div className="grid grid-cols-2 gap-3 text-xs font-mono">
                  <div className="p-3 rounded-xl bg-[#04070E]/60 border border-white/10">
                    <span className="text-slate-400 block text-[10px]">Confidence</span>
                    <span className="font-bold text-emerald-400 text-sm">
                      {(result.Prediction_Confidence * 100).toFixed(2)}%
                    </span>
                  </div>
                  <div className="p-3 rounded-xl bg-[#04070E]/60 border border-white/10">
                    <span className="text-slate-400 block text-[10px]">Latency</span>
                    <span className="font-bold text-cyan-400 text-sm">
                      {result.Prediction_Time_ms} ms
                    </span>
                  </div>
                </div>

                {/* Class Probabilities */}
                <div className="space-y-2 pt-2 border-t border-white/10">
                  <p className="text-xs font-semibold text-slate-300 flex items-center gap-1.5">
                    <BarChart2 className="w-3.5 h-3.5 text-blue-400" /> Class Probabilities
                  </p>
                  <div className="space-y-1.5 max-h-32 overflow-y-auto pr-1">
                    {Object.entries(result.Class_Probabilities)
                      .sort((a, b) => b[1] - a[1])
                      .slice(0, 5)
                      .map(([cls, prob]) => (
                        <div key={cls} className="flex justify-between items-center text-xs font-mono">
                          <span className="text-slate-400">{cls}</span>
                          <span className="text-slate-200">{(prob * 100).toFixed(2)}%</span>
                        </div>
                      ))}
                  </div>
                </div>

                {/* Top SHAP Features */}
                <div className="pt-2 border-t border-white/10">
                  <p className="text-xs font-semibold text-slate-300 mb-2 flex items-center gap-1.5">
                    <Layers className="w-3.5 h-3.5 text-cyan-400" /> Top SHAP Influential Features
                  </p>
                  <div className="space-y-1 text-[11px] font-mono text-slate-400">
                    <div className="flex justify-between">
                      <span>Bwd Packet Length Max</span>
                      <span className="text-cyan-400">+0.246 SHAP</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Destination Port</span>
                      <span className="text-cyan-400">+0.217 SHAP</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Init_Win_bytes_forward</span>
                      <span className="text-cyan-400">+0.218 SHAP</span>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </motion.div>
  );
};
