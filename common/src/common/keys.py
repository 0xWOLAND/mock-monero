from dataclasses import dataclass
from common.group import CryptoParams
import secrets
from common.crypto import hash_mod, to_bytes


@dataclass
class Keypair:
    sk: int
    P: int


@dataclass
class FCMPKey:
    sk: int
    P: int
    I: int


@dataclass
class SpendProof:
    A1: int
    A2: int
    z: int


def keygen(pp: CryptoParams) -> Keypair:
    x = secrets.randbelow(pp.q - 1) + 1
    return Keypair(x, (pp.G * x) % pp.q)


def gen_key(pp: CryptoParams) -> FCMPKey:
    sk = secrets.randbelow(pp.q - 1) + 1
    return FCMPKey(sk=sk, P=(pp.g * sk) % pp.q, I=(pp.U * sk) % pp.q)


def Hp(pp: CryptoParams, P: int) -> int:
    return ((hash_mod(b"KI", to_bytes(P), mod=pp.q) or 1) * pp.U) % pp.q


def key_image(pp: CryptoParams, kp: Keypair) -> int:
    return (Hp(pp, kp.P) * kp.sk) % pp.q


def prove_spend(
    pp: CryptoParams, key: FCMPKey, root: int, ctx: bytes = b""
) -> SpendProof:
    r = secrets.randbelow(pp.q - 1) + 1
    A1 = (pp.g * r) % pp.q
    A2 = (pp.U * r) % pp.q
    e = (
        hash_mod(
            b"DL-EQ",
            ctx,
            to_bytes(root),
            to_bytes(key.P),
            to_bytes(key.I),
            to_bytes(A1),
            to_bytes(A2),
            mod=pp.q,
        )
        or 1
    )
    z = (r + e * key.sk) % pp.q
    return SpendProof(A1, A2, z)


def verify_spend(
    pp: CryptoParams, P: int, I: int, root: int, proof: SpendProof, ctx: bytes = b""
) -> bool:
    e = (
        hash_mod(
            b"DL-EQ",
            ctx,
            to_bytes(root),
            to_bytes(P),
            to_bytes(I),
            to_bytes(proof.A1),
            to_bytes(proof.A2),
            mod=pp.q,
        )
        or 1
    )
    return (pp.g * proof.z) % pp.q == (proof.A1 + e * P) % pp.q and (
        pp.U * proof.z
    ) % pp.q == (proof.A2 + e * I) % pp.q
