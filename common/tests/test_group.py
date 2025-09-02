import pytest
from common.group import CryptoParams, setup, commit


def test_setup():
    """Test group parameter setup."""
    params = setup()
    assert isinstance(params, CryptoParams)
    assert params.q > 0
    assert params.G > 0
    assert params.U > 0


def test_crypto_params_validation():
    """Test group parameter validation."""
    # Valid parameters
    params = CryptoParams(q=23, G=5, U=11, Gc=13, Hc=17, g=5, h=7)
    assert params.q == 23

    # Invalid parameters - generator too large
    with pytest.raises(ValueError):
        CryptoParams(q=23, G=25, U=11, Gc=13, Hc=17, g=5, h=7)


def test_commit():
    """Test Pedersen commitment."""
    params = setup()
    c1 = commit(params, 100, 50)
    c2 = commit(params, 100, 50)
    c3 = commit(params, 101, 50)

    assert c1 == c2  # Same inputs should give same commitment
    assert c1 != c3  # Different values should give different commitments
