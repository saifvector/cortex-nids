import React from 'react';
import { motion } from 'framer-motion';
import { FileText, Download, Code, FileSpreadsheet, CheckCircle2 } from 'lucide-react';

export const Reports: React.FC = () => {
  const reports = [
    {
      title: 'Model Evaluation Report',
      description: '17-metric performance evaluation, classifier comparison, and ROC curves.',
      html: 'http://localhost:8000/reports/evaluation/evaluation_report.html',
      md: 'http://localhost:8000/reports/evaluation/evaluation_report.md',
      csv: 'http://localhost:8000/reports/evaluation/evaluation_metrics.csv',
    },
    {
      title: 'Explainable AI (XAI) Report',
      description: 'SHAP summary plots, beeswarm feature impact, and instance threat rationale.',
      html: 'http://localhost:8000/reports/explainability/explainability_report.html',
      md: 'http://localhost:8000/reports/explainability/explainability_report.md',
      csv: 'http://localhost:8000/reports/explainability/feature_importance.csv',
    },
    {
      title: 'Batch Prediction Results Summary',
      description: 'Processed flow counts, risk level breakdowns, and exported detection logs.',
      html: 'http://localhost:8000/predictions/prediction_report.html',
      md: 'http://localhost:8000/predictions/prediction_report.md',
      csv: 'http://localhost:8000/predictions/prediction_results.csv',
    },
    {
      title: 'FastAPI Backend API Documentation',
      description: 'OpenAPI REST specifications, Pydantic request models, and cURL examples.',
      md: 'http://localhost:8000/reports/api_documentation.md',
    },
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
          <FileText className="w-5 h-5 text-blue-400" />
          Enterprise Automated Reports & Export Center
        </h1>
        <p className="text-xs text-slate-400 mt-1">
          Download PDF, HTML, CSV, and Markdown audit reports generated across all pipeline modules.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {reports.map((item) => (
          <div key={item.title} className="soc-card p-5 border border-[#1E2C42] flex flex-col justify-between space-y-4">
            <div>
              <div className="flex items-center space-x-2">
                <FileText className="w-4 h-4 text-blue-400" />
                <h2 className="text-sm font-bold text-white uppercase">{item.title}</h2>
              </div>
              <p className="text-xs text-slate-400 mt-2">{item.description}</p>
            </div>

            <div className="flex items-center space-x-3 pt-3 border-t border-[#1E2C42]">
              {item.html && (
                <a
                  href={item.html}
                  target="_blank"
                  rel="noreferrer"
                  className="px-3 py-1.5 rounded bg-blue-500/10 text-blue-400 border border-blue-500/30 text-xs font-mono font-semibold hover:bg-blue-500/20 flex items-center gap-1.5"
                >
                  <Code className="w-3.5 h-3.5" /> Open HTML
                </a>
              )}
              {item.csv && (
                <a
                  href={item.csv}
                  download
                  className="px-3 py-1.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 text-xs font-mono font-semibold hover:bg-emerald-500/20 flex items-center gap-1.5"
                >
                  <FileSpreadsheet className="w-3.5 h-3.5" /> CSV Data
                </a>
              )}
            </div>
          </div>
        ))}
      </div>
    </motion.div>
  );
};
