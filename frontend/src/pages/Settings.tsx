import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Settings as SettingsIcon, Save, Server, Sliders, CheckCircle2, Shield } from 'lucide-react';

export const Settings: React.FC = () => {
  const [apiUrl, setApiUrl] = useState<string>('http://localhost:8000');
  const [refreshRate, setRefreshRate] = useState<number>(30);
  const [saved, setSaved] = useState<boolean>(false);

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    setSaved(true);
    setTimeout(() => setSaved(false), 3000);
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="space-y-6 max-w-3xl"
    >
      <div>
        <h1 className="text-xl font-bold text-white flex items-center gap-2">
          <SettingsIcon className="w-5 h-5 text-blue-400" />
          SOC Platform Preferences & API Configuration
        </h1>
        <p className="text-xs text-slate-400 mt-1">
          Manage REST API connection endpoints, telemetry refresh frequencies, and alert threshold preferences.
        </p>
      </div>

      <div className="soc-card p-6 border border-[#1E2C42] space-y-6">
        <form onSubmit={handleSave} className="space-y-5">
          <div className="space-y-2">
            <label className="text-xs font-semibold text-slate-300 flex items-center gap-2">
              <Server className="w-4 h-4 text-blue-400" />
              FastAPI REST Backend Endpoint URL
            </label>
            <input
              type="text"
              value={apiUrl}
              onChange={(e) => setApiUrl(e.target.value)}
              className="w-full bg-[#0B1220] border border-[#1E2C42] rounded-lg px-4 py-2 text-xs font-mono text-white focus:border-blue-500 focus:outline-none"
            />
            <p className="text-[11px] text-slate-500">Default endpoint: http://localhost:8000</p>
          </div>

          <div className="space-y-2">
            <label className="text-xs font-semibold text-slate-300 flex items-center gap-2">
              <Sliders className="w-4 h-4 text-blue-400" />
              Telemetry Auto-Refresh Frequency
            </label>
            <select
              value={refreshRate}
              onChange={(e) => setRefreshRate(Number(e.target.value))}
              className="w-full bg-[#0B1220] border border-[#1E2C42] rounded-lg px-4 py-2 text-xs text-slate-200 focus:border-blue-500 focus:outline-none font-mono"
            >
              <option value={10}>10 Seconds (High Frequency)</option>
              <option value={30}>30 Seconds (Default Standard)</option>
              <option value={60}>60 Seconds (Low Bandwidth)</option>
            </select>
          </div>

          <div className="pt-4 flex items-center justify-between border-t border-[#1E2C42]">
            {saved ? (
              <span className="text-xs text-emerald-400 font-semibold flex items-center gap-1.5">
                <CheckCircle2 className="w-4 h-4" /> Platform preferences saved!
              </span>
            ) : (
              <span></span>
            )}
            <button
              type="submit"
              className="px-6 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-bold text-xs flex items-center gap-2 transition-colors uppercase tracking-wider"
            >
              <Save className="w-4 h-4" /> Save Preferences
            </button>
          </div>
        </form>
      </div>
    </motion.div>
  );
};
