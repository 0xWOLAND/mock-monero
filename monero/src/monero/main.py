import secrets
from typing import Set
from common import setup, keygen, commit
from monero.transaction import Tx, TxOut, prove_input, verify_tx
from monero.range_proof import range_prove_stub
from monero.utxo import UTXO, add_utxo


def main() -> None:
    pp = setup()

    # Wallets / initial UTXOs
    owners = [keygen(pp) for _ in range(8)]
    vals = [10 * (i + 1) for i in range(8)]
    blinds = [secrets.randbelow(pp.q - 1) + 1 for _ in range(8)]
    for i, kp in enumerate(owners):
        C = commit(pp, vals[i], blinds[i])
        add_utxo(UTXO(P=kp.P, C=C, v=vals[i], r=blinds[i], sk=kp.sk))

    # Spend one input with a ring of size 8, create two outputs
    spend_idx = 3
    ring_size = 8
    fee = 3
    ctx = b"MONERO-RINGCT-TOY"

    # Prove input + get r_pseudo so we can balance output blindings
    txin, r_pseudo = prove_input(pp, ctx, spend_idx, ring_size)

    # Choose output amounts (must satisfy v1 + v2 + fee = v_in)
    from .utxo import GLOBAL

    v_in = GLOBAL[spend_idx].v
    v1 = 17
    v2 = v_in - v1 - fee
    assert v2 >= 0

    # Choose output blindings so r1 + r2 == r_pseudo (mod q)
    r1 = secrets.randbelow(pp.q - 1) + 1
    r2 = (r_pseudo - r1) % pp.q

    dest1, dest2 = keygen(pp), keygen(pp)
    C1 = commit(pp, v1, r1)
    C2 = commit(pp, v2, r2)

    tx = Tx(
        ins=[txin],
        outs=[
            TxOut(dest1.P, C1, range_prove_stub(v1)),
            TxOut(dest2.P, C2, range_prove_stub(v2)),
        ],
        fee=fee,
        ctx=ctx,
    )

    # Verify + apply
    spent_images: Set[int] = set()
    ok = verify_tx(pp, tx, spent_images)
    print("TX verifies?", ok)

    if ok:
        spent_images.add(txin.I)
        # append outputs to GLOBAL UTXO (for completeness of the toy)
        add_utxo(UTXO(P=dest1.P, C=C1, v=v1, r=r1, sk=0))
        add_utxo(UTXO(P=dest2.P, C=C2, v=v2, r=r2, sk=0))

    # Double-spend attempt (same tx again)
    ok2 = verify_tx(pp, tx, spent_images)
    print("Double-spend blocked?", not ok2)


if __name__ == "__main__":
    main()
