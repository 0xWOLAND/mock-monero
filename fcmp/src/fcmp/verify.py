from common import CryptoParams, FCMPKey, prove_spend, verify_spend
from fcmp.tree import Tree, root, hash_leaf
from fcmp.zkproof import prove as zk_prove, verify as zk_verify
from fcmp.tx import TxIn, Tx, verify_range


UTXO_P = []
UTXO_C = []
UTXO_LEAVES = []


def add_utxo(pp: CryptoParams, P: int, C: int) -> int:
    leaf = hash_leaf(pp, P, C)
    UTXO_P.append(P)
    UTXO_C.append(C)
    UTXO_LEAVES.append(leaf)
    return len(UTXO_LEAVES) - 1


def build_tree(pp: CryptoParams) -> Tree:
    from fcmp.tree import build

    return build(pp, UTXO_LEAVES)


def prove_input(
    pp: CryptoParams, tree: Tree, key: FCMPKey, C: int, idx: int, ctx: bytes
) -> TxIn:
    root_val = root(tree)
    spend_proof = prove_spend(pp, key, root_val, ctx)
    zk_proof = zk_prove(pp, tree, key.P, C, idx, ctx)
    return TxIn(
        P=key.P, I=key.I, C=C, root=root_val, spend_proof=spend_proof, zk_proof=zk_proof
    )


def verify_input(pp: CryptoParams, txin: TxIn, current_root: int, ctx: bytes) -> bool:
    if txin.root != current_root:
        return False
    if not verify_spend(pp, txin.P, txin.I, txin.root, txin.spend_proof, ctx):
        return False
    if not zk_verify(pp, txin.root, txin.P, txin.C, txin.zk_proof, ctx):
        return False
    return True


def verify_tx(pp: CryptoParams, tx: Tx, tree: Tree, spent_tags: set[int]) -> bool:
    root_val = root(tree)

    for txin in tx.inputs:
        if txin.I in spent_tags:
            return False

    for txin in tx.inputs:
        if not verify_input(pp, txin, root_val, tx.ctx):
            return False

    for txout in tx.outputs:
        if not verify_range(txout.C, txout.range_proof):
            return False

    sum_in = sum(txin.C for txin in tx.inputs) % pp.q
    sum_out = sum(txout.C for txout in tx.outputs) % pp.q
    balance = (sum_in - sum_out - (pp.Hc * (tx.fee % pp.q)) % pp.q) % pp.q
    return balance == 0
