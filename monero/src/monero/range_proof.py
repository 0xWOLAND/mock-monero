"""Range proof stub implementation."""

from dataclasses import dataclass


@dataclass
class RangeProofStub:
    """Stub range proof structure."""
    blob: bytes


def range_prove_stub(v: int) -> RangeProofStub:
    """Generate a stub range proof (always succeeds)."""
    return RangeProofStub(b"OK")


def verify_range_stub(C: int, rp: RangeProofStub) -> bool:
    """Verify stub range proof (always returns True)."""
    return True