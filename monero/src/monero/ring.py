"""LSAG-style ring signature implementation."""

import secrets
from dataclasses import dataclass
from typing import List
from .group import Params
from .keys import Keypair, Hp
from .utils import i2b, Hs


@dataclass
class RingSig:
    """Ring signature structure."""
    c0: int         # Initial challenge
    s: List[int]    # Response values for all ring members


def ring_chal(pp: Params, ctx: bytes, I: int, ring_P: List[int], 
              ring_C: List[int], L: int, R: int) -> int:
    """Compute ring signature challenge."""
    return Hs(pp.q, b"LSAG", ctx, i2b(I),
              b"".join(i2b(p) for p in ring_P),
              b"".join(i2b(c) for c in ring_C),
              i2b(L), i2b(R))


def ring_prove(pp: Params, ctx: bytes, ring_P: List[int], ring_C: List[int],
               real_idx: int, kp: Keypair, I: int) -> RingSig:
    """Generate a ring signature."""
    n = len(ring_P)
    Hp_list = [Hp(pp, P) for P in ring_P]
    s = [0] * n

    alpha = secrets.randbelow(pp.q - 1) + 1
    L_real = (pp.G * alpha) % pp.q
    R_real = (Hp_list[real_idx] * alpha) % pp.q

    # Start challenge after the real index
    c = [0] * (n + 1)
    c[(real_idx + 1) % n] = ring_chal(pp, ctx, I, ring_P, ring_C, L_real, R_real)

    # Walk the ring
    i = (real_idx + 1) % n
    while i != real_idx:
        s[i] = secrets.randbelow(pp.q - 1) + 1
        L_i = (pp.G * s[i] + c[i] * ring_P[i]) % pp.q
        R_i = (Hp_list[i] * s[i] + c[i] * I) % pp.q
        c[(i + 1) % n] = ring_chal(pp, ctx, I, ring_P, ring_C, L_i, R_i)
        i = (i + 1) % n

    # Close ring at real index
    s[real_idx] = (alpha - c[real_idx] * kp.sk) % pp.q
    return RingSig(c0=c[0], s=s)


def ring_verify(pp: Params, ctx: bytes, ring_P: List[int], ring_C: List[int],
                I: int, sig: RingSig) -> bool:
    """Verify a ring signature."""
    n = len(ring_P)
    Hp_list = [Hp(pp, P) for P in ring_P]
    c = sig.c0
    for i in range(n):
        L_i = (pp.G * sig.s[i] + c * ring_P[i]) % pp.q
        R_i = (Hp_list[i] * sig.s[i] + c * I) % pp.q
        c = ring_chal(pp, ctx, I, ring_P, ring_C, L_i, R_i)
    return c == sig.c0  # must loop back to c0