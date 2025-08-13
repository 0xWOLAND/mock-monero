import hashlib
import secrets
from sage.all import *

class FCMP:
    def __init__(self):
        # secp256k1 
        self.p = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
        self.F = GF(self.p)
        self.E = EllipticCurve(self.F, [0, 7])
        
        # Base point
        Gx = 55066263022277343669578718895168534326250603453777594175500187360389116729240
        Gy = 32670510020758816978083085130507043184471273380659243275938904335757337482424
        self.G = self.E(Gx, Gy)
        
        self.q = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
        
        # Generators
        self.Hv = self.h2c("VALUE|v1")
        self.Gb = self.h2c("BLIND|v1") 
        self.T = self.h2c("T|v1")
        self.U = self.h2c("U|v1")
        self.V = self.h2c("V|v1")
        
    def rscalar(self):
        """Secure random scalar"""
        return 1 + secrets.randbelow(self.q - 1)
        
    def h2c(self, tag):
        """Hash to curve"""
        for i in range(10000):
            data = tag.encode() + i.to_bytes(8, 'big')
            h = hashlib.sha512(data).digest()
            x = int.from_bytes(h[:32], 'big') % self.p
            
            try:
                y_sq = (x^3 + 7) % self.p
                y = self.F(y_sq).sqrt()
                if int(y) & 1:
                    y = -y
                pt = self.E([x, y])
                if not pt.is_zero():
                    return pt
            except:
                pass
        raise Exception("h2c failed")
    
    def h2s(self, data, sep=""):
        """Hash to scalar"""
        if isinstance(data, str):
            data = data.encode()
        elif not isinstance(data, bytes):
            data = str(data).encode()
        
        full = sep.encode() + b"|" + data
        h = hashlib.sha512(full).digest()
        return int.from_bytes(h, 'big') % self.q
    
    def pt2b(self, pt):
        """Point to bytes"""
        if pt.is_zero():
            return b'\x00' * 64
        return int(pt[0]).to_bytes(32, 'big') + int(pt[1]).to_bytes(32, 'big')
    
    def canon(self, outs):
        """Canonical ordering"""
        return sorted(outs, key=lambda o: self.pt2b(o['pk']))
    
    def commit(self, val, blind):
        """Pedersen commit"""
        return val * self.Hv + blind * self.Gb
    
    def leaf_hash(self, c, pk):
        """Leaf hash"""
        data = self.pt2b(c) + self.pt2b(pk)
        s1 = self.h2s(data, "LEAF_C")
        s2 = self.h2s(data, "LEAF_P")
        return s1 * self.U + s2 * self.V
    
    def merkle_hash(self, l, r, h):
        """Merkle hash"""
        data = h.to_bytes(4, 'big') + self.pt2b(l) + self.pt2b(r)
        s1 = self.h2s(data, f"MH_L{h}")
        s2 = self.h2s(data, f"MH_R{h}")
        return s1 * self.U + s2 * self.V
    
    def build_tree(self, leaves):
        """Build merkle tree"""
        if not leaves:
            return []
        
        layers = [leaves]
        curr = leaves
        h = 0
        
        while len(curr) > 1:
            next_layer = []
            for i in range(0, len(curr), 2):
                l = curr[i]
                if i + 1 < len(curr):
                    r = curr[i + 1]
                else:
                    pad = self.h2s(f"PAD_{h}_{i}".encode(), "PAD")
                    r = pad * self.U
                
                parent = self.merkle_hash(l, r, h)
                next_layer.append(parent)
            
            layers.append(next_layer)
            curr = next_layer
            h += 1
        
        return layers
    
    def keygen(self):
        """Generate keypair"""
        sk = self.rscalar()
        pk = sk * self.G
        return sk, pk
    
    def h2c_pt(self, pk):
        """Hash point to curve"""
        pub = self.pt2b(pk)
        h = hashlib.sha512(b"KI_H|" + pub).digest()
        
        for i in range(1000):
            x = (int.from_bytes(h[:32], 'big') + i) % self.p
            try:
                y_sq = (x^3 + 7) % self.p
                y = self.F(y_sq).sqrt()
                if int(y) & 1:
                    y = -y
                pt = self.E([x, y])
                if not pt.is_zero():
                    return pt
            except:
                continue
        raise Exception("h2c_pt failed")
    
    def key_img(self, sk, pk):
        """Compute key image"""
        hp = self.h2c_pt(pk)
        return sk * hp
    
    
    def make_out(self, amt, sk, pk):
        """Create output"""
        blind = self.rscalar()
        c = self.commit(amt, blind)
        ki = self.key_img(sk, pk)
        
        return {
            'amt': amt,
            'blind': blind,
            'c': c,
            'pk': pk,
            'ki': ki,
            'sk': sk
        }
    
    def ring_prove(self, canon_outs, sec_idx, sk, root, ki):
        """LSAG-style ring: bind same secret to G and H(P) with the same (c,s)"""
        n = len(canon_outs)
        c = [0] * n
        s = [0] * n

        # Per-member hash-to-curve bases H_i = H(P_i)
        H = [self.h2c_pt(o['pk']) for o in canon_outs]

        # Random for non-secret members
        for i in range(n):
            if i != sec_idx:
                c[i] = self.rscalar()
                s[i] = self.rscalar()

        # Secret nonce
        r = self.rscalar()
        R1_sec = r * self.G
        R2_sec = r * H[sec_idx]

        # Build commitments for all members
        R1, R2 = [], []
        for i, o in enumerate(canon_outs):
            if i == sec_idx:
                R1.append(R1_sec)
                R2.append(R2_sec)
            else:
                # R1_i = s_i*G - c_i*P_i
                R1.append(s[i] * self.G - c[i] * o['pk'])
                # R2_i = s_i*H_i - c_i*KI
                R2.append(s[i] * H[i] - c[i] * ki)

        # Transcript bound to (root, KI) and both commitment lists
        msg = b"RING|v1|" + self.pt2b(root) + self.pt2b(ki)
        transcript = (msg
                      + b"".join(self.pt2b(P) for P in R1)
                      + b"".join(self.pt2b(P) for P in R2)
                      + b"".join(self.pt2b(o['pk']) for o in canon_outs))
        Ctot = self.h2s(transcript, "RING")

        # Close the ring
        c[sec_idx] = (Ctot - sum(c)) % self.q
        s[sec_idx] = (r + c[sec_idx] * sk) % self.q

        return {"chals": c, "resps": s, "tot_chal": Ctot}
    
    def ring_verify(self, proof, canon_outs, root, ki):
        """Verify LSAG-style ring (two equations per member)"""
        c, s, Ctot = proof["chals"], proof["resps"], proof["tot_chal"]
        H = [self.h2c_pt(o['pk']) for o in canon_outs]

        # Recompute commitments
        R1, R2 = [], []
        for i, o in enumerate(canon_outs):
            R1.append(s[i] * self.G - c[i] * o['pk'])
            R2.append(s[i] * H[i] - c[i] * ki)

        msg = b"RING|v1|" + self.pt2b(root) + self.pt2b(ki)
        transcript = (msg
                      + b"".join(self.pt2b(P) for P in R1)
                      + b"".join(self.pt2b(P) for P in R2)
                      + b"".join(self.pt2b(o['pk']) for o in canon_outs))
        Etot = self.h2s(transcript, "RING")

        return (Etot == Ctot) and ((sum(c) % self.q) == Ctot)
    
    def prove(self, outs, sec_idx, sec_out):
        """Generate FCMP proof"""
        canon = self.canon(outs)
        
        # Find secret in canonical order
        sec_idx_canon = None
        for i, out in enumerate(canon):
            if out['pk'] == sec_out['pk']:
                sec_idx_canon = i
                break
        
        # Compute root
        leaves = [self.leaf_hash(o['c'], o['pk']) for o in canon]
        tree = self.build_tree(leaves)
        root = tree[-1][0]
        
        # LSAG ring (includes DLEQ binding)
        ring = self.ring_prove(canon, sec_idx_canon, sec_out['sk'], root, sec_out['ki'])
        
        return {
            'root': root,
            'ki': sec_out['ki'],
            'ring': ring,
        }
    
    def verify(self, proof, outs, spent_kis):
        """Verify FCMP proof"""
        # Linkability first - use bytes for hashable key images
        ki_bytes = self.pt2b(proof['ki'])
        if ki_bytes in spent_kis:
            return False, "Double spend"
        
        # Canonical set + root check
        canon = self.canon(outs)
        leaves = [self.leaf_hash(o['c'], o['pk']) for o in canon]
        tree = self.build_tree(leaves)
        if tree[-1][0] != proof['root']:
            return False, "Root mismatch"
        
        # LSAG ring check (includes DLEQ binding)
        if not self.ring_verify(proof['ring'], canon, proof['root'], proof['ki']):
            return False, "Ring failed"
        
        return True, "Valid"

def demo():
    fcmp = FCMP()
    
    # Users and outputs
    users = [fcmp.keygen() for _ in range(6)]
    outs = []
    for i, (sk, pk) in enumerate(users):
        amt = randint(100, 1000)
        out = fcmp.make_out(amt, sk, pk)
        outs.append(out)
    
    # Spend
    sec_idx = 2
    sec_out = outs[sec_idx]
    spent_kis = set()  # Will store key image bytes
    
    # Prove and verify
    proof = fcmp.prove(outs, sec_idx, sec_out)
    valid, msg = fcmp.verify(proof, outs, spent_kis)
    
    if valid:
        spent_kis.add(fcmp.pt2b(proof['ki']))  # Store as bytes
        print("FCMP++ LSAG proof valid")
    else:
        print(f"Proof failed: {msg}")
    
    # Double spend test
    proof2 = fcmp.prove(outs, sec_idx, sec_out)
    valid2, msg2 = fcmp.verify(proof2, outs, spent_kis)
    print(f"Double spend blocked: {valid2 == False}")

if __name__ == "__main__":
    demo()