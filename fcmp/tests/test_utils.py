import pytest
from fcmp.utils import to_bytes, hash_mod, hash_safe


def test_to_bytes():
    """Test integer to bytes conversion."""
    # Basic conversion
    assert to_bytes(0) == b'\x00' * 32
    assert to_bytes(255) == b'\x00' * 31 + b'\xff'
    assert to_bytes(256) == b'\x00' * 30 + b'\x01\x00'
    
    # Custom length
    assert to_bytes(255, 1) == b'\xff'
    assert to_bytes(255, 4) == b'\x00\x00\x00\xff'


def test_hash_mod():
    """Test hash with modulo."""
    data = b"test data"
    
    # Without modulo
    h1 = hash_mod(data)
    assert isinstance(h1, int)
    assert h1 > 0
    
    # With modulo
    mod = 1000
    h2 = hash_mod(data, mod=mod)
    assert 0 <= h2 < mod
    
    # Same input should give same output
    assert hash_mod(data) == hash_mod(data)
    assert hash_mod(data, mod=mod) == hash_mod(data, mod=mod)
    
    # Different inputs should give different outputs (with high probability)
    h3 = hash_mod(b"different data")
    assert h1 != h3


def test_hash_safe():
    """Test hash_safe (never returns zero)."""
    # Multiple test cases to ensure we never get zero
    for i in range(100):
        data = f"test_{i}".encode()
        mod = 1000
        h = hash_safe(mod, data)
        assert 1 <= h < mod
    
    # Specific test case
    data = b"test"
    mod = 123
    h = hash_safe(mod, data)
    assert 1 <= h < mod


def test_hash_consistency():
    """Test hash function consistency."""
    data1 = b"hello"
    data2 = b"world"
    mod = 12345
    
    # Multiple arguments should be consistent
    h1 = hash_mod(data1, data2, mod=mod)
    h2 = hash_mod(data1, data2, mod=mod)
    assert h1 == h2
    
    # Order matters
    h3 = hash_mod(data2, data1, mod=mod)
    assert h1 != h3  # Should be different with high probability
    
    # Safe version consistency
    hs1 = hash_safe(mod, data1, data2)
    hs2 = hash_safe(mod, data1, data2)
    assert hs1 == hs2