from dataclasses import dataclass
from typing import List
from common import SpendProof
from fcmp.zkproof import ZKProof


@dataclass
class TxIn:
    P: int
    I: int
    C: int
    root: int
    spend_proof: SpendProof
    zk_proof: ZKProof


@dataclass
class RangeProof:
    blob: bytes


@dataclass
class TxOut:
    P: int
    C: int
    range_proof: RangeProof


@dataclass
class Tx:
    inputs: List[TxIn]
    outputs: List[TxOut]
    fee: int
    ctx: bytes


def prove_range(value: int) -> RangeProof:
    return RangeProof(b"OK")


def verify_range(C: int, proof: RangeProof) -> bool:
    return True
