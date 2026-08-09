# AegisSilicon: Real-Time Silent Data Corruption Detection for AI Compute Workloads

![AegisSilicon Enterprise Architecture](https://img.shields.io/badge/AegisSilicon-Enterprise_v1.0-06b6d4?style=for-the-badge)
![AWS Ready](https://img.shields.io/badge/AWS-EC2_%7C_S3_%7C_EKS-232F3E?style=for-the-badge&logo=amazon-aws)
![Python PySpark](https://img.shields.io/badge/PySpark-Structured_Streaming-E25A1C?style=for-the-badge&logo=apachespark)
![Scikit-Learn](https://img.shields.io/badge/Scikit_Learn-Isolation_Forest-F7931E?style=for-the-badge&logo=scikit-learn)
![LangChain RAG](https://img.shields.io/badge/LangChain-ReAct_RAG_Agent-121212?style=for-the-badge)

AegisSilicon is a production-grade, real-time telemetry processing and anomaly mitigation system engineered to detect **Silent Data Corruption (SDC)** in high-performance AI compute clusters (GPUs, TPUs, CPUs). 

As documented in Google's *"Cores That Don't Count"* (Hochschild et al.) and Meta's *"Silent Data Corruption at Scale"* (Dixit et al.), micro-level silicon bit-flips produce mathematically corrupted calculations without throwing OS crashes or hardware alerts. AegisSilicon bridges this gap by monitoring mathematical calculation drift across tumbling observation windows using unsupervised machine learning and automated LangChain RAG AI remediation agents.

---

## Technical Stack

| Layer | Technology | Function |
| :--- | :--- | :--- |
| **Fault Injection** | Python 3.10 + IEEE-754 Bit-Flip Engine | Simulates bit-accurate IEEE-754 float32 flips in Sign (bit 31), Exponent (bits 23-30), and Mantissa (bits 0-22) regions. |
| **Ingestion Stream** | Apache Kafka / PySpark Structured Streaming | 10-second tumbling windows over 128,000 telemetry events/sec from concurrent edge compute nodes. |
| **Feature Engineering**| Temporal Cross-Window Engine | 6 stateful rolling features: `rolling_error_mean_3w`, `error_volatility`, `consecutive_error_streak`, `max_error_spike`, `temperature_trend`, `voltage_instability`. |
| **ML Anomaly Engine** | Scikit-Learn `IsolationForest` + `StandardScaler` | Unsupervised detection of cross-window node degradation with continuous risk scoring. |
| **AI RAG Agent** | LangChain ReAct Agent + ChromaDB | Vector search over hardware maintenance runbooks; automates *Loop A (Data Salvage / Checkpoint Rollback)* vs *Loop B (Hardware Quarantine)*. |
| **API & Database** | FastAPI + WebSockets + SQLAlchemy (SQLite/PostgreSQL) | High-concurrency REST endpoints and live WebSocket telemetry stream. |
| **Cloud Storage** | AWS S3 + AWS EC2 / Docker Compose | Automated archiving of telemetry micro-batches, model artifacts, and diagnostic reports. |
| **Live Dashboard** | React + Vite + Tailwind/CSS + Recharts | Cyberpunk enterprise analytics console with cluster node grid, live error charts, SDC feed, and RAG diagnostic viewer. |

---

## Directory Structure

```text
aegis_silicon/
├── simulator/
│   ├── fault_injector.py       # IEEE-754 single-bit flip fault injection engine
│   ├── matrix_engine.py        # Matrix dot-product compute engine & fleet simulator
│   └── producer.py             # Kafka / live telemetry stream producer
├── streaming/
│   └── spark_pipeline.py       # PySpark 10s tumbling window processor
├── ml/
│   ├── feature_engineer.py     # Cross-window rolling temporal feature engineering
│   └── anomaly_detector.py     # Scikit-Learn IsolationForest anomaly detector
├── agent/
│   ├── hardware_runbooks.py    # Technical hardware SDC maintenance runbooks
│   ├── rag_knowledge_base.py   # ChromaDB vector store & semantic search
│   └── react_agent.py          # LangChain ReAct diagnostic & remediation agent
├── aws/
│   └── s3_manager.py           # Amazon S3 cloud telemetry archive manager
├── backend/
│   ├── db.py                   # SQLAlchemy database schemas (NodeStatus, Telemetry, Alerts)
│   └── app.py                  # FastAPI REST & WebSocket streaming server
├── frontend/                   # React + Vite analytics console
│   ├── src/
│   │   ├── components/         # Navbar, MetricsOverview, NodeTopologyGrid, TelemetryChart, AnomalyFeed, RAGDiagnosticModal
│   │   ├── App.jsx
│   │   └── main.jsx
│   └── package.json
├── deploy/
│   ├── docker-compose.yml      # Full production docker stack (Kafka, Zookeeper, Backend, Frontend)
│   ├── Dockerfile.backend
│   ├── Dockerfile.frontend
│   ├── ec2_deploy.sh           # AWS EC2 deployment automation script
│   └── terraform_aws.tf        # Infrastructure as Code for AWS EC2 & S3
├── tests/                      # Automated test suite
└── requirements.txt
```

---

## Quick Start & Local Execution

### 1. Run Backend Server
```bash
# Install Python dependencies
pip install -r requirements.txt

# Launch FastAPI REST & Live WebSocket Server
python -m backend.app
```
The REST API will be live at `http://localhost:8000` with Swagger docs at `http://localhost:8000/docs`.

### 2. Launch React Analytics Console
```bash
cd frontend
npm install
npm run dev
```
Open `http://localhost:5173` to access the live dashboard.

---

## AWS EC2 & Cloud Deployment

To deploy the entire production containerized stack to an AWS EC2 instance with S3 cloud storage:

```bash
# Make deployment script executable
chmod +x deploy/ec2_deploy.sh

# Run automated AWS deployment
./deploy/ec2_deploy.sh
```

Or deploy infrastructure using Terraform:
```bash
cd deploy
terraform init
terraform apply
```

---

## Verification & Testing

Execute the unit and integration test suite:

```bash
python -c "
from tests.test_fault_injector import test_mantissa_bit_flip, test_exponent_bit_flip, test_sign_bit_flip
test_mantissa_bit_flip(); test_exponent_bit_flip(); test_sign_bit_flip()

from tests.test_ml import test_feature_engineering_rolling_streak, test_anomaly_detection_scoring
test_feature_engineering_rolling_streak(); test_anomaly_detection_scoring()

from tests.test_agent import test_rag_knowledge_base_query, test_react_agent_diagnostic_generation
test_rag_knowledge_base_query(); test_react_agent_diagnostic_generation()
print('ALL AEGIS SILICON TESTS PASSED SUCCESSFULLY.')
"
```
