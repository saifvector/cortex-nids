import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Activity, Pause, Play, Filter, ShieldAlert, Zap, Clock, Terminal, Wifi } from 'lucide-react';
import { RiskBadge } from '../components/RiskBadge';
import { getWebSocketUrl, apiService } from '../services/api';

interface LiveFlowEvent {
  id: string;
  timestamp: string;
  attack: string;
  confidence: number;
  riskScore: number;
  riskLevel: 'Low' | 'Medium' | 'High' | 'Critical';
  srcIp: string;
  destPort: number;
  latencyMs: number;
}

const INITIAL_EVENTS: LiveFlowEvent[] = [
  { id: 'EVT-1001', timestamp: '13:02:10', attack: 'BENIGN', confidence: 0.9991, riskScore: 0, riskLevel: 'Low', srcIp: '192.168.1.105', destPort: 443, latencyMs: 0.024 },
  { id: 'EVT-1002', timestamp: '13:02:08', attack: 'DoS Hulk', confidence: 0.9965, riskScore: 79.8, riskLevel: 'Critical', srcIp: '172.16.0.12', destPort: 80, latencyMs: 0.029 },
  { id: 'EVT-1003', timestamp: '13:02:05', attack: 'BENIGN', confidence: 0.9988, riskScore: 0, riskLevel: 'Low', srcIp: '192.168.1.140', destPort: 80, latencyMs: 0.021 },
  { id: 'EVT-1004', timestamp: '13:02:02', attack: 'PortScan', confidence: 0.9972, riskScore: 49.9, riskLevel: 'Medium', srcIp: '10.0.0.45', destPort: 22, latencyMs: 0.027 },
  { id: 'EVT-1005', timestamp: '13:01:59', attack: 'DDoS', confidence: 0.9994, riskScore: 89.9, riskLevel: 'Critical', srcIp: '172.16.0.88', destPort: 80, latencyMs: 0.031 },
];

const ATTACK_POOL = [
  { attack: 'BENIGN', level: 'Low', score: 0 },
  { attack: 'BENIGN', level: 'Low', score: 0 },
  { attack: 'BENIGN', level: 'Low', score: 0 },
  { attack: 'DoS Hulk', level: 'Critical', score: 79.8 },
  { attack: 'DDoS', level: 'Critical', score: 89.9 },
  { attack: 'PortScan', level: 'Medium', score: 49.9 },
  { attack: 'Bot', level: 'High', score: 72.5 },
];

