from dataclasses import dataclass
from typing import List, Tuple
from .group import Params
from .utils import to_bytes, hash_safe


@dataclass
class Tree:
    layers: List[List[int]]


def hash_node(pp: Params, left: int, right: int) -> int:
    return (pp.g * left + pp.h * right) % pp.q


def hash_leaf(pp: Params, P: int, C: int) -> int:
    return hash_safe(pp.q, b"LEAF", to_bytes(P), to_bytes(C))


def build(pp: Params, leaves: List[int]) -> Tree:
    if not leaves: 
        raise ValueError("Empty leaves")
    layers = [leaves[:]]
    cur = leaves[:]
    while len(cur) > 1:
        nxt = []
        for i in range(0, len(cur), 2):
            L = cur[i]
            R = cur[i + 1] if i + 1 < len(cur) else hash_safe(pp.q, b"PAD", to_bytes(len(layers)), to_bytes(i))
            nxt.append(hash_node(pp, L, R))
        layers.append(nxt)
        cur = nxt
    return Tree(layers)


def root(tree: Tree) -> int:
    return tree.layers[-1][0]


def path(pp: Params, tree: Tree, idx: int) -> Tuple[int, List[int], List[int]]:
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
            sibling = layer[idx + 1] if idx + 1 < len(layer) else hash_safe(pp.q, b"PAD", to_bytes(d), to_bytes(idx))
            dirs.append(0)
        siblings.append(sibling)
        idx //= 2
    return leaf, siblings, dirs