import pytest
from common import setup
from fcmp.tree import build, root, path, hash_leaf, hash_node, Tree


def test_tree_build():
    """Test tree building with various leaf counts."""
    pp = setup()

    # Single leaf
    leaves = [123]
    tree = build(pp, leaves)
    assert isinstance(tree, Tree)
    assert len(tree.layers) == 1
    assert root(tree) == 123

    # Two leaves
    leaves = [123, 456]
    tree = build(pp, leaves)
    assert len(tree.layers) == 2
    expected_root = hash_node(pp, 123, 456)
    assert root(tree) == expected_root

    # Multiple leaves
    leaves = [123, 456, 789, 101112]
    tree = build(pp, leaves)
    assert len(tree.layers) >= 3


def test_tree_empty_leaves():
    """Test that empty leaves raise an error."""
    pp = setup()
    with pytest.raises(ValueError, match="Empty leaves"):
        build(pp, [])


def test_tree_path():
    """Test path extraction from tree."""
    pp = setup()
    leaves = [123, 456, 789]
    tree = build(pp, leaves)

    # Valid path
    leaf, siblings, dirs = path(pp, tree, 0)
    assert leaf == 123
    assert len(siblings) == len(dirs)

    # Path for each leaf
    for i in range(len(leaves)):
        leaf, siblings, dirs = path(pp, tree, i)
        assert leaf == leaves[i]


def test_tree_path_invalid_index():
    """Test path with invalid leaf index."""
    pp = setup()
    leaves = [123, 456]
    tree = build(pp, leaves)

    with pytest.raises(IndexError, match="Bad leaf index"):
        path(pp, tree, -1)

    with pytest.raises(IndexError, match="Bad leaf index"):
        path(pp, tree, 2)


def test_hash_functions():
    """Test hash functions."""
    pp = setup()

    # Hash node
    left, right = 123, 456
    h = hash_node(pp, left, right)
    expected = (pp.g * left + pp.h * right) % pp.q
    assert h == expected

    # Hash leaf
    P, C = 789, 101112
    h = hash_leaf(pp, P, C)
    assert isinstance(h, int)
    assert 0 <= h < pp.q


def test_tree_reconstruction():
    """Test that tree can be reconstructed from paths."""
    pp = setup()
    leaves = [123, 456, 789, 101112]
    tree = build(pp, leaves)
    original_root = root(tree)

    # Verify each leaf can reconstruct the root
    for i, leaf_val in enumerate(leaves):
        leaf, siblings, dirs = path(pp, tree, i)
        assert leaf == leaf_val

        # Reconstruct root from path
        cur = leaf
        for j, (sibling, direction) in enumerate(zip(siblings, dirs)):
            if direction == 0:  # cur is left child
                cur = hash_node(pp, cur, sibling)
            else:  # cur is right child
                cur = hash_node(pp, sibling, cur)

        assert cur == original_root
