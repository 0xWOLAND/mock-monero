"""Key generation and key image operations."""

import secrets
from dataclasses import dataclass
from .group import Params
from .utils import i2b, Hs


@dataclass
class Keypair:
    """A cryptographic keypair with secret and public key."""
    sk: int  # Secret key
    P: int   # Public key


def keygen(pp: Params) -> Keypair:
    """Generate a random keypair."""
    x = secrets.randbelow(pp.q - 1) + 1
    return Keypair(x, (pp.G * x) % pp.q)


def Hp(pp: Params, P: int) -> int:
    """Per-key hash-to-point: Hp(P) = Hs(...)*U"""
    return (Hs(pp.q, b"KI", i2b(P)) * pp.U) % pp.q


def key_image(pp: Params, kp: Keypair) -> int:
    """Generate key image for linkability."""
    return (Hp(pp, kp.P) * kp.sk) % pp.q