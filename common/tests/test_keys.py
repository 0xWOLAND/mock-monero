import pytest
from common.keys import (
    Keypair,
    FCMPKey,
    SpendProof,
    keygen,
    gen_key,
    Hp,
    key_image,
    prove_spend,
    verify_spend,
)
from common.group import setup


def test_keygen():
    """Test Monero-style keypair generation."""
    pp = setup()
    kp = keygen(pp)

    assert isinstance(kp, Keypair)
    assert 1 <= kp.sk < pp.q
    assert kp.P == (pp.G * kp.sk) % pp.q


def test_keygen_uniqueness():
    """Test that generated keypairs are unique."""
    pp = setup()
    keypairs = [keygen(pp) for _ in range(10)]

    secret_keys = [kp.sk for kp in keypairs]
    assert len(set(secret_keys)) == len(secret_keys)

    public_keys = [kp.P for kp in keypairs]
    assert len(set(public_keys)) == len(public_keys)


def test_gen_key_fcmp():
    """Test FCMP-style key generation."""
    pp = setup()
    key = gen_key(pp)

    assert isinstance(key, FCMPKey)
    assert 1 <= key.sk < pp.q
    assert key.P == (pp.g * key.sk) % pp.q
    assert key.I == (pp.U * key.sk) % pp.q


def test_gen_key_uniqueness():
    """Test that generated FCMP keys are unique."""
    pp = setup()
    keys = [gen_key(pp) for _ in range(10)]

    secret_keys = [k.sk for k in keys]
    assert len(set(secret_keys)) == len(secret_keys)

    public_keys = [k.P for k in keys]
    assert len(set(public_keys)) == len(public_keys)

    key_images = [k.I for k in keys]
    assert len(set(key_images)) == len(key_images)


def test_hash_to_point():
    """Test hash-to-point function Hp."""
    pp = setup()
    P1 = 12345
    P2 = 54321

    hp1 = Hp(pp, P1)
    hp2 = Hp(pp, P2)

    # Same input should give same output
    assert Hp(pp, P1) == hp1

    # Different inputs should give different outputs
    assert hp1 != hp2

    # Result should be in valid range
    assert 0 < hp1 < pp.q
    assert 0 < hp2 < pp.q


def test_key_image():
    """Test key image generation."""
    pp = setup()
    kp1 = keygen(pp)
    kp2 = keygen(pp)

    ki1 = key_image(pp, kp1)
    ki2 = key_image(pp, kp2)

    # Different keypairs should give different key images
    assert ki1 != ki2

    # Same keypair should give same key image
    assert key_image(pp, kp1) == ki1

    # Key image should be in valid range
    assert 0 < ki1 < pp.q


def test_spend_proof():
    """Test spend proof generation and verification."""
    pp = setup()
    key = gen_key(pp)
    root = 98765

    proof = prove_spend(pp, key, root)
    assert isinstance(proof, SpendProof)

    # Valid proof should verify
    assert verify_spend(pp, key.P, key.I, root, proof)


def test_spend_proof_with_context():
    """Test spend proof with context."""
    pp = setup()
    key = gen_key(pp)
    root = 98765
    ctx = b"test-context"

    proof = prove_spend(pp, key, root, ctx)

    # Should verify with correct context
    assert verify_spend(pp, key.P, key.I, root, proof, ctx)

    # Should fail with wrong context
    assert not verify_spend(pp, key.P, key.I, root, proof, b"wrong-context")


def test_spend_proof_invalid():
    """Test spend proof fails with wrong parameters."""
    pp = setup()
    key1 = gen_key(pp)
    key2 = gen_key(pp)
    root = 98765

    proof = prove_spend(pp, key1, root)

    # Wrong public key should fail
    assert not verify_spend(pp, key2.P, key1.I, root, proof)

    # Wrong key image should fail
    assert not verify_spend(pp, key1.P, key2.I, root, proof)

    # Wrong root should fail
    assert not verify_spend(pp, key1.P, key1.I, 12345, proof)


def test_proof_uniqueness():
    """Test that proofs are unique (probabilistically)."""
    pp = setup()
    key = gen_key(pp)
    root = 98765

    # Multiple proofs of the same statement should be different
    # (due to random nonce)
    proof1 = prove_spend(pp, key, root)
    proof2 = prove_spend(pp, key, root)

    # Proofs should be different objects
    assert proof1.A1 != proof2.A1 or proof1.A2 != proof2.A2 or proof1.z != proof2.z

    # But both should verify
    assert verify_spend(pp, key.P, key.I, root, proof1)
    assert verify_spend(pp, key.P, key.I, root, proof2)
