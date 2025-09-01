#!/usr/bin/env python3
import secrets
from .group import setup, commit
from .keys import gen_key
from .tree import root
from .tx import TxOut, Tx, prove_range
from .verify import add_utxo, build_tree, prove_input, verify_tx, UTXO_C


def main():
    pp = setup()

    N = 8
    owners = [gen_key(pp) for _ in range(N)]
    values = [10 * (i + 1) for i in range(N)]
    blinds = [secrets.randbelow(pp.q - 1) + 1 for _ in range(N)]
    
    indices = []
    for i in range(N):
        C = commit(pp, values[i], blinds[i])
        indices.append(add_utxo(pp, owners[i].P, C))

    tree = build_tree(pp)
    root0 = root(tree)

    i = 3
    key = owners[i]
    C_in = UTXO_C[indices[i]]
    fee = 3

    v1 = 17
    v2 = values[i] - v1 - fee
    assert v2 >= 0
    
    r_in = blinds[i]
    r1 = secrets.randbelow(pp.q - 1) + 1
    r2 = (r_in - r1) % pp.q
    
    dest1, dest2 = gen_key(pp), gen_key(pp)
    C_out1 = commit(pp, v1, r1)
    C_out2 = commit(pp, v2, r2)

    txin = prove_input(pp, tree, key, C_in, indices[i], ctx=b"FCMP-ZK-TX")
    txout1 = TxOut(dest1.P, C_out1, prove_range(v1))
    txout2 = TxOut(dest2.P, C_out2, prove_range(v2))
    tx = Tx([txin], [txout1, txout2], fee, ctx=b"FCMP-ZK-TX")

    spent_tags: set[int] = set()
    ok = verify_tx(pp, tx, tree, spent_tags)
    print("TX verifies?", ok)

    if ok:
        for txin in tx.inputs:
            spent_tags.add(txin.I)
        add_utxo(pp, txout1.P, txout1.C)
        add_utxo(pp, txout2.P, txout2.C)

    tree2 = build_tree(pp)
    print("Root before:", root0)
    print("Root after :", root(tree2))

    ok2 = verify_tx(pp, tx, tree2, spent_tags)
    print("Double-spend blocked?", not ok2)


if __name__ == "__main__":
    main()