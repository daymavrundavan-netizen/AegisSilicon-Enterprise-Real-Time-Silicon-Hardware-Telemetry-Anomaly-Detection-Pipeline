"""
AegisSilicon Isolation Forest Anomaly Detection Engine.
Unsupervised machine learning model trained on cross-window rolling features.
"""

import os
import joblib
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from ml.feature_engineer import TemporalFeatureEngineer

MODEL_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_FILE = os.path.join(MODEL_DIR, "isolation_forest.pkl")
SCALER_FILE = os.path.join(MODEL_DIR, "scaler.pkl")

class SDCAnomalyDetector:
    """
    Unsupervised Isolation Forest model for Silent Data Corruption detection.
    """

    def __init__(self, contamination: float = 0.10):
        self.contamination = contamination
        self.scaler = StandardScaler()
        self.model = IsolationForest(
            n_estimators=100,
            contamination=self.contamination,
            random_state=42,
            n_jobs=-1
        )
        self.is_trained = False
        self._load_or_train()

    def train(self, X_clean: np.ndarray, X_corrupted: np.ndarray):
        """
        Train Isolation Forest on baseline clean telemetry and injected fault samples.
        """
        X_all = np.vstack([X_clean, X_corrupted])
        X_scaled = self.scaler.fit_transform(X_all)
        self.model.fit(X_scaled)
        self.is_trained = True
        
        # Save model artifacts
        joblib.dump(self.model, MODEL_FILE)
        joblib.dump(self.scaler, SCALER_FILE)
        print(f"[SDCAnomalyDetector] Model trained on {len(X_all)} samples and saved.")

    def _load_or_train(self):
        """Load trained model from disk or auto-generate synthetic training dataset."""
        if os.path.exists(MODEL_FILE) and os.path.exists(SCALER_FILE):
            try:
                self.model = joblib.load(MODEL_FILE)
                self.scaler = joblib.load(SCALER_FILE)
                self.is_trained = True
                print("[SDCAnomalyDetector] Loaded pre-trained model artifacts.")
                return
            except Exception as e:
                print(f"[SDCAnomalyDetector] Failed loading saved model: {e}")

        # Train on synthetic baseline
        self.train_synthetic_baseline()

    def train_synthetic_baseline(self):
        """Generate synthetic dataset matching normal hardware vs SDC degradation."""
        np.random.seed(42)
        n_normal = 900
        n_corrupt = 100

        # Normal telemetry features (clean baseline floating point variance)
        normal_features = np.column_stack([
            np.random.exponential(1e-8, n_normal),  # rolling_error_mean_3w
            np.random.exponential(1e-9, n_normal),  # error_volatility
            np.zeros(n_normal),                     # consecutive_error_streak
            np.random.exponential(1e-7, n_normal),  # max_error_spike
            np.random.normal(0.0, 0.2, n_normal),   # temp trend
            np.random.normal(0.0, 0.0005, n_normal) # voltage instability
        ])

        # Corrupted telemetry features (Mantissa/Exponent flips)
        corrupted_features = np.column_stack([
            np.random.uniform(1e-4, 1e-1, n_corrupt),  # rolling_error_mean_3w
            np.random.uniform(1e-4, 1e-2, n_corrupt),  # error_volatility
            np.random.randint(2, 6, n_corrupt),        # consecutive_error_streak
            np.random.uniform(1e-3, 1.0, n_corrupt),   # max_error_spike
            np.random.normal(6.0, 2.0, n_corrupt),     # temp trend
            np.random.normal(0.02, 0.01, n_corrupt)    # voltage instability
        ])

        self.train(normal_features, corrupted_features)

    def detect_anomaly(self, feature_dict: dict) -> dict:
        """
        Evaluate a single node's feature vector for SDC anomaly.
        """
        vector = np.array([[
            feature_dict["rolling_error_mean_3w"],
            feature_dict["error_volatility"],
            feature_dict["consecutive_error_streak"],
            feature_dict["max_error_spike"],
            feature_dict["temperature_trend"],
            feature_dict["voltage_instability"]
        ]])

        scaled_vector = self.scaler.transform(vector)
        pred = self.model.predict(scaled_vector)[0]
        raw_score = self.model.score_samples(scaled_vector)[0]

        # Map raw score to 0.0 - 1.0 anomaly risk index
        anomaly_risk = float(np.clip(0.5 - raw_score, 0.0, 1.0))
        is_sdc = bool(pred == -1 or feature_dict["rolling_error_mean_3w"] > 1e-5 or feature_dict["consecutive_error_streak"] >= 2)

        return {
            "node_id": feature_dict["node_id"],
            "timestamp": feature_dict.get("timestamp"),
            "anomaly_label": int(pred),
            "anomaly_risk_score": round(anomaly_risk, 4),
            "is_sdc_risk": is_sdc,
            "feature_snapshot": feature_dict
        }
