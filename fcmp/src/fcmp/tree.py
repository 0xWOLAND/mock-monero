from dataclasses import dataclass
from typing import List, Tuple
from common import CryptoParams, to_bytes, hash_mod


@dataclass
class Tree:
    layers: List[List[int]]


def hash_node(pp: CryptoParams, left: int, right: int) -> int:
    return (pp.g * left + pp.h * right) % pp.q


def hash_leaf(pp: CryptoParams, P: int, C: int) -> int:
    return hash_mod(b"LEAF", to_bytes(P), to_bytes(C), mod=pp.q) or 1


def build(pp: CryptoParams, leaves: List[int]) -> Tree:
    if not leaves:
        raise ValueError("Empty leaves")
    layers = [leaves[:]]
    cur = leaves[:]
    while len(cur) > 1:
        nxt = []
        for i in range(0, len(cur), 2):
            L = cur[i]
            R = (
                cur[i + 1]
                if i + 1 < len(cur)
                else (
                    hash_mod(b"PAD", to_bytes(len(layers)), to_bytes(i), mod=pp.q) or 1
                )
            )
            nxt.append(hash_node(pp, L, R))
        layers.append(nxt)
        cur = nxt
    return Tree(layers)


def root(tree: Tree) -> int:
    return tree.layers[-1][0]


def path(pp: CryptoParams, tree: Tree, idx: int) -> Tuple[int, List[int], List[int]]:
    layers = tree.layers
    if not (0 <= idx < len(layers[0])):
        raise IndexError("Bad leaf index")
    leaf = layers[0][idx]
    siblings, dirs = [], []
    for d in range(len(layers) - 1):
        layer = layers[d]
        is_right = idx % 2
        if is_right:
            sibling = layer[idx - 1]
            dirs.append(1)
        else:
            sibling = (
                layer[idx + 1]
                if idx + 1 < len(layer)
                else (hash_mod(b"PAD", to_bytes(d), to_bytes(idx), mod=pp.q) or 1)
            )
            dirs.append(0)
        siblings.append(sibling)
        idx //= 2
    return leaf, siblings, dirs
