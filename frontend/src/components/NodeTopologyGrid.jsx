import React from 'react';
import { Cpu, ShieldOff, ShieldAlert, Bot, Thermometer, Zap } from 'lucide-react';

export default function NodeTopologyGrid({ nodes, onToggleQuarantine, onDiagnose }) {
  return (
    <div className="glass-panel p-6 rounded-2xl border border-slate-800 mb-6">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-lg font-bold text-white flex items-center space-x-2 font-mono-code">
            <Cpu className="w-5 h-5 text-cyan-400" />
            <span>AI COMPUTE CLUSTER TOPOLOGY</span>
          </h2>
          <p className="text-xs text-slate-400">Real-time edge GPU matrix processing node status & physical parameters</p>
        </div>
        <div className="flex items-center space-x-3 text-xs">
          <span className="flex items-center space-x-1.5"><span className="w-2.5 h-2.5 rounded-full bg-emerald-500"></span><span className="text-slate-300">Healthy</span></span>
          <span className="flex items-center space-x-1.5"><span className="w-2.5 h-2.5 rounded-full bg-red-500 animate-ping"></span><span className="text-slate-300">Degraded (SDC)</span></span>
          <span className="flex items-center space-x-1.5"><span className="w-2.5 h-2.5 rounded-full bg-amber-500"></span><span className="text-slate-300">Quarantined</span></span>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4">
        {nodes.map((node) => {
          const isQuarantined = node.status === 'QUARANTINED';
          const isDegraded = node.status === 'DEGRADED';
          
          let cardBg = 'bg-slate-900/60 border-slate-800';
          let badgeBg = 'bg-emerald-950 text-emerald-400 border-emerald-800';
          
          if (isDegraded) {
            cardBg = 'bg-red-950/40 border-red-500/40 glow-red';
            badgeBg = 'bg-red-950 text-red-400 border-red-800 animate-pulse';
          } else if (isQuarantined) {
            cardBg = 'bg-amber-950/30 border-amber-500/30';
            badgeBg = 'bg-amber-950 text-amber-400 border-amber-800';
          }

          return (
            <div key={node.node_id} className={`p-4 rounded-xl border ${cardBg} transition-all duration-200`}>
              <div className="flex items-center justify-between mb-3">
                <span className="text-sm font-bold font-mono-code text-slate-200">{node.node_id}</span>
                <span className={`px-2 py-0.5 text-[10px] font-bold rounded-md border ${badgeBg}`}>
                  {node.status}
                </span>
              </div>

              {/* Physical Parameters */}
              <div className="grid grid-cols-2 gap-2 text-xs mb-4 bg-slate-950/60 p-2.5 rounded-lg border border-slate-800/80">
                <div className="flex items-center space-x-1 text-slate-300">
                  <Thermometer className="w-3.5 h-3.5 text-amber-400" />
                  <span>{node.current_temperature?.toFixed(1)}°C</span>
                </div>
                <div className="flex items-center space-x-1 text-slate-300">
                  <Zap className="w-3.5 h-3.5 text-cyan-400" />
                  <span>{node.current_voltage?.toFixed(3)}V</span>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex items-center space-x-2">
                <button
                  onClick={() => onToggleQuarantine(node.node_id, !isQuarantined)}
                  className={`flex-1 py-1.5 px-2 rounded-lg text-xs font-semibold flex items-center justify-center space-x-1 transition ${
                    isQuarantined 
                      ? 'bg-emerald-600/20 hover:bg-emerald-600/40 text-emerald-300 border border-emerald-500/40' 
                      : 'bg-red-950/60 hover:bg-red-900/80 text-red-300 border border-red-800/60'
                  }`}
                >
                  <ShieldOff className="w-3.5 h-3.5" />
                  <span>{isQuarantined ? 'Restore' : 'Quarantine'}</span>
                </button>

                <button
                  onClick={() => onDiagnose(node.node_id)}
                  className="py-1.5 px-2.5 bg-cyan-950/80 hover:bg-cyan-900 border border-cyan-700/60 text-cyan-300 rounded-lg text-xs font-semibold flex items-center space-x-1"
                  title="Run LangChain RAG AI Agent Diagnosis"
                >
                  <Bot className="w-3.5 h-3.5" />
                  <span>RAG AI</span>
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
