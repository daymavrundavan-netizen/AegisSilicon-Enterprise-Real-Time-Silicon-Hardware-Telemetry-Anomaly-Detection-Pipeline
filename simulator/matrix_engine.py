"""
AegisSilicon Matrix Dot-Product Telemetry Engine.
Simulates high-velocity AI compute workloads across concurrent GPU/CPU nodes.
"""

import time
import random
import numpy as np
from simulator.fault_injector import IEEE754FaultInjector

class MatrixComputeEngine:
    """
    Simulates matrix dot-product operations on AI compute nodes.
    Injects physical hardware SDC faults based on node degradation state.
    """

    def __init__(self, node_id: str, is_degrading: bool = False, fault_probability: float = 0.05):
        self.node_id = node_id
        self.is_degrading = is_degrading
        self.fault_probability = fault_probability
        self.forced_fault_region = None
        self.matrix_dim = (64, 64)
        self.base_temperature = 62.0  # Celsius
        self.base_voltage = 1.15      # Volts

    def inject_forced_fault(self, fault_type: str = "mantissa"):
        """Force an immediate IEEE-754 bit-flip fault injection on the next computation batch."""
        self.is_degrading = True
        self.forced_fault_region = fault_type

    def run_batch(self) -> dict:
        """
        Execute a matrix dot-product computation batch and calculate errors.
        """
        # Generate random input matrices A and B
        A = np.random.randn(*self.matrix_dim).astype(np.float32)
        B = np.random.randn(*self.matrix_dim).astype(np.float32)

        # Ground truth matrix dot product
        C_expected = np.matmul(A, B)
        expected_norm = float(np.linalg.norm(C_expected))

        # Computed matrix (starts identical)
        C_computed = C_expected.copy()
        
        # AI Workload selection
        workloads = [
            "LLM_ATTENTION_KEY_VALUE_PROJECTION",
            "RESNET50_CONV2D_FP32_BACKPROP",
            "TRANSFORMER_FEED_FORWARD_GEMM",
            "DIFFUSION_UNET_CROSS_ATTENTION",
            "BERT_LARGE_ENCODER_MATMUL"
        ]
        active_workload = random.choice(workloads)

        # Initialize default fault state
        has_fault = False
        fault_info = None

        # Inject SDC if node is degrading, forced fault is set, or random cosmic ray hit occurs
        should_inject = self.forced_fault_region is not None or (self.is_degrading and (random.random() < self.fault_probability or random.random() < 0.6))
        if should_inject:
            # Pick a random element in C_computed to corrupt
            idx = (random.randint(0, self.matrix_dim[0] - 1), random.randint(0, self.matrix_dim[1] - 1))
            orig_val = float(C_computed[idx])
            
            # Select target bit-flip region
            if self.forced_fault_region:
                region = self.forced_fault_region
                self.forced_fault_region = None
            else:
                region_weights = [0.80, 0.15, 0.05] if self.is_degrading else [0.70, 0.25, 0.05]
                region = random.choices(['mantissa', 'exponent', 'sign'], weights=region_weights)[0]
            
            fault_info = IEEE754FaultInjector.inject_bit_flip(orig_val, target_region=region)
            
            # Add 32-bit binary representation string
            orig_bits = IEEE754FaultInjector.float_to_bits(orig_val)
            corrupt_bits = IEEE754FaultInjector.float_to_bits(fault_info['corrupted_value'])
            fault_info['orig_binary'] = f"{orig_bits:032b}"
            fault_info['corrupt_binary'] = f"{corrupt_bits:032b}"
            fault_info['matrix_cell_index'] = f"Row {idx[0]}, Col {idx[1]}"

            C_computed[idx] = fault_info['corrupted_value']
            has_fault = True

        computed_norm = float(np.linalg.norm(C_computed))
        relative_error = abs(computed_norm - expected_norm) / (expected_norm + 1e-9)

        # Environmental metric simulation (temperature spike or voltage droop correlation)
        temp_offset = random.gauss(8.5, 2.0) if self.is_degrading else random.gauss(0.0, 1.0)
        voltage_droop = random.gauss(-0.04, 0.01) if (has_fault and fault_info and fault_info['fault_region'] == 'exponent') else random.gauss(0.0, 0.005)

        return {
            "node_id": self.node_id,
            "timestamp": time.time(),
            "operation": "MATRIX_DOT_PRODUCT_FP32",
            "active_workload": active_workload,
            "matrix_dim": list(self.matrix_dim),
            "expected_norm": expected_norm,
            "computed_norm": computed_norm,
            "relative_error": relative_error,
            "has_fault_injected": has_fault,
            "fault_details": fault_info,
            "temperature_c": round(self.base_temperature + temp_offset, 2),
            "voltage_v": round(self.base_voltage + voltage_droop, 3),
            "power_w": round(random.gauss(320.0, 15.0), 1)
        }


class FleetSimulator:
    """
    Manages a fleet of 500 simulated GPU compute nodes with dynamic random SDC fault generation.
    """

    def __init__(self, num_nodes: int = 500, num_corrupted_nodes: int = 15, target_records_per_sec: int = 100000):
        self.target_records_per_sec = target_records_per_sec
        self.num_nodes = num_nodes
        self.nodes = {}
        
        # Pick dynamic random nodes to corrupt across the 500-node compute fleet
        corrupted_indices = set(random.sample(range(num_nodes), min(num_corrupted_nodes, num_nodes)))

        for i in range(num_nodes):
            node_id = f"gpu-node-{i+1:03d}"
            is_degraded = i in corrupted_indices
            self.nodes[node_id] = MatrixComputeEngine(node_id, is_degrading=is_degraded)

    def set_node_quarantine(self, node_id: str, quarantined: bool):
        """Enable or disable node output in fleet."""
        if node_id in self.nodes:
            self.nodes[node_id].is_degrading = not quarantined

    def generate_fleet_telemetry(self) -> list:
        """Collect one metric micro-batch aggregating 100,000 records/sec across all fleet nodes."""
        if random.random() < 0.05:
            random_node = random.choice(list(self.nodes.keys()))
            degrading_count = sum(1 for n in self.nodes.values() if n.is_degrading)
            if degrading_count < 30:
                self.nodes[random_node].is_degrading = True

        records_per_node = self.target_records_per_sec // self.num_nodes
        batch = []
        for engine in self.nodes.values():
            rec = engine.run_batch()
            rec["records_count"] = records_per_node
            batch.append(rec)
        return batch
