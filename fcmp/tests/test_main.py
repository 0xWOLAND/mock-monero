import pytest
from fcmp import setup, commit, gen_key, add_utxo, build_tree, verify_tx


def test_setup():
    pp = setup()
    assert pp.q == (1 << 255) - 19
    assert all(0 < v < pp.q for v in [pp.g, pp.h, pp.U, pp.Gc, pp.Hc])


def test_key_gen():
    pp = setup()
    key = gen_key(pp)
    assert 0 < key.sk < pp.q
    assert key.P == (pp.g * key.sk) % pp.q
    assert key.I == (pp.U * key.sk) % pp.q


def test_commit():
    pp = setup()
    val, blind = 100, 42
    c = commit(pp, val, blind)
    assert c == (pp.Hc * val + pp.Gc * blind) % pp.q


def test_tree_build():
    pp = setup()
    key = gen_key(pp)
    c = commit(pp, 50, 123)
    idx = add_utxo(pp, key.P, c)
    tree = build_tree(pp)
    assert len(tree.layers) > 0
    assert idx == 0