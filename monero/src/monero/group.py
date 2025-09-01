"""Group parameters and setup for toy additive group Z_q."""

from dataclasses import dataclass


@dataclass
class Params:
    """Cryptographic parameters for the Monero toy implementation."""
    q: int   # Prime modulus
    G: int   # Base for keys
    U: int   # Base for key-image hashing  
    Gc: int  # Base for commitment blinding
    Hc: int  # Base for commitment amount


def setup() -> Params:
    """Initialize cryptographic parameters."""
    q = (1 << 255) - 19
    G, U, Gc, Hc = 5, 11, 13, 17
    for v in (G, U, Gc, Hc):
        assert 0 < v < q
    return Params(q, G, U, Gc, Hc)