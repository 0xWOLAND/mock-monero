import hashlib
import secrets
from typing import Optional


def to_bytes(x: int, n: int = 32) -> bytes:
    """Convert integer to bytes with big-endian encoding."""
    return x.to_bytes(n, "big")


def hash_mod(*data: bytes, mod: Optional[int] = None) -> int:
    """Hash data using SHA256 and optionally apply modulo."""
    h = hashlib.sha256()
    for d in data:
        h.update(d)
    val = int.from_bytes(h.digest(), "big")
    return val % mod if mod else val
