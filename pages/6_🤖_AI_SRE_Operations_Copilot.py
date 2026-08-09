"""
AI SRE Operations Copilot (LangChain RAG)
"""

import os
import sys
import streamlit as st

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from agent.react_agent import SDCReActDiagnosticAgent

st.set_page_config(page_title="AI SRE Copilot | Aegis Silicon", page_icon="🤖", layout="wide")

st.markdown("""
<style>
    .stAppViewContainer { background-color: #030712 !important; color: #f3f4f6 !important; }
    [data-testid="stSidebar"] { background-color: #090d16 !important; }
    h1, h2, h3, h4, h5, h6, p, span, label { color: #f3f4f6 !important; font-family: 'Inter', sans-serif !important; }
</style>
""", unsafe_allow_html=True)

st.title("🤖 Aegis AI SRE Operations Copilot (LangChain RAG)")
st.caption("Interactive SRE assistant powered by ChromaDB vector search & ReAct reasoning engine")

if "agent" not in st.session_state:
    st.session_state.agent = SDCReActDiagnosticAgent()
if "chat_history" not in st.session_state:
    st.session_state.chat_history = [
        {"role": "assistant", "content": "👋 Hello! I am Aegis AI Operations Copilot powered by LangChain RAG. How can I assist you with your 500-node AI infrastructure today?"}
    ]

st.markdown("#### Quick Command Chips")
chip1, chip2, chip3 = st.columns(3)
with chip1:
    if st.button("⚡ Diagnose Degraded Nodes"):
        q_text = "What is the status of degraded nodes and their SDC fault risks?"
        st.session_state.chat_history.append({"role": "user", "content": q_text})
        rep = st.session_state.agent.generate_chat_response(q_text, {"total_nodes": 500, "degraded_nodes": 15})["response"]
        st.session_state.chat_history.append({"role": "assistant", "content": rep})
        st.rerun()

with chip2:
    if st.button("📖 ChromaDB Hardware Runbook"):
        q_text = "What is the hardware remediation runbook for IEEE-754 exponent SDC bit-flips?"
        st.session_state.chat_history.append({"role": "user", "content": q_text})
        rep = st.session_state.agent.generate_chat_response(q_text, {"total_nodes": 500})["response"]
        st.session_state.chat_history.append({"role": "assistant", "content": rep})
        st.rerun()

with chip3:
    if st.button("📊 Summarize 500 Fleet Health"):
        q_text = "Summarize the cluster health index, PySpark streaming rate, and S3 landings."
        st.session_state.chat_history.append({"role": "user", "content": q_text})
        rep = st.session_state.agent.generate_chat_response(q_text, {"total_nodes": 500, "health": 94.0})["response"]
        st.session_state.chat_history.append({"role": "assistant", "content": rep})
        st.rerun()

for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

if user_prompt := st.chat_input("Ask SRE Copilot..."):
    st.session_state.chat_history.append({"role": "user", "content": user_prompt})
    with st.chat_message("user"):
        st.write(user_prompt)

    live_ctx = {"total_nodes": 500, "degraded_nodes": 15, "quarantined_nodes": 2, "cluster_health_score": 94.0}
    reply_txt = st.session_state.agent.generate_chat_response(user_prompt, live_ctx)["response"]

    st.session_state.chat_history.append({"role": "assistant", "content": reply_txt})
    with st.chat_message("assistant"):
        st.write(reply_txt)
