import React from 'react';
import { AlertTriangle, ArrowUpRight, ShieldAlert, Cpu } from 'lucide-react';

export default function AnomalyFeed({ anomalies, onDiagnose }) {
  return (
    <div className="glass-panel p-6 rounded-2xl border border-slate-800 mb-6">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-lg font-bold text-white flex items-center space-x-2 font-mono-code">
            <AlertTriangle className="w-5 h-5 text-red-400 animate-bounce" />
            <span>LIVE ISOLATION FOREST SDC ANOMALY DETECTIONS</span>
          </h2>
          <p className="text-xs text-slate-400">Scikit-Learn ML cross-window temporal anomaly alerts</p>
        </div>
        <span className="px-2.5 py-1 bg-red-950/60 border border-red-800 text-red-400 rounded-lg text-xs font-bold font-mono-code">
          {anomalies.length} ALERTS
        </span>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs">
          <thead className="bg-slate-900/80 text-slate-400 uppercase font-mono-code border-b border-slate-800">
            <tr>
              <th className="p-3">Timestamp</th>
              <th className="p-3">Node ID</th>
              <th className="p-3">ML Risk Score</th>
              <th className="p-3">Cross-Window Streak</th>
              <th className="p-3">Max Error Spike</th>
              <th className="p-3">Remediation Track</th>
              <th className="p-3 text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60 text-slate-200">
            {anomalies.length === 0 ? (
              <tr>
                <td colSpan={7} className="p-6 text-center text-slate-500 font-mono-code">
                  No active SDC anomalies detected in baseline. Operating nominal.
                </td>
              </tr>
            ) : (
              anomalies.map((anom) => {
                const feat = anom.feature_snapshot || {};
                const isLoopB = anom.remediation_track === 'LOOP_B_NODE_QUARANTINE';

                return (
                  <tr key={anom.id || Math.random()} className="hover:bg-slate-900/40 transition">
                    <td className="p-3 font-mono-code text-slate-400">
                      {new Date((anom.timestamp || Date.now() / 1000) * 1000).toLocaleTimeString()}
                    </td>
                    <td className="p-3 font-bold font-mono-code text-cyan-400">{anom.node_id}</td>
                    <td className="p-3">
                      <span className="px-2 py-0.5 rounded font-mono-code font-bold bg-red-950 text-red-400 border border-red-800">
                        {(anom.anomaly_risk_score * 100).toFixed(1)}%
                      </span>
                    </td>
                    <td className="p-3 font-mono-code">{feat.consecutive_error_streak || 1} windows</td>
                    <td className="p-3 font-mono-code text-amber-400">{feat.max_error_spike?.toExponential(3) || '1e-4'}</td>
                    <td className="p-3">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                        isLoopB ? 'bg-red-950 text-red-300 border border-red-800' : 'bg-blue-950 text-blue-300 border border-blue-800'
                      }`}>
                        {isLoopB ? 'LOOP B (QUARANTINE)' : 'LOOP A (SALVAGE)'}
                      </span>
                    </td>
                    <td className="p-3 text-right">
                      <button
                        onClick={() => onDiagnose(anom.node_id)}
                        className="px-2.5 py-1 bg-cyan-950 hover:bg-cyan-900 text-cyan-300 border border-cyan-700/60 rounded font-semibold flex items-center space-x-1 ml-auto"
                      >
                        <span>Diagnose</span>
                        <ArrowUpRight className="w-3 h-3" />
                      </button>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
