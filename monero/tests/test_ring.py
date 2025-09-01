"""Test ring signature operations."""

import pytest
from monero.group import setup
from monero.keys import keygen, key_image
from monero.commitments import commit
from monero.ring import ring_prove, ring_verify
import secrets


def test_ring_signature():
    """Test ring signature creation and verification."""
    pp = setup()
    
    # Create a ring of 5 keys
    ring_keys = [keygen(pp) for _ in range(5)]
    ring_P = [kp.P for kp in ring_keys]
    
    # Create commitments for the ring
    values = [10, 20, 30, 40, 50]
    blinds = [secrets.randbelow(pp.q - 1) + 1 for _ in range(5)]
    ring_C = [commit(pp, values[i], blinds[i]) for i in range(5)]
    
    # Sign with the 2nd key (index 1)
    real_idx = 1
    real_kp = ring_keys[real_idx]
    I = key_image(pp, real_kp)
    ctx = b"test-context"
    
    # Create ring signature
    sig = ring_prove(pp, ctx, ring_P, ring_C, real_idx, real_kp, I)
    
    # Verify signature
    assert ring_verify(pp, ctx, ring_P, ring_C, I, sig)


def test_ring_signature_wrong_context():
    """Test ring signature fails with wrong context."""
    pp = setup()
    
    ring_keys = [keygen(pp) for _ in range(3)]
    ring_P = [kp.P for kp in ring_keys]
    ring_C = [commit(pp, 10, secrets.randbelow(pp.q - 1) + 1) for _ in range(3)]
    
    real_idx = 0
    real_kp = ring_keys[real_idx]
    I = key_image(pp, real_kp)
    
    sig = ring_prove(pp, b"context1", ring_P, ring_C, real_idx, real_kp, I)
    
    # Should fail with different context
    assert not ring_verify(pp, b"context2", ring_P, ring_C, I, sig)


def test_ring_signature_wrong_key_image():
    """Test ring signature fails with wrong key image."""
    pp = setup()
    
    ring_keys = [keygen(pp) for _ in range(3)]
    ring_P = [kp.P for kp in ring_keys]
    ring_C = [commit(pp, 10, secrets.randbelow(pp.q - 1) + 1) for _ in range(3)]
    
    real_idx = 0
    real_kp = ring_keys[real_idx]
    I = key_image(pp, real_kp)
    ctx = b"test"
    
    sig = ring_prove(pp, ctx, ring_P, ring_C, real_idx, real_kp, I)
    
    # Create a different key image
    wrong_kp = keygen(pp)
    wrong_I = key_image(pp, wrong_kp)
    
    # Should fail with wrong key image
    assert not ring_verify(pp, ctx, ring_P, ring_C, wrong_I, sig)