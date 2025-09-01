"""Pedersen commitment operations."""

from .group import Params


def commit(pp: Params, v: int, r: int) -> int:
    """Create a Pedersen commitment to value v with blinding factor r."""
    return (pp.Hc * (v % pp.q) + pp.Gc * (r % pp.q)) % pp.q