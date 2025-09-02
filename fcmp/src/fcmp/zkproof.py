import hashlib
from dataclasses import dataclass
from typing import List, Tuple
from common import CryptoParams, to_bytes
from fcmp.tree import Tree, root, path, hash_leaf, hash_node


@dataclass
class ZKProof:
    blob: bytes


def _pack(
    pp: CryptoParams,
    root_val: int,
    leaf: int,
    siblings: List[int],
    dirs: List[int],
    ctx: bytes,
) -> bytes:
    depth = len(siblings)
    sib_data = b"".join(to_bytes(s) for s in siblings)
    dir_data = bytes(dirs)
    path_data = depth.to_bytes(2, "big") + sib_data + dir_data
    binding = hashlib.sha256(
        b"ZK|bind|"
        + ctx
        + to_bytes(root_val)
        + to_bytes(leaf)
        + hashlib.sha256(path_data).digest()
    ).digest()
    return b"ZKv1|" + binding + b"|" + path_data


def _unpack(blob: bytes) -> Tuple[bytes, bytes]:
    assert blob.startswith(b"ZKv1|")
    rest = blob[len(b"ZKv1|") :]
    binding, sep, path_data = rest.partition(b"|")
    return binding, path_data


def prove(
    pp: CryptoParams, tree: Tree, P: int, C: int, idx: int, ctx: bytes
) -> ZKProof:
    root_val = root(tree)
    leaf, siblings, dirs = path(pp, tree, idx)
    assert leaf == hash_leaf(pp, P, C), "Leaf mismatch"
    blob = _pack(pp, root_val, leaf, siblings, dirs, ctx)
    return ZKProof(blob)


def verify(
    pp: CryptoParams, root_val: int, P: int, C: int, proof: ZKProof, ctx: bytes
) -> bool:
    leaf = hash_leaf(pp, P, C)
    binding, path_data = _unpack(proof.blob)

    assert len(path_data) >= 2
    depth = int.from_bytes(path_data[:2], "big")
    body = path_data[2:]
    sib_len = 32 * depth
    assert len(body) == sib_len + depth

    sib_data = body[:sib_len]
    dir_data = body[sib_len:]
    siblings = [
        int.from_bytes(sib_data[i * 32 : (i + 1) * 32], "big") for i in range(depth)
    ]
    dirs = list(dir_data)

    cur = leaf
    for i in range(depth):
        if dirs[i] == 0:
            cur = hash_node(pp, cur, siblings[i])
        else:
            cur = hash_node(pp, siblings[i], cur)

    exp_binding = hashlib.sha256(
        b"ZK|bind|"
        + ctx
        + to_bytes(root_val)
        + to_bytes(leaf)
        + hashlib.sha256(path_data).digest()
    ).digest()
    return (binding == exp_binding) and (cur == root_val)
