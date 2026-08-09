"""
AegisSilicon Telemetry Kafka Producer & Live Stream Publisher.
Streams high-velocity compute telemetry to Kafka topic `gpu-telemetry` or local streaming queue.
"""

import json
import time
import threading
from typing import Callable, Optional
from simulator.matrix_engine import FleetSimulator

class TelemetryProducer:
    """
    Publishes real-time telemetry events to Kafka or local stream bus.
    """

    def __init__(self, bootstrap_servers: str = "localhost:9092", topic: str = "gpu-telemetry", num_nodes: int = 16, target_records_per_sec: int = 100000):
        self.bootstrap_servers = bootstrap_servers
        self.topic = topic
        self.simulator = FleetSimulator(num_nodes=num_nodes, num_corrupted_nodes=3, target_records_per_sec=target_records_per_sec)
        self.kafka_producer = None
        self.is_running = False
        self.listeners = []
        self._init_kafka()

    def _init_kafka(self):
        """Attempt to initialize Kafka producer if cluster is reachable."""
        try:
            from kafka import KafkaProducer
            self.kafka_producer = KafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                api_version=(2, 0, 0),
                request_timeout_ms=1000
            )
            print(f"[AegisSilicon Producer] Connected to Apache Kafka at {self.bootstrap_servers}")
        except Exception:
            print("[AegisSilicon Producer] Running in Standalone Streaming Mode (Kafka offline/standalone).")
            self.kafka_producer = None

    def subscribe(self, callback: Callable[[dict], None]):
        """Register a callback for local streaming events."""
        self.listeners.append(callback)

    def publish_event(self, record: dict):
        """Publish telemetry record to Kafka and local listeners."""
        if self.kafka_producer:
            try:
                self.kafka_producer.send(self.topic, record)
            except Exception as e:
                print(f"[Kafka Error] {e}")
        
        for callback in self.listeners:
            try:
                callback(record)
            except Exception as err:
                print(f"[Callback Error] {err}")

    def start_streaming(self, interval_sec: float = 0.5):
        """Start asynchronous telemetry generator thread."""
        self.is_running = True
        
        def _loop():
            while self.is_running:
                batch = self.simulator.generate_fleet_telemetry()
                for record in batch:
                    self.publish_event(record)
                time.sleep(interval_sec)

        thread = threading.Thread(target=_loop, daemon=True)
        thread.start()

    def stop_streaming(self):
        self.is_running = False


if __name__ == "__main__":
    producer = TelemetryProducer(num_nodes=8)
    def on_event(rec):
        print(f"Node: {rec['node_id']} | RelErr: {rec['relative_error']:.8f} | Temp: {rec['temperature_c']}C")

    producer.subscribe(on_event)
    producer.start_streaming(interval_sec=1.0)
    print("Streaming started. Press Ctrl+C to stop.")
    try:
        time.sleep(5)
    finally:
        producer.stop_streaming()
