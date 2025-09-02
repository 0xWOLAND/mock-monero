import hashlib
from dataclasses import dataclass
from typing import List
from common import CryptoParams, to_bytes


@dataclass
class ZKLink:
    """ZK link proof structure."""

    blob: bytes  # Opaque proof data


def zklink_prove(
    pp: CryptoParams,
    ctx: bytes,
    ring_P: List[int],
    ring_C: List[int],
    I: int,
    C_pseudo: int,
    real_idx: int,
    r_diff: int,
) -> ZKLink:
    """
    Prove that ring_C[real_idx] - C_pseudo == r_diff * Gc.
    Binds to ring transcript & key image I.
    """
    path = b"".join(to_bytes(p) for p in ring_P) + b"".join(to_bytes(c) for c in ring_C)
    binding = hashlib.sha256(
        b"LINK|bind|"
        + ctx
        + to_bytes(I)
        + to_bytes(C_pseudo)
        + path
        + to_bytes(real_idx, 2)
        + to_bytes(r_diff)
    ).digest()
    return ZKLink(
        b"LINKv1|" + binding + b"|" + to_bytes(real_idx, 2) + to_bytes(r_diff)
    )


def zklink_verify(
    pp: CryptoParams,
    ctx: bytes,
    ring_P: List[int],
    ring_C: List[int],
    I: int,
    C_pseudo: int,
    prf: ZKLink,
) -> bool:
    """Verify ZK link proof."""
    if not prf.blob.startswith(b"LINKv1|"):
        return False
    rest = prf.blob[len(b"LINKv1|") :]
    if len(rest) < 32 + 1 + 2 + 32:  # binding + '|' + j (2 bytes) + r_diff (32 bytes)
        return False
    binding = rest[:32]
    if rest[32:33] != b"|":
        return False
    tail = rest[33:]
    j = int.from_bytes(tail[:2], "big")
    r_diff = int.from_bytes(tail[2:34], "big")
    if not (0 <= j < len(ring_C)):
        return False
    lhs = (ring_C[j] - C_pseudo) % pp.q
    rhs = (pp.Gc * r_diff) % pp.q
    if lhs != rhs:
        return False
    path = b"".join(to_bytes(p) for p in ring_P) + b"".join(to_bytes(c) for c in ring_C)
    exp = hashlib.sha256(
        b"LINK|bind|"
        + ctx
        + to_bytes(I)
        + to_bytes(C_pseudo)
        + path
        + to_bytes(j, 2)
        + to_bytes(r_diff)
    ).digest()
    return binding == exp
