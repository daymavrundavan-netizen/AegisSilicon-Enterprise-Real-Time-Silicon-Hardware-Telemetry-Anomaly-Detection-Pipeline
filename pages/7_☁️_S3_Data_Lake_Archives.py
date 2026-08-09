"""
Amazon S3 Data Lake Archives Inspector
"""

import os
import sys
import pandas as pd
import streamlit as st

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from aws.s3_manager import AWSS3Manager

st.set_page_config(page_title="S3 Data Lake Archives | Aegis Silicon", page_icon="☁️", layout="wide")

st.markdown("""
<style>
    .stAppViewContainer { background-color: #030712 !important; color: #f3f4f6 !important; }
    [data-testid="stSidebar"] { background-color: #090d16 !important; }
    h1, h2, h3, h4, h5, h6, p, span, label { color: #f3f4f6 !important; font-family: 'Inter', sans-serif !important; }
</style>
""", unsafe_allow_html=True)

st.title("☁️ Amazon S3 Raw Telemetry Micro-Batches & Diagnostic Landings")
st.caption("Partitioned S3 Data Lake Layout: `s3://aegissilicon-telemetry-archive/raw_telemetry/year=2026/month=08/...`")

if "s3_mgr" not in st.session_state:
    st.session_state.s3_mgr = AWSS3Manager()

s3_data = st.session_state.s3_mgr.get_recent_s3_landings()

if s3_data:
    df_s3 = pd.DataFrame(s3_data)
    st.dataframe(df_s3, use_container_width=True)
else:
    st.info("Scanning partition directories `scratch_s3_archive/raw_telemetry/`...")
    st.json({
        "bucket": "aegissilicon-telemetry-archive",
        "partition_format": "s3://aegissilicon-telemetry-archive/raw_telemetry/year={YYYY}/month={MM}/day={DD}/hour={HH}/",
        "status": "LANDING_ACTIVE"
    })
