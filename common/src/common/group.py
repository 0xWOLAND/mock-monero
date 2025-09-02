from dataclasses import dataclass
from typing import Tuple


@dataclass
class CryptoParams:
    q: int
    G: int
    U: int
    Gc: int
    Hc: int
    g: int
    h: int

    def __post_init__(self):
        generators = [self.G, self.U, self.Gc, self.Hc, self.g, self.h]
        if any(v <= 0 or v >= self.q for v in generators):
            raise ValueError("All generators must be in range (0, q)")


def setup() -> CryptoParams:
    q = (1 << 255) - 19
    G, U, Gc, Hc = 5, 11, 13, 17
    g, h = 5, 7

    return CryptoParams(q=q, G=G, U=U, Gc=Gc, Hc=Hc, g=g, h=h)


def commit(pp: CryptoParams, value: int, blind: int) -> int:
    return (pp.Hc * (value % pp.q) + pp.Gc * (blind % pp.q)) % pp.q
