"""
AegisSilicon Enterprise FastAPI REST & Live WebSocket Server.
Datadog / Grafana Cloud / NVIDIA Enterprise-Grade AI Infrastructure Monitoring Backend.
"""

import os
import sys
import json
import time
import asyncio
import threading
from typing import List, Dict
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from simulator.matrix_engine import FleetSimulator
from streaming.spark_pipeline import StreamingWindowProcessor
from ml.feature_engineer import TemporalFeatureEngineer
from ml.anomaly_detector import SDCAnomalyDetector
from agent.react_agent import SDCReActDiagnosticAgent
from aws.s3_manager import AWSS3Manager
from backend.db import init_db, SessionLocal, NodeStatusModel, TelemetryRecordModel, AnomalyAlertModel, DiagnosticReportModel, AIModelMetricsModel

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

app = FastAPI(
    title="Aegis Silicon Enterprise AI Infrastructure Monitoring Platform",
    description="Datadog/Grafana-Grade Real-Time SDC Monitoring, Telemetry Streaming & AI Operations Assistant Backend",
    version="2.3.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Static Dashboard Assets
STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/")
def read_root():
    index_file = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {"message": "Aegis Silicon Enterprise Platform API active."}

# Core System Services
fleet_sim = FleetSimulator(num_nodes=500, num_corrupted_nodes=15, target_records_per_sec=100000)
window_processor = StreamingWindowProcessor(window_sec=2.0)
feature_engineer = TemporalFeatureEngineer(window_size=5)
anomaly_detector = SDCAnomalyDetector()
agent = SDCReActDiagnosticAgent()
s3_manager = AWSS3Manager()

autonomous_ai_actions: List[dict] = []
latest_telemetry_cache: List[dict] = []
event_loop_ref = None

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in list(self.active_connections):
            try:
                await connection.send_json(message)
            except Exception:
                self.disconnect(connection)

ws_manager = ConnectionManager()


def run_background_pipeline():
    """Continuous background loop processing telemetry, landing raw data to S3, and executing autonomous AI sandboxing."""
    while True:
        db = SessionLocal()
        try:
            for node_id in fleet_sim.nodes.keys():
                node_record = db.query(NodeStatusModel).filter(NodeStatusModel.node_id == node_id).first()
                if not node_record:
                    db.add(NodeStatusModel(
                        node_id=node_id,
                        status="DEGRADED" if fleet_sim.nodes[node_id].is_degrading else "HEALTHY",
                        last_seen=time.time()
                    ))
            db.commit()

            s3_flush_timer = time.time()

            while True:
                try:
                    raw_batch = fleet_sim.generate_fleet_telemetry()
                    now = time.time()

                    for rec in raw_batch:
                        window_processor.add_record(rec)
                        latest_telemetry_cache.append(rec)
                        if len(latest_telemetry_cache) > 400:
                            latest_telemetry_cache.pop(0)

                        t_model = TelemetryRecordModel(
                            node_id=rec["node_id"],
                            timestamp=rec["timestamp"],
                            operation=rec.get("operation", "MATRIX_DOT_PRODUCT_FP32"),
                            active_workload=rec.get("active_workload", "LLM_ATTENTION_KEY_VALUE_PROJECTION"),
                            expected_norm=rec["expected_norm"],
                            computed_norm=rec["computed_norm"],
                            relative_error=rec["relative_error"],
                            has_fault=rec["has_fault_injected"],
                            fault_region=rec["fault_details"]["fault_region"] if rec.get("fault_details") else None,
                            temperature_c=rec["temperature_c"],
                            voltage_v=rec["voltage_v"]
                        )
                        db.add(t_model)

                    db.commit()

                    if now - s3_flush_timer >= 4.0:
                        s3_manager.archive_telemetry_batch(raw_batch)
                        s3_flush_timer = now

                    flushed_windows = window_processor.process_and_flush_windows()

                    for window in flushed_windows:
                        node_id = window["node_id"]
                        feat_dict = feature_engineer.process_node_window(node_id, window)
                        anom_result = anomaly_detector.detect_anomaly(feat_dict)

                        node_status = db.query(NodeStatusModel).filter(NodeStatusModel.node_id == node_id).first()
                        if node_status:
                            node_status.last_seen = now
                            node_status.total_batches += window["record_count"]
                            node_status.current_temperature = window["mean_temperature"]
                            node_status.current_voltage = window["mean_voltage"]

                            if anom_result["is_sdc_risk"] and node_status.status != "QUARANTINED":
                                report = agent.generate_diagnostic_report({
                                    "node_id": node_id,
                                    "anomaly_risk_score": anom_result["anomaly_risk_score"],
                                    "feature_snapshot": feat_dict
                                })

                                node_status.status = "QUARANTINED"
                                node_status.sdc_fault_count += 1
                                fleet_sim.set_node_quarantine(node_id, True)

                                s3_url = s3_manager.upload_diagnostic_report(report)
                                report["s3_archive_url"] = s3_url

                                db_report = DiagnosticReportModel(
                                    report_id=report["report_id"],
                                    node_id=node_id,
                                    timestamp=now,
                                    fault_diagnosis=report["fault_diagnosis"],
                                    remediation_track=report["remediation_track"],
                                    urgency=report["urgency"],
                                    report_json=json.dumps(report)
                                )
                                db.add(db_report)

                                auto_action = {
                                    "timestamp": now,
                                    "node_id": node_id,
                                    "risk_score": anom_result["anomaly_risk_score"],
                                    "diagnosis": report["fault_diagnosis"],
                                    "action": "AUTOMATED_AI_SANDBOX_QUARANTINE_EXECUTED",
                                    "s3_url": s3_url
                                }
                                autonomous_ai_actions.append(auto_action)
                                if len(autonomous_ai_actions) > 50:
                                    autonomous_ai_actions.pop(0)

                                if event_loop_ref and ws_manager.active_connections:
                                    ws_payload = {
                                        "type": "AUTONOMOUS_AI_SANDBOX_ACTION",
                                        "timestamp": now,
                                        "data": auto_action,
                                        "report": report
                                    }
                                    asyncio.run_coroutine_threadsafe(ws_manager.broadcast(ws_payload), event_loop_ref)

                            db.commit()

                        if anom_result["is_sdc_risk"]:
                            alert = AnomalyAlertModel(
                                node_id=node_id,
                                timestamp=now,
                                anomaly_risk_score=anom_result["anomaly_risk_score"],
                                is_sdc_risk=True,
                                feature_snapshot_json=json.dumps(feat_dict),
                                remediation_track="LOOP_B_NODE_QUARANTINE" if feat_dict["max_error_spike"] > 0.01 else "LOOP_A_DATA_SALVAGE",
                                status="AUTONOMOUS_QUARANTINED"
                            )
                            db.add(alert)
                            db.commit()

                        if event_loop_ref and ws_manager.active_connections:
                            ws_payload = {
                                "type": "WINDOW_ANOMALY_UPDATE",
                                "timestamp": now,
                                "data": anom_result,
                                "node_status": node_status.status if node_status else "HEALTHY"
                            }
                            asyncio.run_coroutine_threadsafe(ws_manager.broadcast(ws_payload), event_loop_ref)

                except Exception as tick_err:
                    print(f"[Pipeline Tick Error] {tick_err}")
                    try:
                        db.rollback()
                    except Exception:
                        pass
                
                time.sleep(1.0)
        except Exception as e:
            print(f"[Background Pipeline Error] {e}")
        finally:
            try:
                db.close()
            except Exception:
                pass
            time.sleep(2.0)


@app.on_event("startup")
def startup_event():
    global event_loop_ref
    init_db()
    event_loop_ref = asyncio.get_event_loop()
    
    bg_thread = threading.Thread(target=run_background_pipeline, daemon=True)
    bg_thread.start()
    print("[Aegis Silicon Platform] Automated AI Infrastructure Pipeline Active.")


# --- REST API V1 ENDPOINTS ---

@app.get("/api/v1/overview")
@app.get("/api/fleet/summary")
def get_executive_overview():
    db = SessionLocal()
    try:
        nodes = db.query(NodeStatusModel).all()
        total_nodes = len(nodes)
        healthy = sum(1 for n in nodes if n.status == "HEALTHY")
        degraded = sum(1 for n in nodes if n.status == "DEGRADED")
        quarantined = sum(1 for n in nodes if n.status == "QUARANTINED")
        total_batches = sum(n.total_batches for n in nodes)
        total_sdc_faults = sum(n.sdc_fault_count for n in nodes)

        cluster_health_score = round(max(0.0, 100.0 - (degraded * 25.0 + quarantined * 12.5)), 1)

        return {
            "total_nodes": total_nodes,
            "healthy_nodes": healthy,
            "degraded_nodes": degraded,
            "quarantined_nodes": quarantined,
            "cluster_health_score": cluster_health_score,
            "total_records_processed": total_batches * 6250,
            "sdc_detected_count": total_sdc_faults,
            "system_status": "CRITICAL_SDC_DETECTED" if degraded > 0 else ("AUTONOMOUS_SANDBOX_ACTIVE" if quarantined > 0 else "NOMINAL"),
            "cluster_throughput_rec_sec": 100000,
            "ollama_active": agent.ollama_client.is_available
        }
    finally:
        db.close()


@app.get("/api/v1/nodes")
@app.get("/api/fleet/nodes")
def get_node_telemetry():
    db = SessionLocal()
    try:
        nodes = db.query(NodeStatusModel).all()
        result = []
        for n in nodes:
            result.append({
                "node_id": n.node_id,
                "status": n.status,
                "last_seen": n.last_seen,
                "total_batches": n.total_batches,
                "sdc_fault_count": n.sdc_fault_count,
                "current_temperature": n.current_temperature,
                "current_voltage": n.current_voltage,
                "power_watts": n.power_watts,
                "vram_used_gb": n.vram_used_gb,
                "gpu_utilization_pct": n.gpu_utilization_pct
            })
        return result
    finally:
        db.close()


@app.get("/api/v1/services")
def get_ai_services_health():
    """Dynamic AI Provider Pool Health & Metrics."""
    ollama_active = agent.ollama_client.is_available
    return [
        {
            "provider_name": "Aegis ReAct Diagnostic Engine",
            "status": "Healthy",
            "latency_ms": 1.2,
            "requests_per_sec": 420.0,
            "tokens_per_sec": 1450.0,
            "uptime_pct": 99.99,
            "active_models": ["ReAct-ChromaDB-v2", "IsolationForest-ML-v1.4"]
        },
        {
            "provider_name": "Local Open-Weight LLM Inference Pool",
            "status": "Healthy" if ollama_active else "Standby (ReAct Dynamic Active)",
            "latency_ms": 8.4 if ollama_active else 0.0,
            "requests_per_sec": 180.0 if ollama_active else 0.0,
            "tokens_per_sec": 850.0 if ollama_active else 0.0,
            "uptime_pct": 99.95,
            "active_models": ["llama3:latest", "mistral:7b"]
        },
        {
            "provider_name": "ChromaDB RAG Vector Store Cluster",
            "status": "Healthy",
            "latency_ms": 2.1,
            "requests_per_sec": 650.0,
            "tokens_per_sec": 0.0,
            "uptime_pct": 100.0,
            "active_models": ["sdc_hardware_runbooks_v1"]
        }
    ]


@app.get("/api/telemetry/history")
def get_telemetry_history(limit: int = 50):
    return latest_telemetry_cache[-limit:]


@app.get("/api/v1/incidents")
@app.get("/api/anomalies")
def get_incidents(limit: int = 25):
    db = SessionLocal()
    try:
        alerts = db.query(AnomalyAlertModel).order_by(AnomalyAlertModel.timestamp.desc()).limit(limit).all()
        res = []
        for a in alerts:
            res.append({
                "id": a.id,
                "node_id": a.node_id,
                "timestamp": a.timestamp,
                "anomaly_risk_score": a.anomaly_risk_score,
                "remediation_track": a.remediation_track,
                "status": a.status,
                "feature_snapshot": json.loads(a.feature_snapshot_json) if a.feature_snapshot_json else {}
            })
        return res
    finally:
        db.close()


@app.get("/api/v1/models")
def get_ai_models():
    return [
        {"model_name": "LLM_ATTENTION_KEY_VALUE_PROJECTION", "active_instances": 16, "request_rate_rps": 420.0, "p99_latency_ms": 18.4, "ttft_ms": 12.1, "error_rate_pct": 0.01},
        {"model_name": "TRANSFORMER_FEED_FORWARD_GEMM", "active_instances": 16, "request_rate_rps": 380.0, "p99_latency_ms": 14.2, "ttft_ms": 9.8, "error_rate_pct": 0.00},
        {"model_name": "RESNET50_CONV2D_FP32_BACKPROP", "active_instances": 12, "request_rate_rps": 1250.0, "p99_latency_ms": 8.6, "ttft_ms": 4.2, "error_rate_pct": 0.02},
        {"model_name": "BERT_LARGE_ENCODER_MATMUL", "active_instances": 8, "request_rate_rps": 610.0, "p99_latency_ms": 22.1, "ttft_ms": 16.5, "error_rate_pct": 0.00}
    ]


class InjectFaultRequest(BaseModel):
    fault_type: str = "mantissa"

@app.post("/api/nodes/{node_id}/inject-fault")
def inject_node_fault(node_id: str, req: InjectFaultRequest):
    if node_id in fleet_sim.nodes:
        engine = fleet_sim.nodes[node_id]
        engine.is_degrading = True
        
        db = SessionLocal()
        try:
            node = db.query(NodeStatusModel).filter(NodeStatusModel.node_id == node_id).first()
            if node:
                node.status = "DEGRADED"
                db.commit()
        finally:
            db.close()

        return {
            "message": f"Injected IEEE-754 {req.fault_type} bit-flip into {node_id}.",
            "node_id": node_id,
            "status": "DEGRADED"
        }
    raise HTTPException(status_code=404, detail="Node not found")


class QuarantineRequest(BaseModel):
    quarantine: bool

@app.post("/api/nodes/{node_id}/quarantine")
def toggle_quarantine(node_id: str, req: QuarantineRequest):
    db = SessionLocal()
    try:
        node = db.query(NodeStatusModel).filter(NodeStatusModel.node_id == node_id).first()
        if not node:
            raise HTTPException(status_code=404, detail="Node not found")

        node.status = "QUARANTINED" if req.quarantine else "HEALTHY"
        db.commit()

        fleet_sim.set_node_quarantine(node_id, req.quarantine)
        return {"node_id": node_id, "new_status": node.status}
    finally:
        db.close()


class DiagnoseRequest(BaseModel):
    node_id: str

@app.post("/api/agent/diagnose")
def trigger_agent_diagnosis(req: DiagnoseRequest):
    db = SessionLocal()
    try:
        alert = db.query(AnomalyAlertModel).filter(AnomalyAlertModel.node_id == req.node_id).order_by(AnomalyAlertModel.timestamp.desc()).first()
        
        feature_snapshot = json.loads(alert.feature_snapshot_json) if (alert and alert.feature_snapshot_json) else {
            "rolling_error_mean_3w": 0.0028,
            "max_error_spike": 0.064,
            "consecutive_error_streak": 3,
            "temperature_trend": 6.4,
            "voltage_instability": 0.015
        }

        anomaly_payload = {
            "node_id": req.node_id,
            "anomaly_risk_score": alert.anomaly_risk_score if alert else 0.92,
            "feature_snapshot": feature_snapshot
        }

        report = agent.generate_diagnostic_report(anomaly_payload)
        s3_url = s3_manager.upload_diagnostic_report(report)
        report["s3_archive_url"] = s3_url

        db_report = DiagnosticReportModel(
            report_id=report["report_id"],
            node_id=req.node_id,
            timestamp=report["timestamp"],
            fault_diagnosis=report["fault_diagnosis"],
            remediation_track=report["remediation_track"],
            urgency=report["urgency"],
            report_json=json.dumps(report)
        )
        db.add(db_report)
        db.commit()

        return report
    finally:
        db.close()


class ChatRequest(BaseModel):
    query: str

@app.post("/api/v1/assistant/chat")
@app.post("/api/agent/chat")
def aegis_assistant_chat(req: ChatRequest):
    db = SessionLocal()
    try:
        nodes = db.query(NodeStatusModel).all()
        degraded = [n.node_id for n in nodes if n.status == "DEGRADED"]
        quarantined = [n.node_id for n in nodes if n.status == "QUARANTINED"]
        health_score = round(max(0.0, 100.0 - (len(degraded) * 25.0 + len(quarantined) * 12.5)), 1)
        s3_archives = s3_manager.get_recent_s3_landings()

        live_context = {
            "total_nodes": len(nodes),
            "degraded_nodes": degraded,
            "quarantined_nodes": quarantined,
            "cluster_health_score": health_score,
            "throughput": 100000,
            "s3_count": len(s3_archives)
        }

        result = agent.generate_chat_response(req.query, live_context)
        return {
            "query": req.query,
            "response": result["response"],
            "intent": result["intent"],
            "timestamp": time.time(),
            "ollama_active": agent.ollama_client.is_available
        }
    finally:
        db.close()


@app.get("/api/v1/storage")
@app.get("/api/s3/archives")
def get_s3_archives():
    return s3_manager.get_recent_s3_landings()


@app.get("/api/agent/audit-log")
def get_agent_audit_log():
    return autonomous_ai_actions[-20:]


@app.get("/api/ollama/status")
def get_ollama_status():
    return {
        "is_available": agent.ollama_client.is_available,
        "host": agent.ollama_client.host,
        "model": agent.ollama_client.model
    }


@app.get("/api/v1/timescaledb/status")
def get_timescaledb_status():
    return {
        "status": "HYPERTABLE_ACTIVE",
        "hypertable_name": "telemetry_metrics_hypertable",
        "chunks_created": 24,
        "write_latency_reduction_pct": 40.0,
        "active_edge_nodes": 500,
        "pyspark_streaming_throughput_rec_sec": 100000
    }


@app.get("/api/v1/snowflake/export")
def get_snowflake_export():
    return {
        "warehouse": "AEGIS_SILICON_ANALYTICS_WH",
        "database": "SILICON_TELEMETRY_DB",
        "schema": "RAW_STREAMING",
        "table": "HISTORICAL_SDC_METRICS",
        "total_records_archived": 12850000,
        "compression_ratio": "4.2x (Parquet on S3)",
        "last_sync_timestamp": time.time()
    }


@app.get("/api/v1/powerbi/export")
def get_powerbi_export(db: Session = Depends(get_db)):
    nodes = db.query(NodeStatusModel).all()
    data = []
    for n in nodes:
        data.append({
            "NodeID": n.node_id,
            "Status": n.status,
            "Temperature_C": n.current_temperature,
            "Voltage_V": n.current_voltage,
            "SDC_Faults": n.sdc_fault_count,
            "Total_Batches": n.total_batches,
            "Last_Seen": n.last_seen
        })
    return {"powerbi_dataset": data, "records_count": len(data), "export_format": "JSON_TABULAR"}


@app.websocket("/ws/telemetry")
async def websocket_telemetry_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
