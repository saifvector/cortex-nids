import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
  FileText, Download, Code, FileSpreadsheet, RefreshCw, FileCode, CheckCircle2, Zap, ShieldCheck
} from 'lucide-react';
import { apiService } from '../services/api';

export const Reports: React.FC = () => {
  const [reportMeta, setReportMeta] = useState<any>(null);
  const [compiling, setCompiling] = useState<boolean>(false);

  const handleCompileReport = async () => {
    setCompiling(true);
    try {
      const data = await apiService.generateReport();
      setReportMeta(data);
    } catch (err) {
      console.error('Error compiling fresh report:', err);
    } finally {
      setCompiling(false);
    }
  };

  useEffect(() => {
    handleCompileReport();
  }, []);

  const reportCategories = [
    {
      title: 'Real-Time Threat Detection & Incident Report',
      description: 'Compiled live from predictions/alerts.db containing total flow count, attack breakdowns, and risk audit logs.',
      html: apiService.getReportHtmlUrl(),
      pdf: apiService.getReportPdfUrl(),
      csv: apiService.getReportCsvUrl(),
      md: apiService.getReportMarkdownUrl(),
      badge: 'LIVE DATABASE',
      badgeColor: 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30',
    },
    {
      title: 'Model Evaluation & Benchmark Report',
      description: 'Comprehensive 17-metric performance evaluation, ROC curves, and classifier rankings on the test partition.',
      html: 'http://localhost:8000/reports/evaluation/evaluation_report.html',
      md: 'http://localhost:8000/reports/evaluation/evaluation_report.md',
      csv: 'http://localhost:8000/reports/evaluation/evaluation_metrics.csv',
      badge: 'OFFLINE EVALUATION',
      badgeColor: 'bg-purple-500/15 text-purple-400 border-purple-500/30',
    },
    {
      title: 'Explainable AI (SHAP) Report',
      description: 'Global SHAP feature importance rankings, beeswarm plots, and feature contribution scores.',
      html: 'http://localhost:8000/reports/explainability/explainability_report.html',
      md: 'http://localhost:8000/reports/explainability/explainability_report.md',
      csv: 'http://localhost:8000/reports/explainability/feature_importance.csv',
      badge: 'XAI SHAP',
      badgeColor: 'bg-cyan-500/15 text-cyan-400 border-cyan-500/30',
    },
    {
      title: 'FastAPI Backend API Documentation',
      description: 'OpenAPI REST endpoint specifications, Pydantic data schemas, and cURL integration examples.',
      html: 'http://localhost:8000/docs',
      md: 'http://localhost:8000/reports/api_documentation.md',
      badge: 'API DOCS',
      badgeColor: 'bg-blue-500/15 text-blue-400 border-blue-500/30',
    },
  ];

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="space-y-6"
    >
      {/* Top Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <span className="px-3 py-1 rounded-full bg-blue-500/15 text-blue-400 border border-blue-500/30 text-xs font-mono font-semibold flex items-center gap-1.5">
              <ShieldCheck className="w-3.5 h-3.5 text-cyan-400" /> DYNAMIC REPORTING ENGINE
            </span>
          </div>
          <h1 className="text-xl md:text-2xl font-display font-extrabold text-white tracking-tight mt-1.5 flex items-center gap-2">
            <FileText className="w-5 h-5 text-blue-400" />
            Enterprise Dynamic Report & Export Center
          </h1>
          <p className="text-xs text-slate-400 font-sans">
            Compile and download real-time PDF, HTML, CSV, and Markdown audit reports pulled directly from active database logs and model evaluation checkpoints.
          </p>
        </div>

        <div>
          <button
            onClick={handleCompileReport}
            disabled={compiling}
            className="px-4 py-2.5 rounded-xl bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 text-white font-bold text-xs flex items-center gap-2 shadow-[0_0_20px_rgba(59,130,246,0.3)] transition-all"
          >
            <RefreshCw className={`w-4 h-4 ${compiling ? 'animate-spin' : ''}`} />
            <span>{compiling ? 'Compiling Live Report...' : 'Compile Fresh Dynamic Report'}</span>
          </button>
        </div>
      </div>

      {/* Live Report Metadata Bar */}
      {reportMeta && (
        <div className="liquid-glass-card p-4 rounded-2xl">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-xs font-mono">
            <div className="p-3 rounded-xl bg-[#04070E]/60 border border-white/10">
              <span className="text-slate-400 block text-[10px]">Total Database Flows</span>
              <span className="text-cyan-400 font-bold text-base">{reportMeta.total_flows?.toLocaleString() || 0}</span>
            </div>
            <div className="p-3 rounded-xl bg-[#04070E]/60 border border-white/10">
              <span className="text-slate-400 block text-[10px]">Total Attacks Recorded</span>
              <span className="text-rose-400 font-bold text-base">{reportMeta.total_attacks?.toLocaleString() || 0}</span>
            </div>
            <div className="p-3 rounded-xl bg-[#04070E]/60 border border-white/10">
              <span className="text-slate-400 block text-[10px]">Active Session Predictions</span>
              <span className="text-emerald-400 font-bold text-base">{reportMeta.session_predictions?.toLocaleString() || 0}</span>
            </div>
            <div className="p-3 rounded-xl bg-[#04070E]/60 border border-white/10">
              <span className="text-slate-400 block text-[10px]">Report Compiled At</span>
              <span className="text-slate-200 font-semibold">{reportMeta.timestamp || 'N/A'}</span>
            </div>
          </div>
        </div>
      )}

      {/* Report Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {reportCategories.map((item) => (
          <div key={item.title} className="liquid-glass-card p-6 rounded-2xl flex flex-col justify-between space-y-4">
            <div>
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <FileText className="w-4 h-4 text-blue-400" />
                  <h2 className="text-sm font-bold text-white uppercase font-display">{item.title}</h2>
                </div>
                <span className={`px-2.5 py-0.5 rounded-full border text-[10px] font-mono font-semibold ${item.badgeColor}`}>
                  {item.badge}
                </span>
              </div>
              <p className="text-xs text-slate-400 mt-2 font-sans">{item.description}</p>
            </div>

            <div className="flex flex-wrap items-center gap-2 pt-3 border-t border-white/10">
              {item.pdf && (
                <a
                  href={item.pdf}
                  download
                  className="px-3 py-1.5 rounded-xl bg-purple-500/10 text-purple-400 border border-purple-500/20 text-xs font-mono font-semibold hover:bg-purple-500/20 flex items-center gap-1.5 transition-all"
                >
                  <Download className="w-3.5 h-3.5" /> PDF
                </a>
              )}
              {item.html && (
                <a
                  href={item.html}
                  target="_blank"
                  rel="noreferrer"
                  className="px-3 py-1.5 rounded-xl bg-blue-500/10 text-blue-400 border border-blue-500/20 text-xs font-mono font-semibold hover:bg-blue-500/20 flex items-center gap-1.5 transition-all"
                >
                  <Code className="w-3.5 h-3.5" /> HTML
                </a>
              )}
              {item.csv && (
                <a
                  href={item.csv}
                  download
                  className="px-3 py-1.5 rounded-xl bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 text-xs font-mono font-semibold hover:bg-emerald-500/20 flex items-center gap-1.5 transition-all"
                >
                  <FileSpreadsheet className="w-3.5 h-3.5" /> CSV
                </a>
              )}
              {item.md && (
                <a
                  href={item.md}
                  target="_blank"
                  rel="noreferrer"
                  className="px-3 py-1.5 rounded-xl bg-slate-500/10 text-slate-300 border border-slate-500/20 text-xs font-mono font-semibold hover:bg-slate-500/20 flex items-center gap-1.5 transition-all"
                >
                  <FileCode className="w-3.5 h-3.5" /> Markdown
                </a>
              )}
            </div>
          </div>
        ))}
      </div>
    </motion.div>
  );
};
