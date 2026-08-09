"""
AegisSilicon Enterprise Streamlit Operations & Anomaly Isolation Platform.
Visualizes End-to-End Data Ingestion (100,000 rec/s) -> SDC Fault Injection -> Isolation Forest ML -> Closed-Loop AI Anomaly Isolation.
Works standalone or connected to FastAPI backend APIs.
"""

import os
import sys
import time
import json
import requests
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from simulator.matrix_engine import FleetSimulator
from streaming.spark_pipeline import StreamingWindowProcessor
from ml.feature_engineer import TemporalFeatureEngineer
from ml.anomaly_detector import SDCAnomalyDetector
from agent.react_agent import SDCReActDiagnosticAgent
from aws.s3_manager import AWSS3Manager

# Configure Streamlit Page
st.set_page_config(
    page_title="Aegis Silicon | AI Infrastructure Operations",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Dark Enterprise Glassmorphism CSS with Forced High-Contrast Colors
st.markdown("""
<style>
    /* Global Base Colors */
    .stAppViewContainer { background-color: #030712 !important; color: #f3f4f6 !important; }
    [data-testid="stSidebar"] { background-color: #090d16 !important; border-right: 1px solid rgba(255, 255, 255, 0.1) !important; }
    
    /* Typography */
    h1, h2, h3, h4, h5, h6, p, span, label { color: #f3f4f6 !important; font-family: 'Inter', sans-serif !important; }
    
    /* Metrics Custom Styling */
    [data-testid="stMetric"] {
        background: rgba(15, 23, 42, 0.95) !important;
        border: 1px solid rgba(6, 182, 212, 0.3) !important;
        padding: 16px !important;
        border-radius: 16px !important;
        box-shadow: 0 4px 20px rgba(0,0,0,0.4) !important;
    }
    [data-testid="stMetricValue"] { font-size: 26px !important; font-weight: 800 !important; color: #06b6d4 !important; font-family: monospace !important; }
    [data-testid="stMetricLabel"] { font-size: 12px !important; color: #94a3b8 !important; text-transform: uppercase !important; font-weight: 700 !important; }

    /* Custom Badges */
    .badge-healthy { background-color: #064e3b; color: #34d399; padding: 4px 10px; border-radius: 6px; font-weight: bold; font-family: monospace; font-size: 11px; }
    .badge-degraded { background-color: #7f1d1d; color: #f87171; padding: 4px 10px; border-radius: 6px; font-weight: bold; font-family: monospace; font-size: 11px; }
    .badge-quarantined { background-color: #78350f; color: #fbbf24; padding: 4px 10px; border-radius: 6px; font-weight: bold; font-family: monospace; font-size: 11px; }

    /* Pipeline Stage Boxes */
    .stage-card {
        background: rgba(15, 23, 42, 0.9);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-top: 4px solid #06b6d4;
        padding: 16px;
        border-radius: 12px;
        margin-bottom: 12px;
    }
</style>
""", unsafe_allow_html=True)

# Initialize Session State Engine for Reliable Autonomous Local Execution
if "fleet_sim" not in st.session_state:
    st.session_state.fleet_sim = FleetSimulator(num_nodes=16, num_corrupted_nodes=2, target_records_per_sec=100000)
    st.session_state.window_proc = StreamingWindowProcessor(window_sec=2.0)
    st.session_state.feat_eng = TemporalFeatureEngineer(window_size=5)
    st.session_state.anom_det = SDCAnomalyDetector()
    st.session_state.agent = SDCReActDiagnosticAgent()
    st.session_state.s3_mgr = AWSS3Manager()
    st.session_state.telemetry_history = []
    st.session_state.audit_logs = []
    st.session_state.node_statuses = {f"gpu-node-{i+1:03d}": ("DEGRADED" if i < 2 else "HEALTHY") for i in range(16)}

# Check if external REST API is reachable
API_BASE = "http://localhost:8000"
def check_api_online():
    try:
        r = requests.get(f"{API_BASE}/api/v1/overview", timeout=0.8)
        return r.status_code == 200
    except Exception:
        return False

api_online = check_api_online()

# Run Local Simulation Step if API is offline
def step_local_simulation():
    batch = st.session_state.fleet_sim.generate_fleet_telemetry()
    now = time.time()
    
    for rec in batch:
        st.session_state.window_proc.add_record(rec)
        st.session_state.telemetry_history.append(rec)
        if len(st.session_state.telemetry_history) > 60:
            st.session_state.telemetry_history.pop(0)

    # Archive to S3 every step
    st.session_state.s3_mgr.archive_telemetry_batch(batch)

    # Process ML Anomaly Windows
    windows = st.session_state.window_proc.process_and_flush_windows()
    for w in windows:
        nid = w["node_id"]
        feats = st.session_state.feat_eng.process_node_window(nid, w)
        anom = st.session_state.anom_det.detect_anomaly(feats)
        
        current_st = st.session_state.node_statuses.get(nid, "HEALTHY")
        if anom["is_sdc_risk"] and current_st != "QUARANTINED":
            rep = st.session_state.agent.generate_diagnostic_report({
                "node_id": nid, "anomaly_risk_score": anom["anomaly_risk_score"], "feature_snapshot": feats
            })
            st.session_state.node_statuses[nid] = "QUARANTINED"
            st.session_state.fleet_sim.set_node_quarantine(nid, True)
            s3_url = st.session_state.s3_mgr.upload_diagnostic_report(rep)
            
            st.session_state.audit_logs.append({
                "timestamp": now, "node_id": nid, "risk_score": anom["anomaly_risk_score"],
                "diagnosis": rep["fault_diagnosis"], "s3_url": s3_url
            })
            if len(st.session_state.audit_logs) > 30:
                st.session_state.audit_logs.pop(0)

step_local_simulation()

# Fetch Active Telemetry State
if api_online:
    try:
        overview = requests.get(f"{API_BASE}/api/v1/overview").json()
        nodes_data = requests.get(f"{API_BASE}/api/v1/nodes").json()
        history_data = requests.get(f"{API_BASE}/api/telemetry/history?limit=50").json()
        s3_data = requests.get(f"{API_BASE}/api/v1/storage").json()
    except Exception:
        api_online = False

if not api_online:
    # Use Local State
    nodes_list = st.session_state.fleet_sim.nodes
    nodes_data = []
    degraded_ct = 0
    quarantine_ct = 0
    for nid, status in st.session_state.node_statuses.items():
        if status == "DEGRADED": degraded_ct += 1
        if status == "QUARANTINED": quarantine_ct += 1
        nodes_data.append({
            "node_id": nid, "status": status, "current_temperature": 68.5 if status=="DEGRADED" else 62.0,
            "current_voltage": 1.15, "sdc_fault_count": 1 if status != "HEALTHY" else 0, "total_batches": 48
        })
    health_idx = max(0.0, round(100.0 - (degraded_ct * 25.0 + quarantine_ct * 12.5), 1))
    overview = {
        "cluster_health_score": health_idx, "healthy_nodes": 16 - degraded_ct - quarantine_ct,
        "degraded_nodes": degraded_ct, "quarantined_nodes": quarantine_ct, "total_nodes": 16,
        "cluster_throughput_rec_sec": 100000, "system_status": "CRITICAL_SDC_DRIFT" if degraded_ct > 0 else "NOMINAL"
    }
    history_data = st.session_state.telemetry_history
    s3_data = st.session_state.s3_mgr.get_recent_s3_landings()


# Sidebar Navigation & Auto Refresh
st.sidebar.markdown("## ⚡ AEGIS SILICON")
st.sidebar.caption("Enterprise AI Infrastructure Platform")

auto_refresh = st.sidebar.checkbox("🔄 Auto-Refresh Stream (1.5s)", value=True)
refresh_rate = st.sidebar.slider("Polling Interval (seconds)", 1.0, 5.0, 1.5, 0.5)

selected_view = st.sidebar.radio(
    "Operations Modules",
    ["📊 Executive Overview & Pipeline", "⚡ Interactive SDC Fault Injector", "🤖 AI Operations Assistant", "☁️ S3 Forensic Archives"]
)

st.sidebar.markdown("---")
st.sidebar.markdown(f"**Execution Mode**: `{'FastAPI REST API' if api_online else 'Local Standalone Engine'}`")


# Main Top Title Header
st.title("⚡ Aegis Silicon Operations Center")
st.caption("End-to-End Real-Time Telemetry Ingestion (100,000 rec/s) → ML Anomaly Detection → Autonomous AI Isolation")

# Metric Row
m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("Health Index", f"{overview['cluster_health_score']}%", overview['system_status'])
m2.metric("Ingestion Rate", f"{overview['cluster_throughput_rec_sec']:,} rec/s", "LIVE STREAM")
m3.metric("Compute Nodes", f"{overview['total_nodes']} Nodes", f"{overview['healthy_nodes']} Healthy")
m4.metric("Active SDC Drift", f"{overview['degraded_nodes']} Degraded")
m5.metric("Quarantined Pool", f"{overview['quarantined_nodes']} Isolated", "Closed-Loop AI")

st.markdown("---")


# ================= MODULE 1: EXECUTIVE OVERVIEW & PIPELINE =================
if selected_view == "📊 Executive Overview & Pipeline":
    st.subheader("🔗 End-to-End Anomaly Isolation Pipeline Flow")
    
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown("""
        <div class="stage-card">
            <h4 style="color:#06b6d4;margin:0;">1. Data Ingestion</h4>
            <p style="font-size:12px;color:#cbd5e1;margin-top:6px;">100,000 records/sec matrix GEMM telemetry micro-batches streamed into Kafka & memory.</p>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown("""
        <div class="stage-card" style="border-top-color:#f59e0b;">
            <h4 style="color:#f59e0b;margin:0;">2. IEEE-754 SDC Fault</h4>
            <p style="font-size:12px;color:#cbd5e1;margin-top:6px;">Silicon aging triggers mantissa/exponent bit-flips in FP32 compute registers.</p>
        </div>
        """, unsafe_allow_html=True)
    with c3:
        st.markdown("""
        <div class="stage-card" style="border-top-color:#ef4444;">
            <h4 style="color:#ef4444;margin:0;">3. Isolation Forest ML</h4>
            <p style="font-size:12px;color:#cbd5e1;margin-top:6px;">Tumbling window feature engineering flags rolling error spikes (> 1e-5).</p>
        </div>
        """, unsafe_allow_html=True)
    with c4:
        st.markdown("""
        <div class="stage-card" style="border-top-color:#10b981;">
            <h4 style="color:#10b981;margin:0;">4. Autonomous Isolation</h4>
            <p style="font-size:12px;color:#cbd5e1;margin-top:6px;">ReAct agent automatically fences node and archives raw JSON telemetry to S3.</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("### 📈 Real-Time Ingestion & FP32 Telemetry Graph")
    if history_data:
        df_hist = pd.DataFrame(history_data)
        df_hist['time_str'] = pd.to_datetime(df_hist['timestamp'], unit='s').dt.strftime('%H:%M:%S')
        
        g1, g2 = st.columns([2, 1])
        with g1:
            fig_err = px.line(
                df_hist, x='time_str', y='relative_error', color='node_id',
                title="FP32 Relative Error Stream (Log Scale)", log_y=True, height=320
            )
            fig_err.update_layout(template="plotly_dark", margin=dict(l=20, r=20, t=40, b=20), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(15,23,42,0.6)')
            st.plotly_chart(fig_err, use_container_width=True)
        with g2:
            fig_temp = px.line(
                df_hist, x='time_str', y='temperature_c', color='node_id',
                title="GPU Thermal Trend (°C)", height=320
            )
            fig_temp.update_layout(template="plotly_dark", margin=dict(l=20, r=20, t=40, b=20), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(15,23,42,0.6)')
            st.plotly_chart(fig_temp, use_container_width=True)

    st.markdown("### 🖥️ Edge GPU Compute Fleet Topology Grid")
    if nodes_data:
        grid_cols = st.columns(4)
        for idx, n in enumerate(nodes_data):
            with grid_cols[idx % 4]:
                st_name = n.get("status", "HEALTHY")
                b_class = "badge-healthy"
                if st_name == "DEGRADED": b_class = "badge-degraded"
                if st_name == "QUARANTINED": b_class = "badge-quarantined"
                
                st.markdown(f"""
                <div style="background:rgba(15,23,42,0.9);border:1px solid rgba(255,255,255,0.1);padding:14px;border-radius:12px;margin-bottom:10px;">
                    <div style="display:flex;justify-content:space-between;align-items:center;">
                        <strong style="color:#f3f4f6;font-family:monospace;">{n['node_id']}</strong>
                        <span class="{b_class}">{st_name}</span>
                    </div>
                    <div style="font-size:12px;color:#94a3b8;margin-top:8px;font-family:monospace;">
                        Temp: <b style="color:#f59e0b;">{n.get('current_temperature', 62.0):.1f}°C</b> | Volt: <b style="color:#3b82f6;">{n.get('current_voltage', 1.15):.3f}V</b><br/>
                        Faults: <b style="color:#ef4444;">{n.get('sdc_fault_count', 0)}</b>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                b1, b2 = st.columns(2)
                with b1:
                    is_q = (st_name == "QUARANTINED")
                    if st.button("Restore" if is_q else "Sandbox", key=f"btn_q_{n['node_id']}"):
                        if api_online:
                            requests.post(f"{API_BASE}/api/nodes/{n['node_id']}/quarantine", json={"quarantine": not is_q})
                        else:
                            st.session_state.node_statuses[n['node_id']] = "HEALTHY" if is_q else "QUARANTINED"
                            st.session_state.fleet_sim.set_node_quarantine(n['node_id'], not is_q)
                        st.rerun()
                with b2:
                    if st.button("Diagnose", key=f"btn_diag_{n['node_id']}"):
                        if api_online:
                            rep = requests.post(f"{API_BASE}/api/agent/diagnose", json={"node_id": n['node_id']}).json()
                        else:
                            rep = st.session_state.agent.generate_diagnostic_report({
                                "node_id": n['node_id'], "anomaly_risk_score": 0.94, "feature_snapshot": {}
                            })
                        st.json(rep)


# ================= MODULE 2: INTERACTIVE SDC FAULT INJECTOR =================
elif selected_view == "⚡ Interactive SDC Fault Injector":
    st.subheader("💥 SDC Hardware Fault Injector & IEEE-754 Bit Visualizer")
    st.caption("Inject microscopic hardware bit-flips into matrix calculation registers & trigger closed-loop AI isolation.")

    i1, i2 = st.columns(2)
    with i1:
        st.markdown("#### Fault Injector Console")
        node_opts = [n['node_id'] for n in nodes_data] if nodes_data else ["gpu-node-002"]
        target_n = st.selectbox("Target Compute Node", node_opts)
        
        fb1, fb2, fb3 = st.columns(3)
        with fb1:
            if st.button("💥 Mantissa Flip", type="primary"):
                if api_online:
                    requests.post(f"{API_BASE}/api/nodes/{target_n}/inject-fault", json={"fault_type": "mantissa"})
                else:
                    st.session_state.fleet_sim.nodes[target_n].is_degrading = True
                    st.session_state.node_statuses[target_n] = "DEGRADED"
                st.success(f"Injected Mantissa Bit-Flip into {target_n}!")
                time.sleep(0.4)
                st.rerun()
        with fb2:
            if st.button("🔥 Exponent Burst"):
                if api_online:
                    requests.post(f"{API_BASE}/api/nodes/{target_n}/inject-fault", json={"fault_type": "exponent"})
                else:
                    st.session_state.fleet_sim.nodes[target_n].is_degrading = True
                    st.session_state.node_statuses[target_n] = "DEGRADED"
                st.warning(f"Injected Exponent Burst into {target_n}!")
                time.sleep(0.4)
                st.rerun()
        with fb3:
            if st.button("🟢 Clear Node"):
                if api_online:
                    requests.post(f"{API_BASE}/api/nodes/{target_n}/quarantine", json={"quarantine": False})
                else:
                    st.session_state.node_statuses[target_n] = "HEALTHY"
                    st.session_state.fleet_sim.set_node_quarantine(target_n, False)
                st.success(f"Restored node {target_n}")
                time.sleep(0.4)
                st.rerun()

    with i2:
        st.markdown("#### IEEE-754 32-Bit Binary Bit Representation")
        active_anomalies = [h for h in history_data if h.get('has_fault_injected') or h.get('relative_error', 0) > 1e-5]
        if active_anomalies:
            latest_f = active_anomalies[-1]
            f_det = latest_f.get('fault_details', {})
            st.write(f"**Target Node**: `{latest_f['node_id']}` | **Relative Error**: `{latest_f.get('relative_error', 0):.4e}`")
            if f_det and f_det.get('orig_binary'):
                st.code(
                    f"Clean Bits:     {f_det['orig_binary']} ({f_det.get('original_value')})\n"
                    f"Corrupted Bits: {f_det['corrupt_binary']} ({f_det.get('corrupted_value'):.6f})\n"
                    f"Matrix Cell:    {f_det.get('matrix_cell_index')}", language="text"
                )
            else:
                st.info("Fault injected. Processing IEEE-754 bit-level representation...")
        else:
            st.info("No active SDC bit-flips detected. Inject a fault using the console on the left.")


# ================= MODULE 3: AI OPERATIONS ASSISTANT =================
elif selected_view == "🤖 AI Operations Assistant":
    st.subheader("💬 Aegis AI Operations Copilot")
    st.caption("Ask questions about cluster health, degraded nodes, or ChromaDB hardware runbooks.")

    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": "👋 Hello! I am Aegis AI Operations Copilot. How can I assist you with your AI infrastructure monitoring today?"}
        ]

    for m in st.session_state.messages:
        with st.chat_message(m["role"]):
            st.write(m["content"])

    if user_q := st.chat_input("Ask Aegis AI Assistant..."):
        st.session_state.messages.append({"role": "user", "content": user_q})
        with st.chat_message("user"):
            st.write(user_q)

        if api_online:
            res = requests.post(f"{API_BASE}/api/v1/assistant/chat", json={"query": user_q}).json()
            reply = res.get("response", "No response from AI Assistant.")
        else:
            live_ctx = {
                "total_nodes": 16, "degraded_nodes": [k for k,v in st.session_state.node_statuses.items() if v=="DEGRADED"],
                "quarantined_nodes": [k for k,v in st.session_state.node_statuses.items() if v=="QUARANTINED"],
                "cluster_health_score": overview['cluster_health_score'], "throughput": 100000, "s3_count": len(s3_data)
            }
            reply = st.session_state.agent.generate_chat_response(user_q, live_ctx)["response"]

        st.session_state.messages.append({"role": "assistant", "content": reply})
        with st.chat_message("assistant"):
            st.write(reply)


# ================= MODULE 4: S3 FORENSIC ARCHIVES =================
elif selected_view == "☁️ S3 Forensic Archives":
    st.subheader("☁️ Amazon S3 Raw Telemetry & Forensic Landings")
    st.caption("Partitioned layout `s3://aegissilicon-telemetry-archive/raw_telemetry/year=2026/month=08/...`")

    if s3_data:
        df_s3 = pd.DataFrame(s3_data)
        st.dataframe(df_s3, use_container_width=True)
    else:
        st.info("No S3 partition objects landed yet.")

# Auto Refresh Loop
if auto_refresh:
    time.sleep(refresh_rate)
    st.rerun()
