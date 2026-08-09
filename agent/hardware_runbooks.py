"""
AegisSilicon SDC Hardware Maintenance Runbooks.
Domain knowledge base for AI compute cluster hardware faults and recovery protocols.
"""

HARDWARE_RUNBOOKS = [
    {
        "id": "RUNBOOK-SDC-001",
        "title": "Mantissa Bit-Flip Transient Drift & Checkpoint Rollback (Loop A)",
        "fault_category": "Mantissa Single-Bit Flip",
        "symptoms": "Subtle mathematical error drift (relative error 1e-6 to 1e-3) across floating-point matrix calculations. Temperature normal, ECC silent.",
        "root_cause": "Cosmic ray bit flip or minor thermal noise in floating-point mantissa ALU registers during continuous peak GEMM execution.",
        "remediation_track": "LOOP_A_DATA_SALVAGE",
        "action_steps": [
            "1. Issue soft pause on active AI training batch assigned to node.",
            "2. Roll back model state to last verified clean gradient checkpoint.",
            "3. Reroute corrupted micro-batch for re-execution on redundant node.",
            "4. Execute diagnostic FP32 validation loop on target node for 30 seconds.",
            "5. If error resolves, resume production workload; otherwise escalate to Loop B."
        ]
    },
    {
        "id": "RUNBOOK-SDC-002",
        "title": "Exponent Bit-Flip Scale Explosion & Node Quarantine (Loop B)",
        "fault_category": "Exponent Bit Flip",
        "symptoms": "Catastrophic order-of-magnitude numerical explosion or NaN/Inf generation (relative error > 0.01). Micro-voltage droop recorded.",
        "root_cause": "Transient voltage droop on GPU power rail destabilizing exponent decoding logic in vector processing unit (VPU).",
        "remediation_track": "LOOP_B_NODE_QUARANTINE",
        "action_steps": [
            "1. Immediately fence node from active cluster workload scheduler.",
            "2. Drain remaining active inference tasks to standby compute nodes.",
            "3. Isolate node into hardware sandboxing environment.",
            "4. Run power rail voltage sweep and VPU register memory diagnostic test.",
            "5. Flag node for hardware technician inspection or RMA replacement."
        ]
    },
    {
        "id": "RUNBOOK-SDC-003",
        "title": "Persistent Silicon Degradation & Mercurial Core Quarantine (Loop B)",
        "fault_category": "Mercurial Core Silicon Aging",
        "symptoms": "Intermittent SDC errors repeating across >3 consecutive tumbling windows. Gradual thermal baseline rise.",
        "root_cause": "Physical silicon degradation due to electromigration and aging in high-density GPU matrix processing cores under continuous 24/7 load.",
        "remediation_track": "LOOP_B_NODE_QUARANTINE",
        "action_steps": [
            "1. Revoke node registration from fleet cluster manager.",
            "2. Quarantine node and record fault history in enterprise audit log.",
            "3. Trigger automated AWS EKS node replacement or EC2 auto-scaling swap.",
            "4. Store telemetry trace snapshot to Amazon S3 bucket for forensic analysis."
        ]
    }
]
