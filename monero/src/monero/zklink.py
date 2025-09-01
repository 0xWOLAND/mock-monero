"""Dummy ZK link proof to bind pseudo-input to ring index."""

import hashlib
from dataclasses import dataclass
from typing import List
from .group import Params
from .utils import i2b


@dataclass
class ZKLink:
    """ZK link proof structure."""
    blob: bytes  # Opaque proof data


def zklink_prove(pp: Params, ctx: bytes, ring_P: List[int], ring_C: List[int],
                 I: int, C_pseudo: int, real_idx: int, r_diff: int) -> ZKLink:
    """
    Prove that ring_C[real_idx] - C_pseudo == r_diff * Gc.
    Binds to ring transcript & key image I.
    """
    path = b"".join(i2b(p) for p in ring_P) + b"".join(i2b(c) for c in ring_C)
    binding = hashlib.sha256(
        b"LINK|bind|" + ctx + i2b(I) + i2b(C_pseudo) + path + i2b(real_idx, 2) + i2b(r_diff)
    ).digest()
    return ZKLink(b"LINKv1|" + binding + b"|" + i2b(real_idx, 2) + i2b(r_diff))


def zklink_verify(pp: Params, ctx: bytes, ring_P: List[int], ring_C: List[int],
                  I: int, C_pseudo: int, prf: ZKLink) -> bool:
    """Verify ZK link proof."""
    if not prf.blob.startswith(b"LINKv1|"):
        return False
    rest = prf.blob[len(b"LINKv1|"):]
    binding, _, tail = rest.partition(b"|")
    j = int.from_bytes(tail[:2], "big")
    r_diff = int.from_bytes(tail[2:34], "big")
    if not (0 <= j < len(ring_C)):
        return False
    lhs = (ring_C[j] - C_pseudo) % pp.q
    rhs = (pp.Gc * r_diff) % pp.q
    if lhs != rhs:
        return False
    path = b"".join(i2b(p) for p in ring_P) + b"".join(i2b(c) for c in ring_C)
    exp = hashlib.sha256(
        b"LINK|bind|" + ctx + i2b(I) + i2b(C_pseudo) + path + i2b(j, 2) + i2b(r_diff)
    ).digest()
    return binding == exp