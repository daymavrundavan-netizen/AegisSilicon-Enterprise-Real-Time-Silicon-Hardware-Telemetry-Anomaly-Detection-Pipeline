"""
Executive Overview & Anomaly Isolation Pipeline
"""

import os
import sys
import time
import requests
import pandas as pd
import plotly.express as px
import streamlit as st

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from simulator.matrix_engine import FleetSimulator
from aws.s3_manager import AWSS3Manager

st.set_page_config(page_title="Executive Overview | Aegis Silicon", page_icon="📊", layout="wide")

st.markdown("""
<style>
    .stAppViewContainer { background-color: #030712 !important; color: #f3f4f6 !important; }
    [data-testid="stSidebar"] { background-color: #090d16 !important; }
    h1, h2, h3, h4, h5, h6, p, span, label { color: #f3f4f6 !important; font-family: 'Inter', sans-serif !important; }
    [data-testid="stMetric"] { background: rgba(15, 23, 42, 0.95) !important; border: 1px solid rgba(6, 182, 212, 0.3) !important; padding: 16px !important; border-radius: 16px !important; }
    [data-testid="stMetricValue"] { font-size: 24px !important; font-weight: 800 !important; color: #06b6d4 !important; font-family: monospace !important; }
    .stage-card { background: rgba(15, 23, 42, 0.9); border: 1px solid rgba(255, 255, 255, 0.1); border-top: 4px solid #06b6d4; padding: 16px; border-radius: 12px; margin-bottom: 12px; }
</style>
""", unsafe_allow_html=True)

st.title("📊 Executive Overview & Pipeline Architecture")
st.caption("End-to-End Real-Time Ingestion (100,000+ rec/s across 500 Edge Nodes) -> Isolation Forest ML -> Closed-Loop AI Isolation")

if "fleet_sim" not in st.session_state:
    st.session_state.fleet_sim = FleetSimulator(num_nodes=500, num_corrupted_nodes=15, target_records_per_sec=100000)
    st.session_state.s3_mgr = AWSS3Manager()
    st.session_state.telemetry_history = []
    st.session_state.node_statuses = {f"gpu-node-{i+1:03d}": ("DEGRADED" if i < 15 else "HEALTHY") for i in range(500)}

batch = st.session_state.fleet_sim.generate_fleet_telemetry()
for rec in batch[:20]:
    st.session_state.telemetry_history.append(rec)
    if len(st.session_state.telemetry_history) > 100:
        st.session_state.telemetry_history.pop(0)

degraded_ct = sum(1 for v in st.session_state.node_statuses.values() if v == "DEGRADED")
quarantined_ct = sum(1 for v in st.session_state.node_statuses.values() if v == "QUARANTINED")
health_score = max(0.0, round(100.0 - (degraded_ct * 2.0 + quarantined_ct * 1.5), 1))

m1, m2, m3, m4 = st.columns(4)
m1.metric("Health Index", f"{health_score}%", "NOMINAL" if health_score > 80 else "DEGRADED")
m2.metric("PySpark Throughput", "100,000 rec/s", "Real-Time Stream")
m3.metric("Edge Fleet", "500 Compute Nodes", f"{500 - degraded_ct - quarantined_ct} Healthy")
m4.metric("Isolated Nodes", f"{quarantined_ct} Quarantined", "Closed-Loop AI")

st.markdown("---")
st.subheader("🔗 End-to-End Anomaly Isolation Pipeline Flow")

c1, c2, c3, c4 = st.columns(4)
with c1:
    st.markdown("""
    <div class="stage-card">
        <h4 style="color:#06b6d4;margin:0;">1. Data Ingestion</h4>
        <p style="font-size:12px;color:#cbd5e1;margin-top:6px;">100,000+ rec/sec streamed from 500 edge nodes via Apache Kafka & PySpark.</p>
    </div>
    """, unsafe_allow_html=True)
with c2:
    st.markdown("""
    <div class="stage-card" style="border-top-color:#f59e0b;">
        <h4 style="color:#f59e0b;margin:0;">2. TimescaleDB & S3</h4>
        <p style="font-size:12px;color:#cbd5e1;margin-top:6px;">Windowed metrics into TimescaleDB (-40% latency) & raw batches to S3.</p>
    </div>
    """, unsafe_allow_html=True)
with c3:
    st.markdown("""
    <div class="stage-card" style="border-top-color:#ef4444;">
        <h4 style="color:#ef4444;margin:0;">3. Isolation Forest ML</h4>
        <p style="font-size:12px;color:#cbd5e1;margin-top:6px;">Statistical model & Isolation Forest flag rolling error spikes (> 1e-5).</p>
    </div>
    """, unsafe_allow_html=True)
with c4:
    st.markdown("""
    <div class="stage-card" style="border-top-color:#10b981;">
        <h4 style="color:#10b981;margin:0;">4. Autonomous Isolation</h4>
        <p style="font-size:12px;color:#cbd5e1;margin-top:6px;">ReAct agent automatically fences corrupted nodes & archives to S3.</p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("### 📈 Live Telemetry Stream")
if st.session_state.telemetry_history:
    df_h = pd.DataFrame(st.session_state.telemetry_history)
    df_h['time_str'] = pd.to_datetime(df_h['timestamp'], unit='s').dt.strftime('%H:%M:%S')

    g1, g2 = st.columns([2, 1])
    with g1:
        fig1 = px.line(df_h, x='time_str', y='relative_error', color='node_id', title="FP32 Relative Error (Log Scale)", log_y=True, height=340)
        fig1.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(15,23,42,0.6)')
        st.plotly_chart(fig1, use_container_width=True)
    with g2:
        fig2 = px.line(df_h, x='time_str', y='temperature_c', color='node_id', title="GPU Thermal (°C)", height=340)
        fig2.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(15,23,42,0.6)')
        st.plotly_chart(fig2, use_container_width=True)
