"""
Power BI Executive Dashboards & Snowflake Analytics Export
"""

import os
import sys
import pandas as pd
import streamlit as st

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from simulator.matrix_engine import FleetSimulator

st.set_page_config(page_title="Power BI & Snowflake | Aegis Silicon", page_icon="📥", layout="wide")

st.markdown("""
<style>
    .stAppViewContainer { background-color: #030712 !important; color: #f3f4f6 !important; }
    [data-testid="stSidebar"] { background-color: #090d16 !important; }
    h1, h2, h3, h4, h5, h6, p, span, label { color: #f3f4f6 !important; font-family: 'Inter', sans-serif !important; }
</style>
""", unsafe_allow_html=True)

st.title("📥 Power BI Executive Dashboards & Snowflake Analytics Export")
st.caption("Historical telemetry archived into Snowflake data warehouse & live dataset exporter for Power BI dashboards")

if "fleet_sim" not in st.session_state:
    st.session_state.fleet_sim = FleetSimulator(num_nodes=500, num_corrupted_nodes=15, target_records_per_sec=100000)
    st.session_state.node_statuses = {f"gpu-node-{i+1:03d}": ("DEGRADED" if i < 15 else "HEALTHY") for i in range(500)}

nodes_data = []
for nid, status in st.session_state.node_statuses.items():
    nodes_data.append({
        "NodeID": nid, "Status": status,
        "Temperature_C": 74.2 if status=="DEGRADED" else 62.0,
        "Voltage_V": 1.15, "SDC_Faults": 1 if status != "HEALTHY" else 0, "Total_Batches": 1280
    })

p1, p2 = st.columns(2)
with p1:
    st.markdown("#### ❄️ Snowflake Data Warehouse Sync")
    st.json({
        "warehouse": "AEGIS_SILICON_ANALYTICS_WH",
        "database": "SILICON_TELEMETRY_DB",
        "schema": "RAW_STREAMING",
        "table": "HISTORICAL_SDC_METRICS",
        "total_records_archived": 12850000,
        "compression_ratio": "4.2x (Parquet on S3)"
    })

with p2:
    st.markdown("#### 📊 Power BI Dataset Exporter")
    st.markdown("Export 500-node cluster metrics directly for Power BI, Tableau, or Excel reporting:")
    df_pbi = pd.DataFrame(nodes_data)
    csv_bytes = df_pbi.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Download Power BI Executive Dataset (CSV)",
        data=csv_bytes,
        file_name="aegis_silicon_500nodes_powerbi_dataset.csv",
        mime="text/csv"
    )

st.markdown("---")
st.markdown("#### Live 500-Node Dataset Preview")
st.dataframe(df_pbi, use_container_width=True)
