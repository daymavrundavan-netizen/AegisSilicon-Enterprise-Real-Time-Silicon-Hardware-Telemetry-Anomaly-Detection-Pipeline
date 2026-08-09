"""
AegisSilicon IEEE-754 Floating Point Bit-Flip Fault Injector.
Simulates Silent Data Corruption (SDC) at the physical hardware layer.
"""

import struct
import random
import numpy as np

class IEEE754FaultInjector:
    """
    Injects realistic single-bit flips into IEEE-754 float32 values.
    Supports Sign (bit 31), Exponent (bits 23-30), and Mantissa (bits 0-22) flips.
    """
    
    @staticmethod
    def float_to_bits(f: float) -> int:
        """Pack float32 into 32-bit unsigned int representation."""
        return struct.unpack('>I', struct.pack('>f', float(f)))[0]

    @staticmethod
    def bits_to_float(b: int) -> float:
        """Unpack 32-bit unsigned int back to float32."""
        return struct.unpack('>f', struct.pack('>I', b & 0xFFFFFFFF))[0]

    @classmethod
    def inject_bit_flip(cls, val: float, target_region: str = None, bit_position: int = None) -> dict:
        """
        Inject a single bit-flip into a float32 number.
        
        :param val: Original clean float32 value
        :param target_region: 'sign', 'exponent', or 'mantissa'. If None, randomly chosen.
        :param bit_position: Specific bit 0..31 to flip. If None, chosen within target_region.
        :return: Dict containing original, corrupted, bit position, region, and relative error.
        """
        if target_region is None:
            # Weighted choice matching physical SDC fault distributions in silicon
            target_region = random.choices(['mantissa', 'exponent', 'sign'], weights=[0.70, 0.25, 0.05])[0]

        if bit_position is None:
            if target_region == 'mantissa':
                bit_position = random.randint(0, 22)
            elif target_region == 'exponent':
                bit_position = random.randint(23, 30)
            elif target_region == 'sign':
                bit_position = 31

        original_bits = cls.float_to_bits(val)
        mask = 1 << bit_position
        corrupted_bits = original_bits ^ mask
        corrupted_val = cls.bits_to_float(corrupted_bits)

        # Handle NaN / Inf from exponent flips gracefully
        if np.isnan(corrupted_val) or np.isinf(corrupted_val):
            corrupted_val = val * 1e5 if corrupted_val > 0 else -val * 1e5

        rel_error = abs(corrupted_val - val) / (abs(val) + 1e-9)

        return {
            "original_value": float(val),
            "corrupted_value": float(corrupted_val),
            "bit_position": bit_position,
            "fault_region": target_region,
            "relative_error": float(rel_error),
            "is_silent_corruption": 1e-7 <= rel_error <= 1e-1
        }


if __name__ == "__main__":
    injector = IEEE754FaultInjector()
    clean_val = 250.0000
    
    print("--- IEEE-754 Bit Flip Injections ---")
    for region in ['mantissa', 'exponent', 'sign']:
        res = injector.inject_bit_flip(clean_val, target_region=region)
        print(f"Region: {res['fault_region']:<10} | Bit: {res['bit_position']:<2} | "
              f"Orig: {res['original_value']} -> Corrupted: {res['corrupted_value']:.6f} | "
              f"RelError: {res['relative_error']:.8f} | Silent: {res['is_silent_corruption']}")
