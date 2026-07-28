import React from 'react';

interface RiskBadgeProps {
  level: 'Low' | 'Medium' | 'High' | 'Critical' | string;
  score?: number;
}

export const RiskBadge: React.FC<RiskBadgeProps> = ({ level, score }) => {
  const getStyle = () => {
    switch (level) {
      case 'Low':
        return 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30';
      case 'Medium':
        return 'bg-amber-500/10 text-amber-400 border-amber-500/30';
      case 'High':
        return 'bg-orange-500/10 text-orange-400 border-orange-500/30';
      case 'Critical':
        return 'bg-rose-500/10 text-rose-400 border-rose-500/30 font-bold';
      default:
        return 'bg-slate-800 text-slate-300 border-slate-700';
    }
  };

  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded border text-[11px] font-mono uppercase tracking-wider ${getStyle()}`}>
      <span className="w-1.5 h-1.5 rounded-full bg-current mr-1.5"></span>
      {level} {score !== undefined && `(${score})`}
    </span>
  );
};
