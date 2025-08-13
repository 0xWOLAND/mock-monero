#!/usr/bin/env sage

import hashlib
import secrets
from sage.all import *

class MoneroCorrect:
    def __init__(self):
        # secp256k1 (toy-friendly, prime order)
        self.p = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
        self.E = EllipticCurve(GF(self.p), [0, 7])
        
        Gx = 55066263022277343669578718895168534326250603453777594175500187360389116729240
        Gy = 32670510020758816978083085130507043184471273380659243275938904335757337482424
        self.G = self.E(Gx, Gy)
        self.q = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
        
        # Independent base for amount commitments
        self.H = self.hash_to_point("AMOUNT_BASE|v1")
        
    def enc(self, P):
        """Canonical point encoding (x||y)"""
        if P.is_zero():
            return b'\x00' * 64
        return int(P[0]).to_bytes(32, 'big') + int(P[1]).to_bytes(32, 'big')
    
    def h2s(self, data, domain=""):
        """Hash to scalar with domain separation"""
        if isinstance(data, str):
            data = data.encode()
        if domain:
            data = domain.encode() + b"|" + data
        return int.from_bytes(hashlib.sha256(data).digest(), 'big') % self.q
    
    def hash_to_point(self, domain):
        """Hash to curve point (deterministic)"""
        for i in range(1000):
            seed = domain.encode() + i.to_bytes(4, 'big')
            x = int.from_bytes(hashlib.sha256(seed).digest(), 'big') % self.p
            
            try:
                y_sq = (pow(x, 3, self.p) + 7) % self.p
                y = GF(self.p)(y_sq).sqrt()
                # Canonical y-parity
                if int(y) & 1:
                    y = -y
                P = self.E([x, int(y)])
                if not P.is_zero():
                    return P
            except Exception:
                continue
        raise Exception("hash_to_point failed")
    
    def keygen(self):
        """Generate keypair"""
        sk = 1 + secrets.randbelow(self.q - 1)
        pk = sk * self.G
        return sk, pk
    
    def _generate_decoys(self, count):
        """Generate placeholder decoy one-time keys (for demo only)"""
        decoys = []
        for _ in range(count):
            # In reality, these would come from UTXO set
            r_decoy = 1 + secrets.randbelow(self.q - 1)
            dummy_view, dummy_spend = self.keygen(), self.keygen()
            _, decoy_pk = self.make_stealth(r_decoy, dummy_view[1], dummy_spend[1])
            decoys.append(decoy_pk)
        return decoys
    
    def make_stealth(self, r, A_view_pk, B_spend_pk):
        """Proper stealth address derivation"""
        R = r * self.G
        shared_secret = r * A_view_pk
        t = self.h2s(self.enc(shared_secret), "STEALTH_DERIVE|v1")
        P = B_spend_pk + t * self.G  # one-time public key
        return R, P
    
    def derive_one_time_key(self, a_view_sk, b_spend_sk, R):
        """Receiver derives one-time private key"""
        shared_secret = a_view_sk * R
        t = self.h2s(self.enc(shared_secret), "STEALTH_DERIVE|v1")
        return (t + b_spend_sk) % self.q
    
    def key_image(self, x_one_time_sk, P_one_time_pk):
        """Compute key image I = x * H_p(P)"""
        H_p = self.hash_to_point("KEY_IMAGE_" + self.enc(P_one_time_pk).hex())
        return x_one_time_sk * H_p
    
    def lsag_sign(self, msg, x, P, ring_pks, ring_idx):
        """LSAG linkable ring signature"""
        n = len(ring_pks)
        
        # Key image
        I = self.key_image(x, P)
        
        # Hash-to-point for each ring member
        H_pks = []
        for pk in ring_pks:
            H_pk = self.hash_to_point("KEY_IMAGE_" + self.enc(pk).hex())
            H_pks.append(H_pk)
        
        # Random values for non-signer members
        c = [0] * n
        s = [0] * n
        for i in range(n):
            if i != ring_idx:
                c[i] = 1 + secrets.randbelow(self.q - 1)
                s[i] = 1 + secrets.randbelow(self.q - 1)
        
        # Secret commitment
        alpha = 1 + secrets.randbelow(self.q - 1)
        R1_s = alpha * self.G
        R2_s = alpha * H_pks[ring_idx]
        
        # Build all commitments
        R1, R2 = [], []
        for i in range(n):
            if i == ring_idx:
                R1.append(R1_s)
                R2.append(R2_s)
            else:
                # Simulate: R1_i = s_i*G - c_i*P_i, R2_i = s_i*H_i - c_i*I
                R1.append(s[i] * self.G - c[i] * ring_pks[i])
                R2.append(s[i] * H_pks[i] - c[i] * I)
        
        # Challenge hash (includes ALL transcript elements)
        m = msg.encode() if isinstance(msg, str) else msg
        transcript = (m
                      + b"".join(self.enc(R) for R in R1)
                      + b"".join(self.enc(R) for R in R2)
                      + b"".join(self.enc(pk) for pk in ring_pks)
                      + self.enc(I))
        
        C = self.h2s(transcript, "LSAG_CHALLENGE|v1")
        
        # Complete the ring
        c[ring_idx] = (C - sum(c)) % self.q
        s[ring_idx] = (alpha + c[ring_idx] * x) % self.q
        
        return {"c": c, "s": s, "I": I, "C": C}
    
    def lsag_verify(self, msg, sig, ring_pks):
        """Verify LSAG signature"""
        c, s, I, C = sig["c"], sig["s"], sig["I"], sig["C"]
        n = len(ring_pks)
        
        # Strict size checks
        if len(c) != n or len(s) != n:
            return False
        
        # Reject invalid key image
        if I.is_zero():
            return False
        
        # Reject duplicate ring members
        if len({self.enc(pk) for pk in ring_pks}) != len(ring_pks):
            return False
        
        # Hash-to-point for each member
        H_pks = []
        for pk in ring_pks:
            H_pk = self.hash_to_point("KEY_IMAGE_" + self.enc(pk).hex())
            H_pks.append(H_pk)
        
        # Recompute commitments
        R1, R2 = [], []
        for i in range(n):
            R1.append(s[i] * self.G - c[i] * ring_pks[i])
            R2.append(s[i] * H_pks[i] - c[i] * I)
        
        # Recompute challenge (fixed transcript concatenation)
        m = msg.encode() if isinstance(msg, str) else msg
        transcript = (m
                      + b"".join(self.enc(R) for R in R1)
                      + b"".join(self.enc(R) for R in R2)
                      + b"".join(self.enc(pk) for pk in ring_pks)
                      + self.enc(I))
        
        expected_C = self.h2s(transcript, "LSAG_CHALLENGE|v1")
        
        return expected_C == C and (sum(c) % self.q) == C
    
    def make_tx(self, a_view_sk, A_view_pk, b_spend_sk, B_spend_pk,
                recv_A_view_pk, recv_B_spend_pk, amount):
        """Create Monero-style transaction"""
        
        # Ephemeral key for this transaction
        r = 1 + secrets.randbelow(self.q - 1)
        
        # Sender's one-time address (input)
        R_in, P_in = self.make_stealth(r, A_view_pk, B_spend_pk)
        x_in = self.derive_one_time_key(a_view_sk, b_spend_sk, R_in)
        
        # Unit check for input key (catch wiring mistakes)
        assert x_in * self.G == P_in, "One-time key derivation failed"
        
        # Recipient's one-time address (output)
        r_out = 1 + secrets.randbelow(self.q - 1)
        R_out, P_out = self.make_stealth(r_out, recv_A_view_pk, recv_B_spend_pk)
        
        # RingCT-style amount commitments (simplified)
        blind_in = 1 + secrets.randbelow(self.q - 1)
        # For toy balance: use same blinding so C_in == C_out when amounts equal
        blind_out = blind_in  # Could be random for real privacy
        C_in = amount * self.H + blind_in * self.G     # input commitment
        C_out = amount * self.H + blind_out * self.G   # output commitment
        
        # Ring of one-time public keys (sender + decoys)
        # NOTE: Real decoys would be other outputs' one-time pubkeys from UTXO set
        decoy_pks = self._generate_decoys(3)  # 3 placeholder decoys
        
        ring_pks = [P_in] + decoy_pks
        sender_idx = 0
        
        # Transaction message (canonical bytes for tighter practice)
        tx_msg = (b"MONERO_TX|" + 
                 self.enc(R_out) + 
                 self.enc(P_out) + 
                 self.enc(C_in) + 
                 self.enc(C_out))
        
        # LSAG signature
        sig = self.lsag_sign(tx_msg, x_in, P_in, ring_pks, sender_idx)
        
        return {
            'R_out': R_out,      # For recipient to derive key
            'P_out': P_out,      # Output stealth address
            'C_in': C_in,        # Input commitment
            'C_out': C_out,      # Output commitment
            'ring': ring_pks,    # Ring of one-time keys
            'signature': sig,    # LSAG signature with key image
            'msg': tx_msg,
            'amount': amount     # Hidden in real Monero
        }
    
    def verify_tx(self, tx, spent_key_images):
        """Verify transaction"""
        # Check double-spend via key image
        I_bytes = self.enc(tx['signature']['I'])
        if I_bytes in spent_key_images:
            return False, "Double spend - key image already used"
        
        # Reject zero key image
        if tx['signature']['I'].is_zero():
            return False, "Invalid key image"
        
        # Verify LSAG ring signature
        if not self.lsag_verify(tx['msg'], tx['signature'], tx['ring']):
            return False, "LSAG signature verification failed"
        
        # In real Monero: verify commitments sum to zero + Bulletproof range proofs
        # For toy: check commitments are non-zero + simple balance structure
        if tx['C_in'].is_zero() or tx['C_out'].is_zero():
            return False, "Invalid amount commitments"
        
        # Toy balance check (does NOT hide amounts; just shows structure)
        if tx['C_in'] == tx['C_out']:
            # Balanced transaction (same amount, same blinding)
            pass
        
        return True, "Transaction verified"

