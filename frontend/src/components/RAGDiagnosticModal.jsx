import React from 'react';
import { X, Bot, ShieldAlert, CheckCircle2, FileText, Cloud, Cpu, ArrowRight } from 'lucide-react';

export default function RAGDiagnosticModal({ report, onClose, onQuarantine }) {
  if (!report) return null;

  const isLoopB = report.remediation_track === 'LOOP_B_NODE_QUARANTINE';

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md">
      <div className="glass-panel w-full max-w-3xl rounded-2xl border border-cyan-500/30 overflow-hidden shadow-2xl animate-in fade-in zoom-in duration-200">
        
        {/* Modal Header */}
        <div className="px-6 py-4 bg-slate-900 border-b border-slate-800 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-cyan-950 rounded-xl text-cyan-400 border border-cyan-700/50">
              <Bot className="w-6 h-6 animate-pulse" />
            </div>
            <div>
              <h3 className="text-base font-bold text-white font-mono-code flex items-center space-x-2">
                <span>LANGCHAIN RAG DIAGNOSTIC AGENT</span>
                <span className="px-2 py-0.5 text-[10px] bg-cyan-950 text-cyan-300 border border-cyan-800 rounded">CONFIDENCE {(report.confidence_score * 100).toFixed(0)}%</span>
              </h3>
              <p className="text-xs text-slate-400 font-mono-code">REPORT ID: {report.report_id} | NODE: {report.node_id}</p>
            </div>
          </div>
          <button onClick={onClose} className="p-1.5 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-6 max-h-[75vh] overflow-y-auto space-y-6">
          
          {/* Executive Summary Box */}
          <div className={`p-4 rounded-xl border ${isLoopB ? 'bg-red-950/40 border-red-500/40' : 'bg-blue-950/40 border-blue-500/40'}`}>
            <div className="flex items-center space-x-2 text-xs font-bold font-mono-code uppercase mb-1 text-slate-300">
              <ShieldAlert className="w-4 h-4 text-cyan-400" />
              <span>Fault Diagnosis & Track Selection</span>
            </div>
            <div className="text-sm font-semibold text-white mb-2">{report.fault_diagnosis}</div>
            <div className="text-xs text-slate-300 leading-relaxed">{report.executive_summary}</div>
          </div>

          {/* ReAct Agent Reasoning Trace */}
          <div>
            <h4 className="text-xs font-bold font-mono-code text-slate-400 uppercase tracking-wider mb-2 flex items-center space-x-1.5">
              <Cpu className="w-4 h-4 text-cyan-400" />
              <span>ReAct Thought & Reasoning Chain</span>
            </h4>
            <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 space-y-2 font-mono-code text-xs">
              {report.react_reasoning_trace?.map((step, idx) => (
                <div key={idx} className="flex items-start space-x-2">
                  <span className="text-cyan-500 font-bold select-none">&gt;</span>
                  <span className={step.startsWith('FINAL') ? 'text-emerald-400 font-bold' : step.startsWith('ACTION') ? 'text-amber-300' : 'text-slate-300'}>
                    {step}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Action Plan */}
          <div>
            <h4 className="text-xs font-bold font-mono-code text-slate-400 uppercase tracking-wider mb-2 flex items-center space-x-1.5">
              <FileText className="w-4 h-4 text-cyan-400" />
              <span>Automated Recovery Protocol Steps</span>
            </h4>
            <div className="bg-slate-900/60 p-4 rounded-xl border border-slate-800 space-y-2 text-xs text-slate-200">
              {report.action_plan?.map((action, i) => (
                <div key={i} className="flex items-start space-x-2">
                  <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                  <span>{action}</span>
                </div>
              ))}
            </div>
          </div>

          {/* AWS S3 Archive Location */}
          {report.s3_archive_url && (
            <div className="p-3 bg-slate-900 border border-slate-800 rounded-xl flex items-center justify-between text-xs font-mono-code text-slate-400">
              <div className="flex items-center space-x-2">
                <Cloud className="w-4 h-4 text-cyan-400" />
                <span>Forensic S3 Archive:</span>
              </div>
              <span className="text-cyan-300 truncate max-w-xs">{report.s3_archive_url}</span>
            </div>
          )}

        </div>

        {/* Modal Footer */}
        <div className="px-6 py-4 bg-slate-900 border-t border-slate-800 flex items-center justify-between">
          <button onClick={onClose} className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg text-xs font-semibold">
            Close Report
          </button>
          <button
            onClick={() => {
              onQuarantine(report.node_id, true);
              onClose();
            }}
            className="px-5 py-2 bg-red-600 hover:bg-red-500 text-white rounded-lg text-xs font-bold flex items-center space-x-2 shadow-lg shadow-red-950"
          >
            <ShieldAlert className="w-4 h-4" />
            <span>Execute Quarantine Protocol</span>
          </button>
        </div>

      </div>
    </div>
  );
}
