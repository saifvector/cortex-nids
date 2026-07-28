import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { Cpu, Award, Layers, Clock, ShieldCheck, Database, CheckCircle2 } from 'lucide-react';
import { apiService } from '../services/api';
import { ModelInfoResponse } from '../types/api';
import { LoadingSpinner } from '../components/LoadingSpinner';

export const ModelInsights: React.FC = () => {
  const [model, setModel] = useState<ModelInfoResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    const fetchModel = async () => {
      try {
        const res = await apiService.getModelInfo();
        setModel(res);
      } catch (err) {
        console.error('Error fetching model info:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchModel();
  }, []);

  if (loading) {
    return <LoadingSpinner label="Loading Classifier Architecture & Evaluation Metrics..." size="lg" />;
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
          <Cpu className="w-5 h-5 text-blue-400" />
          Production Model Architecture & Performance Insights
        </h1>
        <p className="text-xs text-slate-400 mt-1">
          Detailed metrics, hyperparameter architecture, evaluation rankings, and dataset versioning details.
        </p>
      </div>

      {/* Top Spec Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 font-mono">
        <div className="soc-card p-4 border border-[#1E2C42]">
          <span className="text-[10px] text-slate-400 uppercase block">CLASSIFIER MODEL</span>
          <span className="text-xl font-bold text-white block mt-1">{model?.model_name || 'LGBMClassifier'}</span>
          <span className="text-[11px] text-slate-500 mt-1 block">Gradient Boosting Ensembles</span>
        </div>

        <div className="soc-card p-4 border border-[#1E2C42]">
          <span className="text-[10px] text-slate-400 uppercase block">TEST ACCURACY</span>
          <span className="text-xl font-bold text-emerald-400 block mt-1">
            {((model?.accuracy || 0.9987) * 100).toFixed(2)}%
          </span>
          <span className="text-[11px] text-slate-500 mt-1 block">504,473 Test Records</span>
        </div>

        <div className="soc-card p-4 border border-[#1E2C42]">
          <span className="text-[10px] text-slate-400 uppercase block">INTRUSION RECALL</span>
          <span className="text-xl font-bold text-blue-400 block mt-1">95.37%</span>
          <span className="text-[11px] text-slate-500 mt-1 block">Attack Detection Sensitivity</span>
        </div>

        <div className="soc-card p-4 border border-[#1E2C42]">
          <span className="text-[10px] text-slate-400 uppercase block">FALSE POSITIVE RATE</span>
          <span className="text-xl font-bold text-emerald-400 block mt-1">0.016%</span>
          <span className="text-[11px] text-slate-500 mt-1 block">Near-Zero False Alarms</span>
        </div>
      </div>

      {/* Detailed Spec Table */}
      <div className="soc-card p-5 border border-[#1E2C42] space-y-4">
        <h2 className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
          Enterprise Model Specifications & Evaluation Summary
        </h2>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-mono text-slate-300">
            <tbody className="divide-y divide-[#1E2C42]">
              <tr>
                <td className="p-3 text-slate-400 font-semibold w-1/3">Algorithm Architecture</td>
                <td className="p-3 text-blue-400 font-bold">{model?.model_name || 'LGBMClassifier'} (LightGBM Gradient Boosting)</td>
              </tr>
              <tr>
                <td className="p-3 text-slate-400 font-semibold">Model Version</td>
                <td className="p-3 text-white">{model?.version || '1.0.0'}</td>
              </tr>
              <tr>
                <td className="p-3 text-slate-400 font-semibold">Training Date & Time</td>
                <td className="p-3 text-white">{model?.training_date || '2026-07-25 19:23:02'}</td>
              </tr>
              <tr>
                <td className="p-3 text-slate-400 font-semibold">Training Dataset Source</td>
                <td className="p-3 text-white">CICIDS2017 Intrusion Benchmark Dataset (2,017,889 Training Rows)</td>
              </tr>
              <tr>
                <td className="p-3 text-slate-400 font-semibold">Feature Count</td>
                <td className="p-3 text-amber-400 font-bold">{model?.feature_count || 20} Selected Features</td>
              </tr>
              <tr>
                <td className="p-3 text-slate-400 font-semibold">Classification Macro F1</td>
                <td className="p-3 text-emerald-400 font-bold">0.9005</td>
              </tr>
              <tr>
                <td className="p-3 text-slate-400 font-semibold">ROC-AUC Score (OvR)</td>
                <td className="p-3 text-emerald-400 font-bold">0.9994</td>
              </tr>
              <tr>
                <td className="p-3 text-slate-400 font-semibold">Inference Latency</td>
                <td className="p-3 text-blue-400 font-bold">0.027 ms / flow</td>
              </tr>
              <tr>
                <td className="p-3 text-slate-400 font-semibold">Training Duration</td>
                <td className="p-3 text-white">443.60 Seconds</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </motion.div>
  );
};
