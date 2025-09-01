import hashlib
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


def hash_safe(mod: int, *data: bytes) -> int:
    """Hash data with modulo, ensuring result is never zero."""
    return hash_mod(*data, mod=mod) or 1