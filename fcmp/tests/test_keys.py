import pytest
from fcmp.group import setup
from fcmp.keys import gen_key, prove_spend, verify_spend, Key


def test_key_generation():
    """Test key generation."""
    pp = setup()
    key = gen_key(pp)
    
    assert isinstance(key, Key)
    assert 0 < key.sk < pp.q
    assert key.P == (pp.g * key.sk) % pp.q
    assert key.I == (pp.U * key.sk) % pp.q


def test_key_uniqueness():
    """Test that generated keys are unique."""
    pp = setup()
    keys = [gen_key(pp) for _ in range(10)]
    
    # All secret keys should be different
    secret_keys = [k.sk for k in keys]
    assert len(set(secret_keys)) == len(secret_keys)
    
    # All public keys should be different
    public_keys = [k.P for k in keys]
    assert len(set(public_keys)) == len(public_keys)


def test_spend_proof():
    """Test spend proof generation and verification."""
    pp = setup()
    key = gen_key(pp)
    root = 12345
    
    proof = prove_spend(pp, key, root)
    assert verify_spend(pp, key.P, key.I, root, proof)


def test_spend_proof_with_context():
    """Test spend proof with context."""
    pp = setup()
    key = gen_key(pp)
    root = 12345
    ctx = b"test-context"
    
    proof = prove_spend(pp, key, root, ctx)
    assert verify_spend(pp, key.P, key.I, root, proof, ctx)
    
    # Should fail with different context
    assert not verify_spend(pp, key.P, key.I, root, proof, b"wrong-context")


def test_spend_proof_invalid():
    """Test spend proof with wrong parameters."""
    pp = setup()
    key1 = gen_key(pp)
    key2 = gen_key(pp)
    root = 12345
    
    proof = prove_spend(pp, key1, root)
    
    # Wrong public key
    assert not verify_spend(pp, key2.P, key1.I, root, proof)
    
    # Wrong key image
    assert not verify_spend(pp, key1.P, key2.I, root, proof)
    
    # Wrong root
    assert not verify_spend(pp, key1.P, key1.I, 54321, proof)