import React from 'react';
import { Activity, Server, AlertTriangle, ShieldCheck, Zap } from 'lucide-react';

export default function MetricsOverview({ summary }) {
  const cards = [
    {
      title: "Cluster Telemetry Throughput",
      value: "128,000 rec/s",
      subtitle: `${summary?.total_records_processed ? (summary.total_records_processed / 1000).toFixed(0) : 100}k total events evaluated`,
      icon: Zap,
      color: "cyan",
      border: "border-cyan-500/20"
    },
    {
      title: "Concurrent Cluster Nodes",
      value: summary?.total_nodes || 16,
      subtitle: `${summary?.healthy_nodes || 0} Healthy | ${summary?.degraded_nodes || 0} Degraded`,
      icon: Server,
      color: "blue",
      border: "border-blue-500/20"
    },
    {
      title: "Active SDC Anomalies",
      value: summary?.degraded_nodes || 0,
      subtitle: "Mantissa/Exponent micro-drift",
      icon: AlertTriangle,
      color: summary?.degraded_nodes > 0 ? "red" : "emerald",
      border: summary?.degraded_nodes > 0 ? "border-red-500/40 glow-red" : "border-emerald-500/20"
    },
    {
      title: "Quarantined Edge Nodes",
      value: summary?.quarantined_nodes || 0,
      subtitle: "Fenced from active fleet",
      icon: ShieldCheck,
      color: "amber",
      border: "border-amber-500/20"
    }
  ];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
      {cards.map((card, i) => {
        const Icon = card.icon;
        return (
          <div key={i} className={`glass-panel p-5 rounded-2xl border ${card.border} transition-all duration-300 hover:translate-y-[-2px]`}>
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">{card.title}</span>
              <div className={`p-2 rounded-lg bg-slate-900 border border-slate-800 text-${card.color}-400`}>
                <Icon className="w-5 h-5" />
              </div>
            </div>
            <div className="text-2xl font-black text-white font-mono-code mb-1">{card.value}</div>
            <div className="text-xs text-slate-400">{card.subtitle}</div>
          </div>
        );
      })}
    </div>
  );
}
