import React, { useState } from 'react';
import { motion } from 'framer-motion';
import {
  UploadCloud, FileText, Download, AlertTriangle, CheckCircle,
  Sparkles, Layers, ShieldCheck, HelpCircle, FileCheck
} from 'lucide-react';
import { apiService, getApiBaseUrl } from '../services/api';
import { BatchSummaryResponse } from '../types/api';
import { LoadingSpinner } from '../components/LoadingSpinner';

export const BatchAnalysis: React.FC = () => {
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

  const handleLoadSample = async () => {
    try {
      setLoading(true);
      setError(null);
      let text = '';
      try {
        const res = await fetch('/sample_test_traffic.csv');
        if (res.ok) {
          text = await res.text();
        }
      } catch {
        // Continue to fallback
      }

      if (!text || !text.includes('Destination Port')) {
        // Fallback sample data in standard CICIDS2017 schema
        text = `Destination Port,Flow Duration,Total Fwd Packets,Total Backward Packets,Total Length of Fwd Packets,Total Length of Bwd Packets,Fwd Packet Length Max,Fwd Packet Length Min,Fwd Packet Length Mean,Fwd Packet Length Stddev,Bwd Packet Length Max,Bwd Packet Length Min,Bwd Packet Length Mean,Bwd Packet Length Stddev,Flow Bytes/s,Flow Packets/s,Flow IAT Mean,Flow IAT Stddev,Flow IAT Max,Flow IAT Min\n80,1000,10,8,500,400,100,20,50.0,10.0,80,10,40.0,5.0,900.0,18.0,50.0,5.0,100,1\n443,1500,12,10,600,500,120,25,50.0,12.0,90,15,45.0,6.0,800.0,15.0,60.0,6.0,120,2\n8080,2500,15,12,800,700,150,30,53.3,15.0,100,20,58.3,8.0,600.0,10.8,80.0,8.0,150,3\n22,800,8,6,300,250,80,15,37.5,8.0,60,10,31.2,4.0,687.5,17.5,40.0,4.0,80,1\n53,300,4,4,150,150,50,10,37.5,5.0,50,10,37.5,5.0,1000.0,26.6,20.0,2.0,40,1`;
      }

      const sampleBlob = new Blob([text], { type: 'text/csv' });
      const sampleFile = new File([sampleBlob], 'sample_test_traffic.csv', { type: 'text/csv' });
      setFile(sampleFile);
    } catch (err: any) {
      setError('Failed to load sample dataset: ' + (err.message || ''));
    } finally {
      setLoading(false);
    }
  };

  const handleUpload = async () => {
    if (!file) {
      setError('Please select or load a CSV file to process.');
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const summary = await apiService.predictBatchCsv(file);
      setResult(summary);
    } catch (err: any) {
      setError(err.response?.data?.detail || err.response?.data?.message || 'Batch prediction failed.');
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
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl md:text-2xl font-bold text-white flex items-center gap-2">
            <UploadCloud className="w-6 h-6 text-blue-400" />
            CSV Batch Traffic Analysis Engine
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            High-throughput batch file ingestion, multi-threaded ML inference, and exported threat summaries.
          </p>
        </div>

        {/* Action helper buttons */}
        <div className="flex items-center gap-2">
          <button
            onClick={handleLoadSample}
            disabled={loading}
            className="px-3.5 py-2 rounded-xl bg-gradient-to-r from-blue-600/20 to-purple-600/20 hover:from-blue-600/30 hover:to-purple-600/30 text-cyan-300 border border-cyan-500/30 text-xs font-semibold flex items-center gap-1.5 transition-all shadow-sm"
          >
            <Sparkles className="w-3.5 h-3.5 text-cyan-400" />
            <span>⚡ Try Sample CSV (1-Click)</span>
          </button>

          <a
            href="/sample_test_traffic.csv"
            download="sample_test_traffic.csv"
            className="px-3.5 py-2 rounded-xl bg-white/[0.04] hover:bg-white/[0.08] text-slate-300 border border-white/10 text-xs font-semibold flex items-center gap-1.5 transition-all"
          >
            <Download className="w-3.5 h-3.5 text-slate-400" />
            <span>Template CSV</span>
          </a>
        </div>
      </div>

      {/* Quick 3-Step Instruction Guide */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        <div className="p-3.5 rounded-xl bg-white/[0.02] border border-white/5 flex items-start gap-3">
          <div className="w-7 h-7 rounded-lg bg-blue-500/10 text-blue-400 flex items-center justify-center font-bold text-xs shrink-0">1</div>
          <div>
            <h4 className="text-xs font-bold text-slate-200">Select or Drop CSV</h4>
            <p className="text-[11px] text-slate-400 mt-0.5">Upload network flows formatted with standard CICIDS2017 headers, or click 1-Click Sample above.</p>
          </div>
        </div>

        <div className="p-3.5 rounded-xl bg-white/[0.02] border border-white/5 flex items-start gap-3">
          <div className="w-7 h-7 rounded-lg bg-purple-500/10 text-purple-400 flex items-center justify-center font-bold text-xs shrink-0">2</div>
          <div>
            <h4 className="text-xs font-bold text-slate-200">Start Batch Processing</h4>
            <p className="text-[11px] text-slate-400 mt-0.5">The CORTEX AI engine analyzes thousands of packets per second for attacks (DoS, PortScan, Bots).</p>
          </div>
        </div>

        <div className="p-3.5 rounded-xl bg-white/[0.02] border border-white/5 flex items-start gap-3">
          <div className="w-7 h-7 rounded-lg bg-emerald-500/10 text-emerald-400 flex items-center justify-center font-bold text-xs shrink-0">3</div>
          <div>
            <h4 className="text-xs font-bold text-slate-200">Review KPIs & Export</h4>
            <p className="text-[11px] text-slate-400 mt-0.5">Inspect attack severity breakdown and download full predictions CSV with risk scores.</p>
          </div>
        </div>
      </div>

      {/* Upload Zone */}
      <div className="liquid-glass-card p-8 rounded-2xl text-center">
        <input
          type="file"
          accept=".csv"
          onChange={handleFileChange}
          className="hidden"
          id="csv-batch-input"
        />
        <label
          htmlFor="csv-batch-input"
          className={`cursor-pointer flex flex-col items-center justify-center p-8 border-2 border-dashed rounded-2xl transition-all ${
            file
              ? 'border-emerald-500/50 bg-emerald-500/[0.03]'
              : 'border-white/10 hover:border-blue-500/50 bg-[#0B1220]/50 hover:bg-[#0B1220]/80'
          }`}
        >
          {file ? (
            <FileCheck className="w-12 h-12 text-emerald-400 mb-3 animate-pulse" />
          ) : (
            <FileText className="w-12 h-12 text-blue-400 mb-3 opacity-80" />
          )}

          <span className="text-sm font-semibold text-slate-200">
            {file ? file.name : 'Click to browse or drag & drop network traffic CSV'}
          </span>
          <span className="text-xs text-slate-400 mt-1">
            {file ? `${(file.size / 1024).toFixed(1)} KB • Ready for inference` : 'Supports standard CICIDS2017 feature CSV schemas'}
          </span>
        </label>

        {error && (
          <div className="mt-4 p-3 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-400 text-xs flex items-center justify-center gap-2">
            <AlertTriangle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <div className="mt-6 flex flex-wrap items-center justify-center gap-3">
          <button
            onClick={handleUpload}
            disabled={!file || loading}
            className="px-8 py-3 rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white font-bold text-xs tracking-wider uppercase flex items-center gap-2 disabled:opacity-40 transition-all shadow-lg shadow-blue-600/20 cursor-pointer disabled:cursor-not-allowed"
          >
            <UploadCloud className="w-4 h-4" />
            {loading ? 'Executing Batch Pipeline...' : 'Start Batch Processing'}
          </button>

          {!file && (
            <button
              onClick={handleLoadSample}
              type="button"
              className="px-5 py-3 rounded-xl bg-white/[0.04] hover:bg-white/[0.08] text-cyan-300 border border-cyan-500/30 text-xs font-semibold flex items-center gap-1.5 transition-all"
            >
              <Sparkles className="w-4 h-4 text-cyan-400" />
              <span>Load Demo Data</span>
            </button>
          )}
        </div>
      </div>

      {loading && <LoadingSpinner label="Processing High-Volume Traffic Ingestion with ML Engine..." size="lg" />}

      {/* Summary View */}
      {result && !loading && (
        <div className="space-y-6">
          {/* Summary KPIs */}
          <div className="grid grid-cols-1 sm:grid-cols-4 gap-4 font-mono">
            <div className="liquid-glass-card p-4 rounded-xl">
              <span className="text-[10px] text-slate-400 uppercase tracking-wider">Total Predicted Flows</span>
              <span className="text-2xl font-bold text-white block mt-1">{result.total_records_predicted.toLocaleString()}</span>
            </div>
            <div className="liquid-glass-card p-4 rounded-xl">
              <span className="text-[10px] text-slate-400 uppercase tracking-wider">Mean Confidence</span>
              <span className="text-2xl font-bold text-emerald-400 block mt-1">{(result.average_confidence * 100).toFixed(2)}%</span>
            </div>
            <div className="liquid-glass-card p-4 rounded-xl">
              <span className="text-[10px] text-slate-400 uppercase tracking-wider">Mean Risk Score</span>
              <span className="text-2xl font-bold text-amber-400 block mt-1">{result.average_risk_score} / 100</span>
            </div>
            <div className="liquid-glass-card p-4 rounded-xl">
              <span className="text-[10px] text-slate-400 uppercase tracking-wider">Mean Latency</span>
              <span className="text-2xl font-bold text-blue-400 block mt-1">{result.average_latency_ms} ms</span>
            </div>
          </div>

          {/* Tables Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="liquid-glass-card p-5 rounded-2xl">
              <h3 className="text-xs font-semibold text-slate-300 uppercase tracking-wider mb-3 flex items-center gap-2">
                <Layers className="w-4 h-4 text-blue-400" />
                Attack Category Breakdown
              </h3>
              <div className="space-y-2 max-h-60 overflow-y-auto pr-1 font-mono text-xs">
                {Object.entries(result.attack_breakdown).map(([atk, cnt]) => (
                  <div key={atk} className="flex justify-between items-center p-2.5 rounded-xl bg-white/[0.03] border border-white/5">
                    <span className="text-slate-300 font-medium">{atk}</span>
                    <span className={`font-bold ${atk === 'BENIGN' ? 'text-emerald-400' : 'text-rose-400'}`}>
                      {cnt.toLocaleString()}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            <div className="liquid-glass-card p-5 rounded-2xl">
              <h3 className="text-xs font-semibold text-slate-300 uppercase tracking-wider mb-3 flex items-center gap-2">
                <ShieldCheck className="w-4 h-4 text-emerald-400" />
                Risk Severity Breakdown
              </h3>
              <div className="space-y-2 font-mono text-xs">
                {Object.entries(result.risk_level_breakdown).map(([lvl, cnt]) => (
                  <div key={lvl} className="flex justify-between items-center p-2.5 rounded-xl bg-white/[0.03] border border-white/5">
                    <span className="text-slate-300 font-medium">{lvl} Severity</span>
                    <span className="font-bold text-amber-400">{cnt.toLocaleString()}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Download Banner */}
          <div className="liquid-glass-card p-5 rounded-2xl flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <h4 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
                <Download className="w-4 h-4 text-emerald-400" />
                Export Full Prediction Dataset
              </h4>
              <p className="text-[11px] text-slate-400 mt-0.5">
                Download full classified CSV results with individual flow risk scores and confidence probabilities.
              </p>
            </div>
            <a
              href={`${getApiBaseUrl()}/predictions/download`}
              target="_blank"
              rel="noreferrer"
              className="px-5 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs flex items-center gap-2 transition-all shadow-lg shadow-emerald-600/20 shrink-0"
            >
              <Download className="w-4 h-4" /> Download Results CSV
            </a>
          </div>
        </div>
      )}
    </motion.div>
  );
};
