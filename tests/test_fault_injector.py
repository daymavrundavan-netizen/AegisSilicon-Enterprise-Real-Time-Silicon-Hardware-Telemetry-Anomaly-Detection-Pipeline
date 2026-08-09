"""
Unit Tests for IEEE-754 Bit Flip Fault Injector.
"""

from simulator.fault_injector import IEEE754FaultInjector

def test_mantissa_bit_flip():
    injector = IEEE754FaultInjector()
    clean_val = 250.0000
    res = injector.inject_bit_flip(clean_val, target_region='mantissa', bit_position=10)
    
    assert res['original_value'] == 250.0
    assert res['bit_position'] == 10
    assert res['fault_region'] == 'mantissa'
    assert res['corrupted_value'] != clean_val
    assert 0.0 < res['relative_error'] < 1.0

def test_exponent_bit_flip():
    injector = IEEE754FaultInjector()
    clean_val = 100.0
    res = injector.inject_bit_flip(clean_val, target_region='exponent', bit_position=25)
    
    assert res['fault_region'] == 'exponent'
    assert res['corrupted_value'] != clean_val
    assert res['relative_error'] > 0.01

def test_sign_bit_flip():
    injector = IEEE754FaultInjector()
    clean_val = 50.0
    res = injector.inject_bit_flip(clean_val, target_region='sign', bit_position=31)
    
    assert res['fault_region'] == 'sign'
    assert res['corrupted_value'] == -50.0
    assert abs(res['relative_error'] - 2.0) < 1e-4

if __name__ == "__main__":
    test_mantissa_bit_flip()
    test_exponent_bit_flip()
    test_sign_bit_flip()
    print("ALL FAULT INJECTOR TESTS PASSED.")
