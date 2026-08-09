"""
AegisSilicon Ollama Local LLM Client Integration.
Connects to local or EC2-hosted Ollama instance (http://localhost:11434) for context-aware SDC reasoning.
"""

import json
import requests
from typing import Optional

class OllamaLLMClient:
    """
    Client for Ollama open-weight LLMs (Llama 3, Mistral, Phi-3).
    """

    def __init__(self, host: str = "http://localhost:11434", model: str = "llama3"):
        self.host = host.rstrip('/')
        self.model = model
        self.is_available = False
        self._check_health()

    def _check_health(self):
        """Check if Ollama server is running and reachable."""
        try:
            res = requests.get(f"{self.host}/api/tags", timeout=1.5)
            if res.status_code == 200:
                self.is_available = True
                print(f"[Ollama LLM] Connected to local Ollama server at {self.host}.")
                return
        except Exception:
            pass
        self.is_available = False
        print(f"[Ollama LLM] Local Ollama server offline at {self.host}. Using deterministic ReAct reasoning engine.")

    def generate_sdc_diagnosis(self, node_id: str, feature_snap: dict, matched_runbook: dict) -> Optional[str]:
        """
        Query Ollama LLM for deep hardware diagnostic reasoning.
        """
        if not self.is_available:
            self._check_health()
            if not self.is_available:
                return None

        prompt = f"""
You are AegisSilicon Autonomous Hardware AI Agent monitoring GPU/TPU compute nodes for Silent Data Corruption (SDC).
Analyze the following degrading node telemetry and generate a concise technical diagnosis and recovery plan:

Node ID: {node_id}
Rolling Error Mean (3 Windows): {feature_snap.get('rolling_error_mean_3w', 0.0):.8f}
Max Error Spike: {feature_snap.get('max_error_spike', 0.0):.6f}
Consecutive Error Streak: {feature_snap.get('consecutive_error_streak', 0)}
Temperature Offset: +{feature_snap.get('temperature_trend', 0.0):.1f}C
Voltage Instability: {feature_snap.get('voltage_instability', 0.0):.4f}

Matched Hardware Runbook: {matched_runbook.get('title') if matched_runbook else 'Generic SDC'}
Suggested Remediation Track: {matched_runbook.get('remediation_track') if matched_runbook else 'LOOP_B_NODE_QUARANTINE'}

Provide:
1. Exact Micro-Fault Analysis (Mantissa float drift vs Exponent power rail burst).
2. Autonomous Closed-Loop Action Plan.
Keep response under 150 words.
"""

        try:
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False
            }
            res = requests.post(f"{self.host}/api/generate", json=payload, timeout=8.0)
            if res.status_code == 200:
                data = res.json()
                return data.get("response", "").strip()
        except Exception as e:
            print(f"[Ollama Query Error] {e}")

        return None
