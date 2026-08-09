import React, { useState, useEffect } from 'react';
import Navbar from './components/Navbar';
import MetricsOverview from './components/MetricsOverview';
import NodeTopologyGrid from './components/NodeTopologyGrid';
import TelemetryChart from './components/TelemetryChart';
import AnomalyFeed from './components/AnomalyFeed';
import RAGDiagnosticModal from './components/RAGDiagnosticModal';

const API_BASE = 'http://localhost:8000';
const WS_URL = 'ws://localhost:8000/ws/telemetry';

export default function App() {
  const [summary, setSummary] = useState(null);
  const [nodes, setNodes] = useState([]);
  const [telemetryHistory, setTelemetryHistory] = useState([]);
  const [anomalies, setAnomalies] = useState([]);
  const [selectedReport, setSelectedReport] = useState(null);
  const [isConnected, setIsConnected] = useState(false);

  // Fetch REST API data
  const fetchData = async () => {
    try {
      const [sumRes, nodesRes, telemRes, anomRes] = await Promise.all([
        fetch(`${API_BASE}/api/fleet/summary`),
        fetch(`${API_BASE}/api/fleet/nodes`),
        fetch(`${API_BASE}/api/telemetry/history?limit=40`),
        fetch(`${API_BASE}/api/anomalies?limit=20`)
      ]);

      if (sumRes.ok) setSummary(await sumRes.json());
      if (nodesRes.ok) setNodes(await nodesRes.json());
      if (telemRes.ok) setTelemetryHistory(await telemRes.json());
      if (anomRes.ok) setAnomalies(await anomRes.json());
    } catch (err) {
      console.warn("Backend REST API offline or connecting...", err);
    }
  };

  // Connect WebSocket & Polling
  useEffect(() => {
    fetchData();
    const pollInterval = setInterval(fetchData, 2500);

    let ws;
    try {
      ws = new WebSocket(WS_URL);
      ws.onopen = () => setIsConnected(true);
      ws.onclose = () => setIsConnected(false);
      ws.onmessage = (evt) => {
        try {
          const msg = JSON.parse(evt.data);
          if (msg.type === 'WINDOW_ANOMALY_UPDATE') {
            fetchData();
          }
        } catch (e) {}
      };
    } catch (e) {
      setIsConnected(false);
    }

    return () => {
      clearInterval(pollInterval);
      if (ws) ws.close();
    };
  }, []);

  // Action Handlers
  const handleToggleQuarantine = async (nodeId, quarantine) => {
    try {
      const res = await fetch(`${API_BASE}/api/nodes/${nodeId}/quarantine`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ quarantine })
      });
      if (res.ok) fetchData();
    } catch (err) {
      console.error("Failed quarantine update:", err);
    }
  };

  const handleDiagnose = async (nodeId) => {
    try {
      const res = await fetch(`${API_BASE}/api/agent/diagnose`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ node_id: nodeId })
      });
      if (res.ok) {
        const report = await res.json();
        setSelectedReport(report);
      }
    } catch (err) {
      console.error("Failed to run agent diagnosis:", err);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
      <Navbar summary={summary} isConnected={isConnected} />

      <main className="flex-1 max-w-7xl w-full mx-auto p-6">
        <MetricsOverview summary={summary} />
        
        <NodeTopologyGrid 
          nodes={nodes} 
          onToggleQuarantine={handleToggleQuarantine} 
          onDiagnose={handleDiagnose} 
        />

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2">
            <TelemetryChart history={telemetryHistory} />
          </div>
          <div className="lg:col-span-1">
            <AnomalyFeed anomalies={anomalies} onDiagnose={handleDiagnose} />
          </div>
        </div>
      </main>

      <footer className="glass-panel py-4 px-6 border-t border-slate-800 text-center text-xs text-slate-500 font-mono-code">
        AegisSilicon Enterprise SDC Telemetry Pipeline | PySpark Structured Streaming & Isolation Forest ML & LangChain RAG
      </footer>

      {selectedReport && (
        <RAGDiagnosticModal 
          report={selectedReport} 
          onClose={() => setSelectedReport(null)}
          onQuarantine={handleToggleQuarantine}
        />
      )}
    </div>
  );
}
