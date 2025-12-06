import os
import hashlib

p = 2**255 - 19

def inv(x):
    return pow(x, p-2, p)

d = (-121665 * inv(121666)) % p

a = p - 1

def mod_sqrt(u):    
    if u % p == 0:
        return 0
    x = pow(u, (p + 3) // 8, p)
    if (x * x - u) % p == 0:
        return x
 
    # try x = x * 2^((p-1)/4)
    I = pow(2, (p - 1) // 4, p)
    x = (x * I) % p
    if (x * x - u) % p == 0:
        return x
    return None

By = (4 * inv(5)) % p

num = (By * By - 1) % p
den = (d * By * By + 1) % p
Bx = mod_sqrt((num * inv(den)) % p)

if Bx is None:
    raise RuntimeError("failed to compute basepoint x")

B = (Bx % p, By % p)


def ed_add(P, Q):
    (x1, y1), (x2, y2) = P, Q
    x1x2 = (x1 * x2) % p
    y1y2 = (y1 * y2) % p
    xnum = (x1 * y2 + x2 * y1) % p
    xden = (1 + d * x1x2 * y1y2) % p
    ynum = (y1y2 - a * x1x2) % p
    yden = (1 - d * x1x2 * y1y2) % p
    x3 = (xnum * inv(xden)) % p
    y3 = (ynum * inv(yden)) % p

    return (x3, y3)

def ed_double(P):
    return ed_add(P, P)

def scalarmult(P, e):
    Q = (0, 1)
    R = P
    while e > 0:
        if e & 1:
            Q = ed_add(Q, R)
        R = ed_double(R)
        e >>= 1
    return Q

def encodepoint(P):
    x, y = P
    y_bytes = int.to_bytes(y, 32, "little")
    x_lsb = x & 1

    last = y_bytes[-1]
    last = (last & 0x7F) | (x_lsb << 7)
    y_bytes = y_bytes[:-1] + bytes([last])

    return y_bytes

def clamp_scalar(h_bytes32):
    hb = bytearray(h_bytes32)

    hb[0] &= 248
    hb[31] &= 127
    hb[31] |= 64

    return int.from_bytes(hb, "little")

def generate_keypair():
    seed = os.urandom(32)
    h = hashlib.sha512(seed).digest()
    a = clamp_scalar(h[:32])
    A = scalarmult(B, a)
    public_key = encodepoint(A)

    return seed, public_key

def derive_public_from_private(private_key_hex: str) -> str:
    if not isinstance(private_key_hex, str):
        raise TypeError("private_key_hex must be a hex string")

    priv_bytes = bytes.fromhex(private_key_hex)

    if len(priv_bytes) == 64:
        seed = priv_bytes[:32]
    elif len(priv_bytes) == 32:
        seed = priv_bytes
    else:
        raise ValueError("private_key_hex must be 32- or 64-byte hex (seed or seed+pub)")

    h = hashlib.sha512(seed).digest()
    a = clamp_scalar(h[:32])
    A = scalarmult(B, a)
    public_key_bytes = encodepoint(A)

    return public_key_bytes.hex()

# only takes in raw bytes, NOT hex strings ("abc123..")
def verify_keypair(keypair):    # takes in a tuple (seed, public_key) or a 64 byte concentrated key (seed + public_key) 
    if isinstance(keypair, tuple):
        seed, pub = keypair
    elif isinstance(keypair, (bytes, bytearray)) and len(keypair) == 64:
        seed, pub = keypair[:32], keypair[32:]
    else:
        raise ValueError("function only takes in a tuple or a 64 byte concentrated key")

    h = hashlib.sha512(seed).digest()
    a = clamp_scalar(h[:32])

    A = scalarmult(B, a)
    derived_pub = encodepoint(A)

    return derived_pub == pub
    # returns True if valid, false otherwise.

def keygen():
    sk_seed, pk = generate_keypair()

    public_key = pk.hex()
    private_key = (sk_seed + pk).hex()

    valid_status = verify_keypair((sk_seed, pk))

    return sk_seed, public_key, private_key, valid_status