"""
Unit Tests for LangChain ReAct Diagnostic Agent & RAG Knowledge Base.
"""

from agent.react_agent import SDCReActDiagnosticAgent
from agent.rag_knowledge_base import RAGKnowledgeBase

def test_rag_knowledge_base_query():
    kb = RAGKnowledgeBase()
    results = kb.query_runbook("mantissa bit flip transient checkpoint", top_k=1)
    
    assert len(results) >= 1
    assert "RUNBOOK-SDC-001" in results[0]["id"] or "Mantissa" in results[0]["title"]

def test_react_agent_diagnostic_generation():
    agent = SDCReActDiagnosticAgent()
    payload = {
        "node_id": "gpu-node-005",
        "anomaly_risk_score": 0.96,
        "feature_snapshot": {
            "rolling_error_mean_3w": 0.045,
            "max_error_spike": 0.12,
            "consecutive_error_streak": 4,
            "temperature_trend": 8.2
        }
    }
    
    report = agent.generate_diagnostic_report(payload)
    
    assert report["node_id"] == "gpu-node-005"
    assert report["remediation_track"] == "LOOP_B_NODE_QUARANTINE"
    assert len(report["react_reasoning_trace"]) >= 4
    assert len(report["action_plan"]) > 0

if __name__ == "__main__":
    test_rag_knowledge_base_query()
    test_react_agent_diagnostic_generation()
    print("ALL LANGCHAIN RAG AGENT TESTS PASSED.")
