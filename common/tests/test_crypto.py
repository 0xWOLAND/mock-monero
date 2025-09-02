import pytest
from common.crypto import hash_mod, to_bytes


def test_hash_mod_consistency():
    """Test that hash function produces consistent results."""
    data = b"test"
    result1 = hash_mod(data, mod=1000)
    result2 = hash_mod(data, mod=1000)
    assert result1 == result2


def test_hash_mod_different_inputs():
    """Test that different inputs produce different hashes."""
    result1 = hash_mod(b"test1", mod=1000)
    result2 = hash_mod(b"test2", mod=1000)
    assert result1 != result2


def test_to_bytes():
    """Test integer to bytes conversion."""
    result = to_bytes(123, 4)
    assert result == b"\x00\x00\x00{"
    assert len(result) == 4
