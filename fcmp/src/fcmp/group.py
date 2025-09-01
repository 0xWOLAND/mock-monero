from dataclasses import dataclass


@dataclass
class Params:
    """Cryptographic parameters for the FCMP scheme."""
    q: int  # Prime modulus
    g: int  # Generator for public keys
    h: int  # Generator for tree operations
    U: int  # Generator for key images
    Gc: int # Generator for commitment blinding
    Hc: int # Generator for commitment values


def setup() -> Params:
    """Initialize cryptographic parameters."""
    q = (1 << 255) - 19
    g, h, U = 5, 7, 11
    Gc, Hc = 13, 17
    for v in (g, h, U, Gc, Hc): 
        assert 0 < v < q
    return Params(q=q, g=g, h=h, U=U, Gc=Gc, Hc=Hc)


def commit(pp: Params, value: int, blind: int) -> int:
    """Create a Pedersen commitment to a value with blinding factor."""
    return (pp.Hc * (value % pp.q) + pp.Gc * (blind % pp.q)) % pp.q