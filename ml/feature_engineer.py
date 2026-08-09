"""
AegisSilicon Cross-Window Feature Engineering Engine.
Engineers stateful rolling temporal features across tumbling windows to encode cross-window memory.
"""

from collections import deque
import numpy as np
import pandas as pd

class TemporalFeatureEngineer:
    """
    Maintains stateful sliding window history for each compute node.
    Calculates rolling features across multiple 10-second observation windows.
    """

    def __init__(self, window_size: int = 5, error_threshold: float = 1e-6):
        self.window_size = window_size
        self.error_threshold = error_threshold
        # Per node window histories: node_id -> deque of window metrics dicts
        self.node_histories = {}

    def process_node_window(self, node_id: str, window_metrics: dict) -> dict:
        """
        Process a single 10s window metric for a node and extract 6 cross-window rolling features.
        
        window_metrics should contain:
          - mean_relative_error
          - std_relative_error
          - max_relative_error
          - mean_temperature
          - mean_voltage
        """
        if node_id not in self.node_histories:
            self.node_histories[node_id] = deque(maxlen=self.window_size)

        history = self.node_histories[node_id]
        history.append(window_metrics)

        # Extract temporal series across history
        errors = [w.get("mean_relative_error", 0.0) for w in history]
        max_errors = [w.get("max_relative_error", 0.0) for w in history]
        temps = [w.get("mean_temperature", 62.0) for w in history]
        voltages = [w.get("mean_voltage", 1.15) for w in history]

        # 1. Rolling error mean (over 3-5 windows)
        rolling_error_mean = float(np.mean(errors[-3:]))

        # 2. Error Volatility (std dev of errors across windows)
        error_volatility = float(np.std(errors)) if len(errors) > 1 else 0.0

        # 3. Consecutive Error Streak (count of consecutive windows with error exceeding SDC threshold)
        streak = 0
        for e in reversed(errors):
            if e >= self.error_threshold:
                streak += 1
            else:
                break

        # 4. Max Error Spike
        max_error_spike = float(np.max(max_errors))

        # 5. Temperature Trend (delta from baseline)
        temperature_trend = float(np.mean(temps) - 62.0)

        # 6. Voltage Instability (variance)
        voltage_instability = float(np.var(voltages)) if len(voltages) > 1 else 0.0

        feature_vector = {
            "node_id": node_id,
            "timestamp": window_metrics.get("timestamp"),
            "rolling_error_mean_3w": rolling_error_mean,
            "error_volatility": error_volatility,
            "consecutive_error_streak": streak,
            "max_error_spike": max_error_spike,
            "temperature_trend": temperature_trend,
            "voltage_instability": voltage_instability
        }

        return feature_vector

    def extract_feature_matrix(self, feature_dicts: list) -> np.ndarray:
        """Convert list of feature dicts to 2D numpy array for ML model input."""
        cols = [
            "rolling_error_mean_3w",
            "error_volatility",
            "consecutive_error_streak",
            "max_error_spike",
            "temperature_trend",
            "voltage_instability"
        ]
        df = pd.DataFrame(feature_dicts)
        return df[cols].values
