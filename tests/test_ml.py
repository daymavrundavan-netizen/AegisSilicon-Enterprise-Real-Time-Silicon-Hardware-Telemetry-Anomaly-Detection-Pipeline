"""
Unit Tests for Machine Learning Feature Engineering and Isolation Forest.
"""

from ml.feature_engineer import TemporalFeatureEngineer
from ml.anomaly_detector import SDCAnomalyDetector

def test_feature_engineering_rolling_streak():
    engineer = TemporalFeatureEngineer(window_size=5, error_threshold=1e-5)
    
    w1 = {"timestamp": 1.0, "mean_relative_error": 1e-8, "max_relative_error": 1e-7, "mean_temperature": 62.0, "mean_voltage": 1.15}
    w2 = {"timestamp": 2.0, "mean_relative_error": 2e-8, "max_relative_error": 2e-7, "mean_temperature": 62.1, "mean_voltage": 1.15}
    w3 = {"timestamp": 3.0, "mean_relative_error": 1e-4, "max_relative_error": 1e-3, "mean_temperature": 64.0, "mean_voltage": 1.14}
    w4 = {"timestamp": 4.0, "mean_relative_error": 5e-4, "max_relative_error": 5e-3, "mean_temperature": 66.2, "mean_voltage": 1.13}

    engineer.process_node_window("gpu-001", w1)
    engineer.process_node_window("gpu-001", w2)
    engineer.process_node_window("gpu-001", w3)
    feat4 = engineer.process_node_window("gpu-001", w4)

    assert feat4["consecutive_error_streak"] == 2
    assert feat4["rolling_error_mean_3w"] > 1e-5
    assert feat4["temperature_trend"] > 0.0

def test_anomaly_detection_scoring():
    detector = SDCAnomalyDetector()
    
    normal_feats = {
        "node_id": "gpu-normal",
        "rolling_error_mean_3w": 1e-8,
        "error_volatility": 1e-9,
        "consecutive_error_streak": 0,
        "max_error_spike": 1e-7,
        "temperature_trend": 0.0,
        "voltage_instability": 0.0001
    }
    
    corrupt_feats = {
        "node_id": "gpu-corrupt",
        "rolling_error_mean_3w": 0.005,
        "error_volatility": 0.002,
        "consecutive_error_streak": 4,
        "max_error_spike": 0.05,
        "temperature_trend": 7.5,
        "voltage_instability": 0.02
    }

    res_normal = detector.detect_anomaly(normal_feats)
    res_corrupt = detector.detect_anomaly(corrupt_feats)

    assert res_normal["is_sdc_risk"] is False
    assert res_corrupt["is_sdc_risk"] is True
    assert res_corrupt["anomaly_risk_score"] > 0.60

if __name__ == "__main__":
    test_feature_engineering_rolling_streak()
    test_anomaly_detection_scoring()
    print("ALL ML ANOMALY ENGINE TESTS PASSED.")
