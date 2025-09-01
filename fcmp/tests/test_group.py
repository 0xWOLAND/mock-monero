import pytest
from fcmp.group import setup, commit, Params


def test_setup():
    """Test parameter setup."""
    pp = setup()
    assert isinstance(pp, Params)
    assert pp.q == (1 << 255) - 19
    assert all(0 < v < pp.q for v in [pp.g, pp.h, pp.U, pp.Gc, pp.Hc])


def test_commit():
    """Test Pedersen commitment."""
    pp = setup()
    
    # Basic commitment
    val, blind = 100, 42
    c = commit(pp, val, blind)
    expected = (pp.Hc * val + pp.Gc * blind) % pp.q
    assert c == expected
    
    # Zero value commitment
    c_zero = commit(pp, 0, blind)
    assert c_zero == (pp.Gc * blind) % pp.q
    
    # Zero blind commitment
    c_no_blind = commit(pp, val, 0)
    assert c_no_blind == (pp.Hc * val) % pp.q


def test_commit_homomorphism():
    """Test commitment homomorphism property."""
    pp = setup()
    
    val1, val2 = 10, 20
    blind1, blind2 = 5, 7
    
    c1 = commit(pp, val1, blind1)
    c2 = commit(pp, val2, blind2)
    c_sum = commit(pp, val1 + val2, blind1 + blind2)
    
    assert (c1 + c2) % pp.q == c_sum