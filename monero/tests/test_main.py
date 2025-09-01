"""Test the main demo functionality."""

import pytest
from monero import setup, keygen, commit, add_utxo, UTXO, clear_utxos


def test_setup():
    """Test parameter setup."""
    pp = setup()
    assert pp.q == (1 << 255) - 19
    assert all(0 < v < pp.q for v in [pp.G, pp.U, pp.Gc, pp.Hc])


def test_keygen():
    """Test key generation."""
    pp = setup()
    kp = keygen(pp)
    assert 0 < kp.sk < pp.q
    assert kp.P == (pp.G * kp.sk) % pp.q


def test_commit():
    """Test commitments."""
    pp = setup()
    val, blind = 100, 42
    c = commit(pp, val, blind)
    assert c == (pp.Hc * val + pp.Gc * blind) % pp.q


def test_utxo_management():
    """Test UTXO operations."""
    clear_utxos()
    pp = setup()
    kp = keygen(pp)
    val, blind = 50, 123
    c = commit(pp, val, blind)
    
    utxo = UTXO(P=kp.P, C=c, v=val, r=blind, sk=kp.sk)
    idx = add_utxo(utxo)
    assert idx == 0
    
    clear_utxos()  # Clean up