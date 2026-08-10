"""
500 Edge GPU Compute Fleet Topology & AI Diagnosis Modal
"""

import os
import sys
import time
import requests
import pandas as pd
import streamlit as st

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from simulator.matrix_engine import FleetSimulator
from agent.react_agent import SDCReActDiagnosticAgent

st.set_page_config(page_title="Edge Fleet Topology | Aegis Silicon", page_icon="🖥️", layout="wide")

st.markdown("""
<style>
    .stAppViewContainer { background-color: #030712 !important; color: #f3f4f6 !important; }
    [data-testid="stSidebar"] { background-color: #090d16 !important; }
    h1, h2, h3, h4, h5, h6, p, span, label { color: #f3f4f6 !important; font-family: 'Inter', sans-serif !important; }
    .badge-healthy { background-color: #064e3b; color: #34d399; padding: 4px 10px; border-radius: 6px; font-weight: bold; font-family: monospace; font-size: 11px; }
    .badge-degraded { background-color: #7f1d1d; color: #f87171; padding: 4px 10px; border-radius: 6px; font-weight: bold; font-family: monospace; font-size: 11px; }
    .badge-quarantined { background-color: #78350f; color: #fbbf24; padding: 4px 10px; border-radius: 6px; font-weight: bold; font-family: monospace; font-size: 11px; }
    .node-card { background: rgba(15, 23, 42, 0.9); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 12px; padding: 14px; margin-bottom: 10px; }
</style>
""", unsafe_allow_html=True)

st.title("🖥️ Edge GPU Compute Fleet Topology (500 Nodes)")
st.caption("Interactive node explorer across 500 edge compute nodes on AWS EC2")

if "diag_modal" not in st.session_state:
    st.session_state.diag_modal = None

if "fleet_sim" not in st.session_state:
    st.session_state.fleet_sim = FleetSimulator(num_nodes=500, num_corrupted_nodes=15, target_records_per_sec=100000)
    st.session_state.agent = SDCReActDiagnosticAgent()
    st.session_state.node_statuses = {nid: ("DEGRADED" if engine.is_degrading else "HEALTHY") for nid, engine in st.session_state.fleet_sim.nodes.items()}

col1, col2, col3 = st.columns([2, 1, 1])
with col1:
    search_q = st.text_input("🔍 Search Node (e.g., gpu-node-042)", "").strip().lower()
with col2:
    status_f = st.selectbox("Status Filter", ["ALL", "HEALTHY", "DEGRADED", "QUARANTINED"])
with col3:
    page_num = st.number_input("Page (12 nodes/page)", min_value=1, max_value=42, value=1)

API_BASE = os.getenv("API_BASE", "http://backend:8000")
if "API_BASE" in st.session_state:
    API_BASE = st.session_state.API_BASE

live_nodes_data = []
try:
    r = requests.get(f"{API_BASE}/api/v1/nodes", timeout=1.5)
    if r.status_code == 200:
        live_nodes_data = r.json()
        if live_nodes_data:
            st.session_state.node_statuses = {n["node_id"]: n["status"] for n in live_nodes_data}
except Exception:
    pass

nodes_list = []
if live_nodes_data:
    for n in live_nodes_data:
        nodes_list.append({
            "node_id": n["node_id"],
            "status": n["status"],
            "temperature": n.get("current_temperature", 62.0),
            "voltage": n.get("current_voltage", 1.15),
            "faults": n.get("sdc_fault_count", 0)
        })
else:
    for nid, status in st.session_state.node_statuses.items():
        nodes_list.append({
            "node_id": nid, "status": status,
            "temperature": 74.2 if status=="DEGRADED" else 62.0,
            "voltage": 1.15, "faults": 1 if status != "HEALTHY" else 0
        })

filtered = nodes_list
if search_q:
    filtered = [n for n in filtered if search_q in n['node_id'].lower()]
if status_f != "ALL":
    filtered = [n for n in filtered if n['status'] == status_f]

start_i = (page_num - 1) * 12
end_i = start_i + 12
display_nodes = filtered[start_i:end_i]

st.caption(f"Displaying nodes {start_i+1} to {min(end_i, len(filtered))} of {len(filtered)} matching compute nodes:")

if display_nodes:
    cols = st.columns(4)
    for idx, n in enumerate(display_nodes):
        with cols[idx % 4]:
            st_val = n["status"]
            b_class = "badge-healthy"
            if st_val == "DEGRADED": b_class = "badge-degraded"
            if st_val == "QUARANTINED": b_class = "badge-quarantined"

            st.markdown(f"""
            <div class="node-card">
                <div style="display:flex;justify-content:space-between;align-items:center;">
                    <strong style="color:#f3f4f6;font-family:monospace;font-size:14px;">{n['node_id']}</strong>
                    <span class="{b_class}">{st_val}</span>
                </div>
                <div style="font-size:12px;color:#94a3b8;margin-top:8px;font-family:monospace;">
                    Temp: <b style="color:#f59e0b;">{n['temperature']:.1f}°C</b> | Volt: <b style="color:#3b82f6;">{n['voltage']:.3f}V</b><br/>
                    Faults: <b style="color:#ef4444;">{n['faults']}</b>
                </div>
            </div>
            """, unsafe_allow_html=True)

            b1, b2 = st.columns(2)
            with b1:
                is_q = (st_val == "QUARANTINED")
                if st.button("Unsandbox" if is_q else "Sandbox", key=f"btn_s_{n['node_id']}"):
                    st.session_state.node_statuses[n['node_id']] = "HEALTHY" if is_q else "QUARANTINED"
                    st.session_state.fleet_sim.set_node_quarantine(n['node_id'], not is_q)
                    st.success(f"Updated {n['node_id']}")
                    time.sleep(0.3)
                    st.rerun()
            with b2:
                if st.button("Diagnose", key=f"btn_d_{n['node_id']}"):
                    st.session_state.diag_modal = n['node_id']

if st.session_state.get("diag_modal"):
    st.markdown("---")
    st.subheader(f"🤖 Diagnostic Report: `{st.session_state.diag_modal}`")
    rep = st.session_state.agent.generate_diagnostic_report({
        "node_id": st.session_state.diag_modal, "anomaly_risk_score": 0.94, "feature_snapshot": {}
    })
    st.json(rep)
    if st.button("Close Diagnosis Panel"):
        st.session_state.diag_modal = None
        st.rerun()
