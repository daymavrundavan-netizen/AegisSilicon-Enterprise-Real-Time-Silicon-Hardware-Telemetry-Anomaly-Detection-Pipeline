import React from 'react';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Legend } from 'recharts';
import { Activity } from 'lucide-react';

export default function TelemetryChart({ history }) {
  // Format telemetry history for multi-series chart
  const formattedData = history.slice(-30).map((item, index) => ({
    time: new Date(item.timestamp * 1000).toLocaleTimeString([], { hour12: false, minute: '2-digit', second: '2-digit' }),
    node: item.node_id,
    error: Math.max(1e-8, item.relative_error),
    threshold: 1e-4
  }));

  return (
    <div className="glass-panel p-6 rounded-2xl border border-slate-800 mb-6">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-lg font-bold text-white flex items-center space-x-2 font-mono-code">
            <Activity className="w-5 h-5 text-cyan-400" />
            <span>REAL-TIME IEEE-754 ARITHMETIC DRIFT (FP32 RELATIVE ERROR)</span>
          </h2>
          <p className="text-xs text-slate-400">Micro-batch matrix dot-product relative mathematical error vs baseline</p>
        </div>
        <div className="px-2.5 py-1 bg-slate-900 border border-slate-800 rounded-lg text-xs font-mono-code text-cyan-400">
          SDC THRESHOLD: 1e-4
        </div>
      </div>

      <div className="h-64 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={formattedData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
            <XAxis dataKey="time" stroke="#64748b" tick={{ fontSize: 11 }} />
            <YAxis scale="log" domain={['auto', 'auto']} stroke="#64748b" tick={{ fontSize: 11 }} />
            <Tooltip 
              contentStyle={{ backgroundColor: '#090d16', borderColor: '#334155', borderRadius: '8px', fontSize: '12px' }}
              labelStyle={{ color: '#06b6d4', fontWeight: 'bold' }}
            />
            <Legend wrapperStyle={{ fontSize: '12px' }} />
            <Line type="monotone" dataKey="error" stroke="#06b6d4" strokeWidth={2} dot={false} name="Relative Error" />
            <Line type="monotone" dataKey="threshold" stroke="#ef4444" strokeDasharray="5 5" strokeWidth={1.5} dot={false} name="SDC Threat Limit" />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
