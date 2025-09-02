import secrets
from dataclasses import dataclass
from typing import List, Set, Tuple
from common import CryptoParams, Keypair, key_image, commit

from monero.ring import RingSig, ring_prove, ring_verify
from monero.zklink import ZKLink, zklink_prove, zklink_verify
from monero.range_proof import RangeProofStub, verify_range_stub
from monero.utxo import UTXO, GLOBAL


@dataclass
class TxIn:
    """Transaction input."""

    ring_P: List[int]  # Ring of public keys
    ring_C: List[int]  # Ring of commitments
    I: int  # Key image
    sig: RingSig  # Ring signature
    C_pseudo: int  # Pseudo-input commitment
    link_proof: ZKLink  # ZK link proof


@dataclass
class TxOut:
    """Transaction output."""

    P: int  # Recipient public key
    C: int  # Commitment
    rp: RangeProofStub  # Range proof


@dataclass
class Tx:
    """Transaction."""

    ins: List[TxIn]  # Inputs
    outs: List[TxOut]  # Outputs
    fee: int  # Transaction fee
    ctx: bytes  # Context/message


def build_ring_indices(n: int, real_idx: int, ring_size: int) -> List[int]:
    """Build ring indices around a real index."""
    ring_size = max(1, min(ring_size, n))
    # Naive: take a window around real_idx (wrap if needed)
    half = ring_size // 2
    start = (real_idx - half) % n
    idxs = [(start + k) % n for k in range(ring_size)]
    if real_idx not in idxs:
        idxs[-1] = real_idx
    return idxs


def prove_input(
    pp: CryptoParams, ctx: bytes, utxo_index: int, ring_size: int
) -> Tuple[TxIn, int]:
    """
    Create a transaction input by proving ownership of a UTXO.
    Returns the TxIn and the pseudo-input blinding factor.
    """
    u = GLOBAL[utxo_index]
    # Ring selection & materials
    idxs = build_ring_indices(len(GLOBAL), utxo_index, ring_size)
    ring_P = [GLOBAL[i].P for i in idxs]
    ring_C = [GLOBAL[i].C for i in idxs]
    real_pos = idxs.index(utxo_index)

    # Key image for real key
    kp = Keypair(u.sk, u.P)
    I = key_image(pp, kp)

    # Pseudo-input: same amount, fresh blinding r_pseudo
    r_pseudo = secrets.randbelow(pp.q - 1) + 1
    C_pseudo = commit(pp, u.v, r_pseudo)

    # Relation to real input for dummy link
    r_diff = (u.r - r_pseudo) % pp.q  # => C_real - C_pseudo = r_diff * Gc

    # LSAG ring sig
    sig = ring_prove(pp, ctx, ring_P, ring_C, real_pos, kp, I)

    # Dummy ZK link binds pseudo to same ring index
    link = zklink_prove(pp, ctx, ring_P, ring_C, I, C_pseudo, real_pos, r_diff)

    return TxIn(ring_P, ring_C, I, sig, C_pseudo, link), r_pseudo


def verify_tx(pp: CryptoParams, tx: Tx, spent_images: Set[int]) -> bool:
    """Verify a transaction."""
    # 0) Double-spend check
    for tin in tx.ins:
        if tin.I in spent_images:
            return False

    # 1) Ring + link per input
    for tin in tx.ins:
        if not ring_verify(pp, tx.ctx, tin.ring_P, tin.ring_C, tin.I, tin.sig):
            return False
        if not zklink_verify(
            pp, tx.ctx, tin.ring_P, tin.ring_C, tin.I, tin.C_pseudo, tin.link_proof
        ):
            return False

    # 2) Outputs: range-proof stubs
    for tout in tx.outs:
        if not verify_range_stub(tout.C, tout.rp):
            return False

    # 3) Commitment balance using pseudo-inputs:
    # sum(C_pseudo_in) - sum(C_out) - fee*Hc == 0
    sum_in = 0
    for tin in tx.ins:
        sum_in = (sum_in + tin.C_pseudo) % pp.q
    sum_out = 0
    for tout in tx.outs:
        sum_out = (sum_out + tout.C) % pp.q
    bal = (sum_in - sum_out - (pp.Hc * (tx.fee % pp.q)) % pp.q) % pp.q
    if bal != 0:
        return False

    return True
