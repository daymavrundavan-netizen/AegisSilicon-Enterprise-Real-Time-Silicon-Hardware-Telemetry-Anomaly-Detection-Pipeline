"""
AegisSilicon Enterprise Database Models & Persistence Layer.
Supports SQLite and PostgreSQL (TimescaleDB) for enterprise AI infrastructure monitoring.
"""

import os
import json
import time
from sqlalchemy import create_engine, Column, String, Float, Integer, Boolean, Text, DateTime, func
from sqlalchemy.orm import declarative_base, sessionmaker

DB_PATH = os.path.join(os.path.dirname(__file__), "aegis_silicon.db")
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DB_PATH}")

if "sqlite" in DATABASE_URL:
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False, "timeout": 30}
    )
    from sqlalchemy import event
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA busy_timeout=5000")
        cursor.close()
else:
    engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class NodeStatusModel(Base):
    __tablename__ = "node_status"
    
    node_id = Column(String, primary_key=True, index=True)
    status = Column(String, default="HEALTHY")  # HEALTHY, DEGRADED, QUARANTINED
    last_seen = Column(Float, default=time.time)
    total_batches = Column(Integer, default=0)
    sdc_fault_count = Column(Integer, default=0)
    current_temperature = Column(Float, default=62.0)
    current_voltage = Column(Float, default=1.15)
    power_watts = Column(Float, default=320.0)
    vram_used_gb = Column(Float, default=67.2)
    gpu_utilization_pct = Column(Float, default=85.0)

class TelemetryRecordModel(Base):
    __tablename__ = "telemetry_records"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    node_id = Column(String, index=True)
    timestamp = Column(Float, index=True)
    operation = Column(String, default="MATRIX_DOT_PRODUCT_FP32")
    active_workload = Column(String, default="LLM_ATTENTION_KEY_VALUE_PROJECTION")
    expected_norm = Column(Float)
    computed_norm = Column(Float)
    relative_error = Column(Float)
    has_fault = Column(Boolean, default=False)
    fault_region = Column(String, nullable=True)
    temperature_c = Column(Float)
    voltage_v = Column(Float)

class AnomalyAlertModel(Base):
    __tablename__ = "anomaly_alerts"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    node_id = Column(String, index=True)
    timestamp = Column(Float, index=True)
    anomaly_risk_score = Column(Float)
    is_sdc_risk = Column(Boolean, default=True)
    feature_snapshot_json = Column(Text)
    remediation_track = Column(String, default="LOOP_A_DATA_SALVAGE")
    status = Column(String, default="AUTONOMOUS_QUARANTINED")

class AIModelMetricsModel(Base):
    __tablename__ = "ai_model_metrics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    model_name = Column(String, index=True)
    active_instances = Column(Integer, default=16)
    request_rate_rps = Column(Float, default=420.0)
    p99_latency_ms = Column(Float, default=18.4)
    ttft_ms = Column(Float, default=12.1)
    error_rate_pct = Column(Float, default=0.01)

class DiagnosticReportModel(Base):
    __tablename__ = "diagnostic_reports"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    report_id = Column(String, unique=True, index=True)
    node_id = Column(String, index=True)
    timestamp = Column(Float)
    fault_diagnosis = Column(String)
    remediation_track = Column(String)
    urgency = Column(String)
    report_json = Column(Text)

def init_db():
    Base.metadata.create_all(bind=engine)
    if "sqlite" in DATABASE_URL:
        with engine.connect() as conn:
            from sqlalchemy import text
            for col, col_type in [("power_watts", "FLOAT DEFAULT 320.0"), ("vram_used_gb", "FLOAT DEFAULT 67.2"), ("gpu_utilization_pct", "FLOAT DEFAULT 85.0")]:
                try:
                    conn.execute(text(f"ALTER TABLE node_status ADD COLUMN {col} {col_type}"))
                    conn.commit()
                except Exception:
                    pass
    print(f"[Database] Enterprise database tables initialized at '{DATABASE_URL}'.")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
