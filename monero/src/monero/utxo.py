from dataclasses import dataclass
from typing import List


@dataclass
class UTXO:
    """Unspent Transaction Output."""

    P: int  # Public key
    C: int  # Commitment
    v: int  # Value (stored for demo)
    r: int  # Blinding factor (stored for demo)
    sk: int  # Secret key (stored for demo wallet)


# Global UTXO set (for demonstration purposes)
GLOBAL: List[UTXO] = []


def add_utxo(utxo: UTXO) -> int:
    """Add a UTXO to the global set and return its index."""
    GLOBAL.append(utxo)
    return len(GLOBAL) - 1


def get_utxo(index: int) -> UTXO:
    """Get a UTXO by index."""
    return GLOBAL[index]


def get_utxo_count() -> int:
    """Get the number of UTXOs in the global set."""
    return len(GLOBAL)


def clear_utxos() -> None:
    """Clear all UTXOs (for testing)."""
    GLOBAL.clear()