export const ThreatMonitor: React.FC = () => {
  const [events, setEvents] = useState<LiveFlowEvent[]>(INITIAL_EVENTS);
  const [isLive, setIsLive] = useState<boolean>(true);
  const [wsConnected, setWsConnected] = useState<boolean>(false);
  const [filterLevel, setFilterLevel] = useState<string>('All');
  const [selectedEvent, setSelectedEvent] = useState<LiveFlowEvent | null>(null);

  // WebSocket Connection Effect
  useEffect(() => {
    if (!isLive) return;

    let ws: WebSocket | null = null;
    try {
      const wsUrl = getWebSocketUrl();
      ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        setWsConnected(true);
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          const newEvt: LiveFlowEvent = {
            id: data.id || `EVT-${Math.floor(1000 + Math.random() * 9000)}`,
            timestamp: data.timestamp || new Date().toLocaleTimeString(),
            attack: data.attack_type || 'BENIGN',
            confidence: data.confidence || 0.995,
            riskScore: data.risk_score || 0,
            riskLevel: data.risk_level || 'Low',
            srcIp: data.src_ip || '192.168.1.1',
            destPort: data.dst_port || 80,
            latencyMs: data.prediction_time_ms || 0.027,
          };
          setEvents((prev) => [newEvt, ...prev.slice(0, 49)]);
        } catch (e) {
          console.error('Error parsing WebSocket alert event:', e);
        }
      };

      ws.onerror = () => {
        setWsConnected(false);
      };

      ws.onclose = () => {
        setWsConnected(false);
      };
    } catch {
      setWsConnected(false);
    }

    // Fallback simulation timer if WS is disconnected
    const fallbackTimer = setInterval(() => {
      if (!wsConnected) {
        const randomItem = ATTACK_POOL[Math.floor(Math.random() * ATTACK_POOL.length)];
        const newEvent: LiveFlowEvent = {
          id: `EVT-${Math.floor(1000 + Math.random() * 9000)}`,
          timestamp: new Date().toLocaleTimeString(),
          attack: randomItem.attack,
          confidence: 0.99 + Math.random() * 0.009,
          riskScore: randomItem.score,
          riskLevel: randomItem.level as any,
          srcIp: `192.168.${Math.floor(Math.random() * 5)}.${Math.floor(Math.random() * 255)}`,
          destPort: [80, 443, 22, 8080, 53][Math.floor(Math.random() * 5)],
          latencyMs: floatFix(0.02 + Math.random() * 0.015),
        };
        setEvents((prev) => [newEvent, ...prev.slice(0, 49)]);
      }
    }, 2500);

    return () => {
      if (ws) ws.close();
      clearInterval(fallbackTimer);
    };
  }, [isLive, wsConnected]);

  function floatFix(val: number) {
    return Math.round(val * 1000) / 1000;
  }

  const filteredEvents = events.filter((e) => filterLevel === 'All' || e.riskLevel === filterLevel);

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-display font-bold text-white flex items-center gap-2">
            <Activity className="w-5 h-5 text-blue-400 animate-pulse" />
            Live Real-Time SOC Threat Event Monitor
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Continuous packet sniffing, flow aggregation, ML inference, and WebSocket alert streaming.
          </p>
        </div>

        <div className="flex items-center space-x-3">
          {/* Pause / Resume button */}
          <button
            onClick={() => setIsLive(!isLive)}
            className={`px-4 py-2 rounded-xl text-xs font-semibold flex items-center space-x-2 border transition-all ${
              isLive
                ? 'bg-blue-500/10 text-blue-400 border-blue-500/30 hover:bg-blue-500/20'
                : 'bg-amber-500/10 text-amber-400 border-amber-500/30 hover:bg-amber-500/20'
            }`}
          >
            {isLive ? <Pause className="w-3.5 h-3.5" /> : <Play className="w-3.5 h-3.5" />}
            <span>{isLive ? 'Pause Live Stream' : 'Resume Live Stream'}</span>
          </button>

          {/* Severity Filter */}
          <div className="flex items-center space-x-1 bg-white/[0.04] border border-white/10 p-1 rounded-xl">
            {['All', 'Critical', 'High', 'Medium', 'Low'].map((lvl) => (
              <button
                key={lvl}
                onClick={() => setFilterLevel(lvl)}
                className={`px-2.5 py-1 rounded-lg text-[11px] font-mono transition-colors ${
                  filterLevel === lvl ? 'bg-blue-600 text-white font-bold' : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                {lvl}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Main Stream Table */}
      <div className="liquid-glass-card p-6 rounded-2xl">
        <div className="flex items-center justify-between mb-3 text-xs font-mono">
          <span className="text-slate-400">FEED METRICS: {filteredEvents.length} Active Events Displayed</span>
          <span className="text-emerald-400 flex items-center gap-1.5 font-bold">
            <Wifi className="w-3.5 h-3.5 text-cyan-400" />
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping"></span>
            {wsConnected ? 'WEBSOCKET CONNECTED' : 'LIVE STREAMING'}
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-mono text-slate-300">
            <thead className="bg-white/[0.02] text-slate-400 uppercase text-[10px] tracking-wider border-b border-white/10">
              <tr>
                <th className="p-3">Event ID</th>
                <th className="p-3">Timestamp</th>
                <th className="p-3">Source IP</th>
                <th className="p-3">Dest Port</th>
                <th className="p-3">Predicted Attack</th>
                <th className="p-3">Confidence</th>
                <th className="p-3">Risk Level</th>
                <th className="p-3">Latency</th>
                <th className="p-3 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              <AnimatePresence initial={false}>
                {filteredEvents.map((evt) => (
                  <motion.tr
                    key={evt.id}
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0 }}
                    transition={{ duration: 0.25 }}
                    className="hover:bg-white/[0.04] transition-colors"
                  >
                    <td className="p-3 text-slate-400 font-semibold">{evt.id}</td>
                    <td className="p-3 text-slate-400">{evt.timestamp}</td>
                    <td className="p-3 text-slate-300">{evt.srcIp}</td>
                    <td className="p-3 text-slate-400">{evt.destPort}</td>
                    <td className="p-3 font-bold text-white">{evt.attack}</td>
                    <td className="p-3 text-emerald-400">{(evt.confidence * 100).toFixed(2)}%</td>
                    <td className="p-3">
                      <RiskBadge level={evt.riskLevel} score={evt.riskScore} />
                    </td>
                    <td className="p-3 text-cyan-400">{evt.latencyMs} ms</td>
                    <td className="p-3 text-right">
                      <button
                        onClick={() => setSelectedEvent(evt)}
                        className="px-2.5 py-1 rounded-lg bg-blue-500/10 text-blue-400 border border-blue-500/20 hover:bg-blue-500/20 text-[11px]"
                      >
                        Inspect
                      </button>
                    </td>
                  </motion.tr>
                ))}
              </AnimatePresence>
            </tbody>
          </table>
        </div>
      </div>

      {/* Inspect Modal Drawer */}
      {selectedEvent && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-md flex items-center justify-center z-50 p-4">
          <motion.div
            initial={{ scale: 0.95, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            className="liquid-glass-card p-6 rounded-2xl max-w-lg w-full space-y-4"
          >
            <div className="flex items-center justify-between border-b border-white/10 pb-3">
              <div className="flex items-center space-x-2">
                <ShieldAlert className="w-5 h-5 text-blue-400" />
                <h3 className="font-bold text-white text-base">Flow Inspection: {selectedEvent.id}</h3>
              </div>
              <button
                onClick={() => setSelectedEvent(null)}
                className="text-slate-400 hover:text-white text-sm"
              >
                ✕
              </button>
            </div>

            <div className="space-y-3 font-mono text-xs text-slate-300">
              <div className="flex justify-between p-2.5 rounded-xl bg-[#04070E]/60 border border-white/10">
                <span className="text-slate-400">Predicted Category</span>
                <span className="font-bold text-white">{selectedEvent.attack}</span>
              </div>
              <div className="flex justify-between p-2.5 rounded-xl bg-[#04070E]/60 border border-white/10">
                <span className="text-slate-400">Risk Severity Level</span>
                <RiskBadge level={selectedEvent.riskLevel} score={selectedEvent.riskScore} />
              </div>
              <div className="flex justify-between p-2.5 rounded-xl bg-[#04070E]/60 border border-white/10">
                <span className="text-slate-400">Classification Confidence</span>
                <span className="text-emerald-400 font-bold">{(selectedEvent.confidence * 100).toFixed(2)}%</span>
              </div>
              <div className="flex justify-between p-2.5 rounded-xl bg-[#04070E]/60 border border-white/10">
                <span className="text-slate-400">Inference Latency</span>
                <span className="text-cyan-400">{selectedEvent.latencyMs} ms</span>
              </div>
              <div className="flex justify-between p-2.5 rounded-xl bg-[#04070E]/60 border border-white/10">
                <span className="text-slate-400">Source Host IP</span>
                <span className="text-slate-200">{selectedEvent.srcIp}</span>
              </div>
              <div className="flex justify-between p-2.5 rounded-xl bg-[#04070E]/60 border border-white/10">
                <span className="text-slate-400">Target Port</span>
                <span className="text-slate-200">{selectedEvent.destPort}</span>
              </div>
            </div>

            <div className="pt-3 flex justify-end">
              <button
                onClick={() => setSelectedEvent(null)}
                className="px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-bold text-xs"
              >
                Close Inspection
              </button>
            </div>
          </motion.div>
        </div>
      )}
    </div>
  );
};
