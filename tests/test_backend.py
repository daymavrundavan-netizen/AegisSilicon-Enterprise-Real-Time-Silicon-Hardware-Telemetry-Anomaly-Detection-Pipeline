"""
Integration Tests for FastAPI Backend REST API.
"""

from fastapi.testclient import TestClient
from backend.app import app

client = TestClient(app)

def test_get_fleet_summary():
    response = client.get("/api/fleet/summary")
    assert response.status_code == 200
    data = response.json()
    assert "total_nodes" in data
    assert data["total_nodes"] >= 1

def test_get_fleet_nodes():
    response = client.get("/api/fleet/nodes")
    assert response.status_code == 200
    nodes = response.json()
    assert isinstance(nodes, list)

def test_quarantine_node_endpoint():
    # Toggle quarantine on gpu-node-001
    response = client.post("/api/nodes/gpu-node-001/quarantine", json={"quarantine": True})
    assert response.status_code == 200
    assert response.json()["new_status"] == "QUARANTINED"

    # Restore node
    response_restore = client.post("/api/nodes/gpu-node-001/quarantine", json={"quarantine": False})
    assert response_restore.status_code == 200
    assert response_restore.json()["new_status"] == "HEALTHY"

def test_agent_diagnose_endpoint():
    response = client.post("/api/agent/diagnose", json={"node_id": "gpu-node-003"})
    assert response.status_code == 200
    report = response.json()
    assert report["node_id"] == "gpu-node-003"
    assert "react_reasoning_trace" in report
