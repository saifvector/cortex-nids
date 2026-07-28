import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { UploadCloud, FileText, Download, AlertTriangle, Search, Filter, ArrowUpDown } from 'lucide-react';
import { apiService } from '../services/api';
import { BatchSummaryResponse } from '../types/api';
import { LoadingSpinner } from '../components/LoadingSpinner';

export const BatchAnalysis: React.FC = () => {
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [result, setResult] = useState<BatchSummaryResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState<string>('');

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setError(null);
    }
  };

  const handleUpload = async () => {
    if (!file) {
      setError('Please select a CSV file to process.');
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const summary = await apiService.predictBatchCsv(file);
      setResult(summary);
    } catch (err: any) {
      setError(err.response?.data?.message || 'Batch prediction failed.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="space-y-6"
    >
      {/* Title */}
      <div>
        <h1 className="text-xl font-bold text-white flex items-center gap-2">
          <UploadCloud className="w-5 h-5 text-blue-400" />
          CSV Batch Traffic Analysis Engine
        </h1>
        <p className="text-xs text-slate-400 mt-1">
          High-throughput batch file ingestion, multi-threaded inference, and exported threat summaries.
        </p>
      </div>

      {/* Upload Zone */}
      <div className="soc-card p-8 border border-[#1E2C42] text-center">
        <input
          type="file"
          accept=".csv"
          onChange={handleFileChange}
          className="hidden"
          id="csv-batch-input"
        />
        <label
          htmlFor="csv-batch-input"
          className="cursor-pointer flex flex-col items-center justify-center p-8 border-2 border-dashed border-[#1E2C42] hover:border-blue-500/50 rounded-xl transition-all bg-[#0B1220]/50"
        >
          <FileText className="w-10 h-10 text-blue-400 mb-3 opacity-80" />
          <span className="text-sm font-semibold text-slate-200">
            {file ? file.name : 'Click to browse or drag & drop network traffic CSV'}
          </span>
          <span className="text-xs text-slate-400 mt-1">
            {file ? `${(file.size / 1024 / 1024).toFixed(2)} MB` : 'Supports standard CICIDS2017 feature CSV schemas'}
          </span>
        </label>

        {error && (
          <div className="mt-4 p-3 rounded-lg bg-rose-500/10 border border-rose-500/30 text-rose-400 text-xs flex items-center justify-center gap-2">
            <AlertTriangle className="w-4 h-4" />
            <span>{error}</span>
          </div>
        )}

        <div className="mt-6 flex justify-center">
          <button
            onClick={handleUpload}
            disabled={!file || loading}
            className="px-8 py-2.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-bold text-xs tracking-wider uppercase flex items-center gap-2 disabled:opacity-50 transition-all shadow-lg"
          >
            <UploadCloud className="w-4 h-4" />
            {loading ? 'Executing Batch Pipeline...' : 'Start Batch Processing'}
          </button>
        </div>
      </div>

      {loading && <LoadingSpinner label="Processing High-Volume Traffic Ingestion..." size="lg" />}

      {/* Summary View */}
      {result && !loading && (
        <div className="space-y-6">
          {/* Summary KPIs */}
          <div className="grid grid-cols-1 sm:grid-cols-4 gap-4 font-mono">
            <div className="soc-card p-4 border border-[#1E2C42]">
              <span className="text-[10px] text-slate-400 uppercase">Total Predicted Flows</span>
              <span className="text-xl font-bold text-white block mt-1">{result.total_records_predicted.toLocaleString()}</span>
            </div>
            <div className="soc-card p-4 border border-[#1E2C42]">
              <span className="text-[10px] text-slate-400 uppercase">Mean Confidence</span>
              <span className="text-xl font-bold text-emerald-400 block mt-1">{(result.average_confidence * 100).toFixed(2)}%</span>
            </div>
            <div className="soc-card p-4 border border-[#1E2C42]">
              <span className="text-[10px] text-slate-400 uppercase">Mean Risk Score</span>
              <span className="text-xl font-bold text-amber-400 block mt-1">{result.average_risk_score} / 100</span>
            </div>
            <div className="soc-card p-4 border border-[#1E2C42]">
              <span className="text-[10px] text-slate-400 uppercase">Mean Latency</span>
              <span className="text-xl font-bold text-blue-400 block mt-1">{result.average_latency_ms} ms</span>
            </div>
          </div>

          {/* Tables Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="soc-card p-5 border border-[#1E2C42]">
              <h3 className="text-xs font-semibold text-slate-300 uppercase tracking-wider mb-3">
                Attack Category Breakdown
              </h3>
              <div className="space-y-2 max-h-60 overflow-y-auto pr-1 font-mono text-xs">
                {Object.entries(result.attack_breakdown).map(([atk, cnt]) => (
                  <div key={atk} className="flex justify-between items-center p-2 rounded bg-[#0B1220]">
                    <span className="text-slate-300">{atk}</span>
                    <span className="font-bold text-blue-400">{cnt.toLocaleString()}</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="soc-card p-5 border border-[#1E2C42]">
              <h3 className="text-xs font-semibold text-slate-300 uppercase tracking-wider mb-3">
                Risk Severity Breakdown
              </h3>
              <div className="space-y-2 font-mono text-xs">
                {Object.entries(result.risk_level_breakdown).map(([lvl, cnt]) => (
                  <div key={lvl} className="flex justify-between items-center p-2 rounded bg-[#0B1220]">
                    <span className="text-slate-300">{lvl} Severity</span>
                    <span className="font-bold text-amber-400">{cnt.toLocaleString()}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Download Banner */}
          <div className="soc-card p-5 border border-[#1E2C42] flex items-center justify-between">
            <div>
              <h4 className="text-xs font-bold text-white uppercase">Export Full Prediction Dataset</h4>
              <p className="text-[11px] text-slate-400 mt-0.5">Download full CSV results with individual flow risk scores and confidence probabilities.</p>
            </div>
            <a
              href="http://localhost:8000/predictions/prediction_results.csv"
              download
              className="px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs flex items-center gap-2 transition-colors"
            >
              <Download className="w-4 h-4" /> Download Results CSV
            </a>
          </div>
        </div>
      )}
    </motion.div>
  );
};
