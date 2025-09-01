"""Basic cryptographic utilities for Monero implementation."""

import hashlib
from typing import Optional


def i2b(x: int, n: int = 32) -> bytes:
    """Convert integer to bytes with big-endian encoding."""
    return x.to_bytes(n, "big")


def H(*chunks: bytes, q: Optional[int] = None) -> int:
    """Hash data using SHA256 and optionally apply modulo."""
    h = hashlib.sha256()
    for c in chunks:
        h.update(c)
    v = int.from_bytes(h.digest(), "big")
    return v % q if q else v


def Hs(q: int, *chunks: bytes) -> int:
    """Hash data with modulo, ensuring result is never zero."""
    return H(*chunks, q=q) or 1