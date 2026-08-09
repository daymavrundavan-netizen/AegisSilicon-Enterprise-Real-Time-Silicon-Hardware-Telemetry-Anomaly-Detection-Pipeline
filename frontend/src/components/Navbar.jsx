import React from 'react';
import { Cpu, ShieldAlert, Cloud, Activity, CheckCircle } from 'lucide-react';

export default function Navbar({ summary, isConnected }) {
  const isCritical = summary?.degraded_nodes > 0;

  return (
    <header className="glass-panel sticky top-0 z-40 px-6 py-4 border-b border-slate-800 flex items-center justify-between">
      <div className="flex items-center space-x-4">
        <div className="p-2.5 bg-cyan-950/80 border border-cyan-500/30 rounded-xl text-cyan-400 glow-cyan">
          <Cpu className="w-6 h-6 animate-pulse" />
        </div>
        <div>
          <div className="flex items-center space-x-2">
            <h1 className="text-xl font-bold tracking-wider text-white font-mono-code">AEGIS<span className="text-cyan-400">SILICON</span></h1>
            <span className="px-2 py-0.5 text-xs font-semibold bg-cyan-950 text-cyan-300 border border-cyan-700/50 rounded-md">ENTERPRISE v1.0</span>
          </div>
          <p className="text-xs text-slate-400">Real-Time Silent Data Corruption Detection & Automated RAG Remediation</p>
        </div>
      </div>

      <div className="flex items-center space-x-6">
        {/* Connection status */}
        <div className="flex items-center space-x-2 text-xs">
          <span className={`w-2.5 h-2.5 rounded-full ${isConnected ? 'bg-emerald-500 shadow-emerald-500/50 shadow-sm animate-ping' : 'bg-red-500'}`}></span>
          <span className="text-slate-300 font-mono-code">{isConnected ? 'LIVE WEBSOCKET STREAM' : 'POLLING REST API'}</span>
        </div>

        {/* System Health Badge */}
        <div className={`px-3 py-1.5 rounded-lg border text-xs font-bold flex items-center space-x-2 ${
          isCritical 
            ? 'bg-red-950/80 border-red-500/50 text-red-400 pulse-red' 
            : 'bg-emerald-950/80 border-emerald-500/50 text-emerald-400'
        }`}>
          {isCritical ? <ShieldAlert className="w-4 h-4" /> : <CheckCircle className="w-4 h-4" />}
          <span>{isCritical ? 'SDC ANOMALY DETECTED' : 'SYSTEM NOMINAL'}</span>
        </div>

        {/* S3 Archiving Indicator */}
        <div className="hidden lg:flex items-center space-x-2 px-3 py-1.5 bg-slate-900 border border-slate-800 rounded-lg text-xs text-slate-300">
          <Cloud className="w-4 h-4 text-cyan-400" />
          <span>AWS S3 ARCHIVE ACTIVE</span>
        </div>
      </div>
    </header>
  );
}
