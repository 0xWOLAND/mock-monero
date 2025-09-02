import pytest
import secrets
from common import setup, keygen, commit
from monero import (
    add_utxo,
    clear_utxos,
    UTXO,
    prove_input,
    verify_tx,
    Tx,
    TxOut,
    range_prove_stub,
)


def test_transaction_flow():
    """Test complete transaction flow."""
    clear_utxos()
    pp = setup()

    # Create initial UTXOs
    owners = [keygen(pp) for _ in range(5)]
    vals = [10 * (i + 1) for i in range(5)]
    blinds = [secrets.randbelow(pp.q - 1) + 1 for _ in range(5)]

    for i, kp in enumerate(owners):
        C = commit(pp, vals[i], blinds[i])
        add_utxo(UTXO(P=kp.P, C=C, v=vals[i], r=blinds[i], sk=kp.sk))

    # Create a transaction spending UTXO 2
    spend_idx = 2
    ring_size = 5
    fee = 2
    ctx = b"TEST-TX"

    # Prove input
    txin, r_pseudo = prove_input(pp, ctx, spend_idx, ring_size)

    # Create outputs
    v_in = vals[spend_idx]  # 30
    v1 = 15
    v2 = v_in - v1 - fee  # 13
    assert v2 >= 0

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

    # Verify transaction
    spent_images = set()
    assert verify_tx(pp, tx, spent_images)

    # Test double spend prevention
    spent_images.add(txin.I)
    assert not verify_tx(pp, tx, spent_images)

    clear_utxos()  # Clean up


def test_transaction_invalid_balance():
    """Test transaction with invalid balance fails."""
    clear_utxos()
    pp = setup()

    # Create one UTXO
    kp = keygen(pp)
    val = 100
    blind = secrets.randbelow(pp.q - 1) + 1
    C = commit(pp, val, blind)
    add_utxo(UTXO(P=kp.P, C=C, v=val, r=blind, sk=kp.sk))

    # Create input
    txin, r_pseudo = prove_input(pp, b"TEST", 0, 1)

    # Create outputs with wrong total (intentionally unbalanced)
    v1 = 50
    v2 = 60  # Total 110 > 100, should fail
    fee = 0

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
        ctx=b"TEST",
    )

    # Should fail due to balance
    assert not verify_tx(pp, tx, set())

    clear_utxos()  # Clean up
