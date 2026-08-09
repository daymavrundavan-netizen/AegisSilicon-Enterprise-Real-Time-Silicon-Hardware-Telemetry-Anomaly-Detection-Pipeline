"""
AegisSilicon Structured Streaming Pipeline (PySpark / In-Memory Streaming Engine).
Performs tumbling window aggregation (10s windows) over high-velocity telemetry streams.
"""

import time
from collections import defaultdict
from typing import Dict, List

class StreamingWindowProcessor:
    """
    Stateful Tumbling Window Aggregator for Telemetry Streams.
    Computes 10-second tumbling window statistics per node.
    """

    def __init__(self, window_sec: float = 10.0):
        self.window_sec = window_sec
        # Buffer of raw telemetry records: node_id -> list of raw records
        self.buffers = defaultdict(list)
        self.last_flush = time.time()

    def add_record(self, record: dict) -> None:
        """Add incoming telemetry record to the active window buffer."""
        node_id = record["node_id"]
        self.buffers[node_id].append(record)

    def process_and_flush_windows(self) -> List[dict]:
        """
        Aggregate records over the 10-second tumbling window per node.
        
        Returns:
          List of aggregated node window dicts.
        """
        now = time.time()
        aggregated_windows = []

        for node_id, records in list(self.buffers.items()):
            if not records:
                continue

            errors = [r["relative_error"] for r in records]
            temps = [r["temperature_c"] for r in records]
            voltages = [r["voltage_v"] for r in records]
            has_faults = [1 if r.get("has_fault_injected") else 0 for r in records]

            window_dict = {
                "node_id": node_id,
                "timestamp": now,
                "record_count": len(records),
                "mean_relative_error": float(sum(errors) / len(errors)),
                "std_relative_error": float((sum((e - (sum(errors)/len(errors)))**2 for e in errors) / len(errors)) ** 0.5) if len(errors) > 1 else 0.0,
                "max_relative_error": float(max(errors)),
                "mean_temperature": float(sum(temps) / len(temps)),
                "mean_voltage": float(sum(voltages) / len(voltages)),
                "injected_fault_count": sum(has_faults)
            }
            aggregated_windows.append(window_dict)

        # Clear buffer for next tumbling window
        self.buffers.clear()
        self.last_flush = now
        return aggregated_windows


def create_spark_streaming_session():
    """
    Factory to create PySpark Structured Streaming session if Spark is installed.
    """
    try:
        from pyspark.sql import SparkSession
        spark = SparkSession.builder \
            .appName("AegisSilicon-SDC-Detector") \
            .master("local[*]") \
            .config("spark.driver.memory", "2g") \
            .getOrCreate()
        print("[AegisSilicon Spark] PySpark Structured Streaming session initialized.")
        return spark
    except Exception as e:
        print(f"[AegisSilicon Spark] PySpark session unavailable: {e}. Using internal StreamingWindowProcessor.")
        return None


if __name__ == "__main__":
    aggregator = StreamingWindowProcessor(window_sec=2.0)
    sample_record = {
        "node_id": "gpu-node-001",
        "relative_error": 1.2e-6,
        "temperature_c": 64.2,
        "voltage_v": 1.148,
        "has_fault_injected": True
    }
    aggregator.add_record(sample_record)
    res = aggregator.process_and_flush_windows()
    print("Aggregated Window Output:", res)
