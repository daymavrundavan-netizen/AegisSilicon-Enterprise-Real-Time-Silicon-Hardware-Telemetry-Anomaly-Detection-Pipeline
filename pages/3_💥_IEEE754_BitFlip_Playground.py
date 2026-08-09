"""
IEEE-754 32-Bit Microscopic Register Bit-Flip Simulator
"""

import os
import sys
import time
import streamlit as st

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from simulator.matrix_engine import FleetSimulator
from simulator.fault_injector import IEEE754FaultInjector

st.set_page_config(page_title="IEEE-754 Bit-Flip Playground | Aegis Silicon", page_icon="💥", layout="wide")

st.markdown("""
<style>
    .stAppViewContainer { background-color: #030712 !important; color: #f3f4f6 !important; }
    [data-testid="stSidebar"] { background-color: #090d16 !important; }
    h1, h2, h3, h4, h5, h6, p, span, label { color: #f3f4f6 !important; font-family: 'Inter', sans-serif !important; }
</style>
""", unsafe_allow_html=True)

st.title("💥 IEEE-754 32-Bit Microscopic Register Bit-Flip Simulator")
st.caption("Interactive hardware fault injector: select any float value, flip bits, and observe real-time SDC propagation.")

if "fleet_sim" not in st.session_state:
    st.session_state.fleet_sim = FleetSimulator(num_nodes=500, num_corrupted_nodes=15, target_records_per_sec=100000)
    st.session_state.node_statuses = {f"gpu-node-{i+1:03d}": ("DEGRADED" if i < 15 else "HEALTHY") for i in range(500)}

c1, c2 = st.columns(2)
with c1:
    st.markdown("#### 🛠️ Live Bit-Flip Playground")
    input_val = st.number_input("Base Register Floating-Point Value", value=3.14159265, format="%.8f")
    bit_idx = st.slider("Bit Position to Invert (0 = LSB Mantissa, 31 = MSB Sign)", 0, 31, 23)

    bits = IEEE754FaultInjector.float_to_bits(input_val)
    corrupted_bits = bits ^ (1 << bit_idx)
    corrupted_val = IEEE754FaultInjector.bits_to_float(corrupted_bits)
    rel_err = abs(corrupted_val - input_val) / (abs(input_val) + 1e-9)

    sign_b = (bits >> 31) & 1
    exp_b = (bits >> 23) & 0xFF
    man_b = bits & 0x7FFFFF

    c_sign_b = (corrupted_bits >> 31) & 1
    c_exp_b = (corrupted_bits >> 23) & 0xFF
    c_man_b = corrupted_bits & 0x7FFFFF

    bit_region = "MANTISSA (Precision Loss)"
    if bit_idx == 31: bit_region = "SIGN (Sign Inversion)"
    elif 23 <= bit_idx <= 30: bit_region = "EXPONENT (Huge Value Explosion)"

    st.markdown(f"**Target Bit Region**: `<span style='color:#06b6d4;'>{bit_region}</span>`", unsafe_allow_html=True)
    st.metric("Relative Error Spike", f"{rel_err:.4e}", "SDC Anomaly Triggered" if rel_err > 1e-5 else "Clean")

    target_node = st.selectbox("Select Node from 500 Compute Fleet", [f"gpu-node-{i+1:03d}" for i in range(500)])
    if st.button("🚀 Inject Bit-Flip into Fleet Pipeline", type="primary"):
        st.session_state.fleet_sim.nodes[target_node].is_degrading = True
        st.session_state.node_statuses[target_node] = "DEGRADED"
        st.success(f"Injected SDC Bit-Flip into {target_node} register!")
        time.sleep(0.4)
        st.rerun()

with c2:
    st.markdown("#### 🔬 IEEE-754 32-Bit Binary Breakdown")
    st.code(
        f"ORIGINAL VALUE:  {input_val:.8f}\n"
        f"Sign [31]:       {sign_b:01b}\n"
        f"Exponent [30-23]:{exp_b:08b} (Dec: {exp_b})\n"
        f"Mantissa [22-0]: {man_b:023b}\n"
        f"Binary 32-Bit:   {bits:032b}\n\n"
        f"CORRUPTED VALUE: {corrupted_val:.8f}\n"
        f"Sign [31]:       {c_sign_b:01b}\n"
        f"Exponent [30-23]:{c_exp_b:08b} (Dec: {c_exp_b})\n"
        f"Mantissa [22-0]: {c_man_b:023b}\n"
        f"Binary 32-Bit:   {corrupted_bits:032b}",
        language="text"
    )
