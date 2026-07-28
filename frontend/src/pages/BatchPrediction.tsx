import React, { useState } from 'react';
import { Upload, FileText, Download, CheckCircle2, AlertTriangle, Layers } from 'lucide-react';
import { apiService } from '../services/api';
import { BatchSummaryResponse } from '../types/api';
import { LoadingSpinner } from '../components/LoadingSpinner';

export const BatchPrediction: React.FC = () => {
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [result, setResult] = useState<BatchSummaryResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setError(null);
    }
  };

  const handleUpload = async () => {
    if (!file) {
      setError('Please select a CSV file to upload.');
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
    <div className="space-y-6">
      {/* Title */}
      <div>
        <h1 className="text-xl font-bold text-slate-100 flex items-center gap-2">
          <Upload className="w-6 h-6 text-cyan-400" />
          CSV Batch Traffic Prediction Engine
        </h1>
        <p className="text-xs text-slate-400 mt-1">
          Upload network packet/flow CSV files for high-throughput batch prediction and risk score breakdown.
        </p>
      </div>

      {/* Upload Box */}
      <div className="glass-panel p-8 rounded-xl border border-slate-800 text-center">
        <input
          type="file"
          accept=".csv"
          onChange={handleFileChange}
          className="hidden"
          id="csv-upload-input"
        />
        <label
          htmlFor="csv-upload-input"
          className="cursor-pointer flex flex-col items-center justify-center p-8 border-2 border-dashed border-slate-700 hover:border-cyan-500/50 rounded-xl transition-all duration-200 bg-slate-950/40"
        >
          <FileText className="w-12 h-12 text-cyan-400 mb-3 opacity-80" />
          <span className="text-sm font-semibold text-slate-200">
            {file ? file.name : 'Click to select or drag & drop CSV file'}
          </span>
          <span className="text-xs text-slate-500 mt-1">
            {file ? `${(file.size / 1024 / 1024).toFixed(2)} MB` : 'Supports standard CICIDS2017 feature CSV format'}
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
            className="px-8 py-3 rounded-lg bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-black font-bold text-sm tracking-wide flex items-center gap-2 shadow-[0_0_20px_rgba(6,182,212,0.3)] disabled:opacity-50 transition-all duration-200"
          >
            <Upload className="w-4 h-4" />
            {loading ? 'Processing Batch Inference...' : 'Upload & Process Batch'}
          </button>
        </div>
      </div>

      {loading && <LoadingSpinner label="Running Batch Inference Pipeline..." size="lg" />}

      {/* Batch Results View */}
      {result && !loading && (
        <div className="space-y-6">
          {/* Summary KPIs */}
          <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
            <div className="glass-panel p-4 rounded-xl border border-slate-800 font-mono">
              <span className="text-xs text-slate-400 block">Total Records</span>
              <span className="text-xl font-bold text-slate-100">{result.total_records_predicted.toLocaleString()}</span>
            </div>
            <div className="glass-panel p-4 rounded-xl border border-slate-800 font-mono">
              <span className="text-xs text-slate-400 block">Avg Confidence</span>
              <span className="text-xl font-bold text-emerald-400">{(result.average_confidence * 100).toFixed(2)}%</span>
            </div>
            <div className="glass-panel p-4 rounded-xl border border-slate-800 font-mono">
              <span className="text-xs text-slate-400 block">Avg Risk Score</span>
              <span className="text-xl font-bold text-amber-400">{result.average_risk_score} / 100</span>
            </div>
            <div className="glass-panel p-4 rounded-xl border border-slate-800 font-mono">
              <span className="text-xs text-slate-400 block">Avg Latency</span>
              <span className="text-xl font-bold text-cyan-400">{result.average_latency_ms} ms</span>
            </div>
          </div>

          {/* Breakdown Tables */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="glass-panel p-6 rounded-xl border border-slate-800">
              <h3 className="text-sm font-semibold text-slate-200 uppercase tracking-wider mb-4">
                Attack Category Breakdown
              </h3>
              <div className="space-y-2 max-h-60 overflow-y-auto pr-1">
                {Object.entries(result.attack_breakdown).map(([atk, cnt]) => (
                  <div key={atk} className="flex justify-between items-center text-xs font-mono p-2 rounded bg-slate-900/60">
                    <span className="text-slate-300">{atk}</span>
                    <span className="font-bold text-cyan-400">{cnt.toLocaleString()}</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="glass-panel p-6 rounded-xl border border-slate-800">
              <h3 className="text-sm font-semibold text-slate-200 uppercase tracking-wider mb-4">
                Risk Level Distribution
              </h3>
              <div className="space-y-2">
                {Object.entries(result.risk_level_breakdown).map(([lvl, cnt]) => (
                  <div key={lvl} className="flex justify-between items-center text-xs font-mono p-2 rounded bg-slate-900/60">
                    <span className="text-slate-300">{lvl} Risk</span>
                    <span className="font-bold text-amber-400">{cnt.toLocaleString()}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Download CSV Action */}
          <div className="glass-panel p-6 rounded-xl border border-slate-800 flex items-center justify-between">
            <div>
              <h4 className="text-sm font-semibold text-slate-100">Download Full Prediction Results</h4>
              <p className="text-xs text-slate-400 mt-1">Export complete predictions CSV with confidence, risk score, and class probabilities.</p>
            </div>
            <a
              href="http://localhost:8000/predictions/prediction_results.csv"
              download
              className="px-5 py-2.5 rounded-lg bg-emerald-500 hover:bg-emerald-400 text-black font-bold text-xs flex items-center gap-2 transition-colors"
            >
              <Download className="w-4 h-4" />
              Download Results CSV
            </a>
          </div>
        </div>
      )}
    </div>
  );
};
