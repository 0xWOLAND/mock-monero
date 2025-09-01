import secrets
from dataclasses import dataclass
from .group import Params
from .utils import to_bytes, hash_safe


@dataclass
class Key:
    sk: int
    P: int
    I: int


@dataclass
class SpendProof:
    A1: int
    A2: int
    z: int


def gen_key(pp: Params) -> Key:
    sk = secrets.randbelow(pp.q - 1) + 1
    return Key(sk=sk, P=(pp.g * sk) % pp.q, I=(pp.U * sk) % pp.q)


def prove_spend(pp: Params, key: Key, root: int, ctx: bytes = b"") -> SpendProof:
    r = secrets.randbelow(pp.q - 1) + 1
    A1 = (pp.g * r) % pp.q
    A2 = (pp.U * r) % pp.q
    e = hash_safe(pp.q, b"DL-EQ", ctx, to_bytes(root), to_bytes(key.P), 
                  to_bytes(key.I), to_bytes(A1), to_bytes(A2))
    z = (r + e * key.sk) % pp.q
    return SpendProof(A1, A2, z)


def verify_spend(pp: Params, P: int, I: int, root: int, proof: SpendProof, ctx: bytes = b"") -> bool:
    e = hash_safe(pp.q, b"DL-EQ", ctx, to_bytes(root), to_bytes(P), 
                  to_bytes(I), to_bytes(proof.A1), to_bytes(proof.A2))
    return (pp.g * proof.z) % pp.q == (proof.A1 + e * P) % pp.q and \
           (pp.U * proof.z) % pp.q == (proof.A2 + e * I) % pp.q