def demo():
    monero = MoneroCorrect()
    
    # Alice (sender) - separate view and spend key pairs
    a_alice, A_alice = monero.keygen()  # view keypair
    b_alice, B_alice = monero.keygen()  # spend keypair
    
    # Bob (recipient) - separate view and spend key pairs
    a_bob, A_bob = monero.keygen()      # view keypair  
    b_bob, B_bob = monero.keygen()      # spend keypair
    
    spent_key_images = set()
    
    # Create transaction
    tx = monero.make_tx(a_alice, A_alice, b_alice, B_alice,
                       A_bob, B_bob, 100)
    
    # Verify transaction
    valid, msg = monero.verify_tx(tx, spent_key_images)
    
    if valid:
        # Mark key image as spent
        spent_key_images.add(monero.enc(tx['signature']['I']))
        
        print("Monero transaction verified")
        print(f"LSAG ring size: {len(tx['ring'])}")
        print("Stealth addresses used")
        print("Key image prevents double-spend")
        
        # Test double-spend prevention
        valid2, msg2 = monero.verify_tx(tx, spent_key_images)
        print(f"Double-spend blocked: {not valid2}")
        
        # Demonstrate receiver can derive their key
        x_recv = monero.derive_one_time_key(a_bob, b_bob, tx['R_out'])
        print(f"Recipient can derive private key: {x_recv * monero.G == tx['P_out']}")
        
    else:
        print(f"Transaction failed: {msg}")

if __name__ == "__main__":
    demo()