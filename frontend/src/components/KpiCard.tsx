import React, { ReactNode } from 'react';
import { motion } from 'framer-motion';

interface KpiCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: ReactNode;
  trend?: string;
  statusColor?: 'blue' | 'emerald' | 'amber' | 'rose' | 'purple' | 'cyan';
}

export const KpiCard: React.FC<KpiCardProps> = ({
  title,
  value,
  subtitle,
  icon,
  trend,
  statusColor = 'blue',
}) => {
  const colorGradients = {
    blue: 'from-blue-500/20 to-blue-600/5 text-blue-400 border-blue-500/30',
    emerald: 'from-emerald-500/20 to-emerald-600/5 text-emerald-400 border-emerald-500/30',
    amber: 'from-amber-500/20 to-amber-600/5 text-amber-400 border-amber-500/30',
    rose: 'from-rose-500/20 to-rose-600/5 text-rose-400 border-rose-500/30',
    purple: 'from-purple-500/20 to-purple-600/5 text-purple-400 border-purple-500/30',
    cyan: 'from-cyan-500/20 to-cyan-600/5 text-cyan-400 border-cyan-500/30',
  };

  return (
    <motion.div
      whileHover={{ y: -3, scale: 1.01 }}
      transition={{ type: 'spring', stiffness: 350, damping: 25 }}
      className="liquid-glass-card rounded-2xl p-5 relative overflow-hidden group"
    >
      {/* Accent Corner Glow */}
      <div className={`absolute -top-12 -right-12 w-24 h-24 rounded-full bg-gradient-to-br ${colorGradients[statusColor]} blur-2xl group-hover:scale-150 transition-transform duration-500`} />

      <div className="flex items-center justify-between relative z-10">
        <div>
          <p className="text-[10px] font-mono font-semibold uppercase tracking-widest text-slate-400">{title}</p>
          <h3 className="text-2xl font-bold font-mono text-white mt-1 tracking-tight group-hover:text-cyan-300 transition-colors">
            {value}
          </h3>
          {subtitle && <p className="text-[11px] text-slate-400 mt-1">{subtitle}</p>}
        </div>
        <div className={`p-3 rounded-xl bg-gradient-to-br ${colorGradients[statusColor]} border backdrop-blur-md shadow-lg`}>
          {icon}
        </div>
      </div>

      {trend && (
        <div className="mt-3 pt-3 border-t border-white/10 flex items-center justify-between text-[11px] relative z-10">
          <span className="text-slate-400">SOC Benchmark</span>
          <span className="font-mono font-semibold text-emerald-400 flex items-center gap-1">
            {trend}
          </span>
        </div>
      )}
    </motion.div>
  );
};
