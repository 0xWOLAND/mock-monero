"""Test key operations."""

import pytest
from monero.group import setup
from monero.keys import keygen, key_image, Keypair


def test_keygen():
    """Test key generation."""
    pp = setup()
    kp = keygen(pp)
    
    assert isinstance(kp, Keypair)
    assert 0 < kp.sk < pp.q
    assert kp.P == (pp.G * kp.sk) % pp.q


def test_key_uniqueness():
    """Test that keys are unique."""
    pp = setup()
    keys = [keygen(pp) for _ in range(10)]
    
    secret_keys = [k.sk for k in keys]
    assert len(set(secret_keys)) == len(secret_keys)
    
    public_keys = [k.P for k in keys]
    assert len(set(public_keys)) == len(public_keys)


def test_key_image():
    """Test key image generation."""
    pp = setup()
    kp = keygen(pp)
    I = key_image(pp, kp)
    
    assert isinstance(I, int)
    assert 0 <= I < pp.q
    
    # Same key should produce same image
    I2 = key_image(pp, kp)
    assert I == I2
    
    # Different keys should produce different images
    kp2 = keygen(pp)
    I3 = key_image(pp, kp2)
    assert I != I3