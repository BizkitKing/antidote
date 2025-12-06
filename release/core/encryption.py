import os
import time
import hashlib
import hmac

from .ed25519 import keygen
from .ed25519 import derive_public_from_private


def get_ssn(message_sender_public_key):

    return message_sender_public_key[:12]

def generate_keypair():
    seed, public_key, private_key, valid_status = keygen()
    return seed, public_key, private_key, valid_status



def _key_bytes_from_str(s: str) -> bytes:
    return hashlib.sha256(s.encode('utf-8')).digest()

def secure_keystream(key: str, length: int) -> bytes:
    key_bytes = _key_bytes_from_str(key)
    out = b''
    counter = 0
    while len(out) < length:
        ctr = counter.to_bytes(4, 'big')
        out += hmac.new(key_bytes, ctr, hashlib.sha256).digest()
        counter += 1
    return out[:length]



def encrypt(message_sender_public_key: str, message_receiver_public_key: str, message_content: str) -> str:
    nonce = os.urandom(16)
    msg_bytes = message_content.encode('utf-8')
    
    ks_seed = f"{message_receiver_public_key}:{nonce.hex()}"
    keystream = secure_keystream(ks_seed, len(msg_bytes))
    ciphertext = bytes([m ^ k for m, k in zip(msg_bytes, keystream)])
    
    
    hmac_key = _key_bytes_from_str(message_receiver_public_key)
    tag = hmac.new(hmac_key, nonce + ciphertext, hashlib.sha256).digest()

    return nonce.hex() + ciphertext.hex() + tag.hex()



def decrypt_with_pub(encrypted_hex: str, receiver_public_key: str):
    if len(encrypted_hex) < 32 + 64:
        raise ValueError("Encrypted data too short / malformed.")

    nonce_hex = encrypted_hex[:32]
    tag_hex = encrypted_hex[-64:]
    ct_hex = encrypted_hex[32:-64]

    try:
        nonce = bytes.fromhex(nonce_hex)
        ciphertext = bytes.fromhex(ct_hex)
        tag = bytes.fromhex(tag_hex)

    except ValueError:
        raise ValueError("Encrypted text is not valid hex.")


    hmac_key = _key_bytes_from_str(receiver_public_key)
    expected_tag = hmac.new(hmac_key, nonce + ciphertext, hashlib.sha256).digest()

    if not hmac.compare_digest(tag, expected_tag):
        raise ValueError("Authentication failed (bad tag) — ciphertext may be tampered with.")

    ks_seed = f"{receiver_public_key}:{nonce_hex}"
    keystream = secure_keystream(ks_seed, len(ciphertext))
    plaintext_bytes = bytes([c ^ k for c, k in zip(ciphertext, keystream)])
    
    try:
        return plaintext_bytes.decode('utf-8')
    except UnicodeDecodeError:
        return plaintext_bytes
        
def decrypt_with_priv(encrypted_hex, receiver_private_key_hex):
    try:
        receiver_pub_hex = derive_public_from_private(receiver_private_key_hex)
    except Exception as e:
        raise ValueError(f"Failed to derive public key from private key: {e}")

    try:
        return decrypt_with_pub(encrypted_hex, receiver_pub_hex)
    except Exception as e:
        raise ValueError(f"Decryption failed: {e}")



def sign(message_sender_public_key: str, message_receiver_public_key: str, message: str):

    sender_public_key_cut_size = 8
    receiver_public_key_cut_size = 8
    
    part1_key_sig = ''
    part2_key_sig = ''

    for _ in range(sender_public_key_cut_size):
        idx = int.from_bytes(os.urandom(2), 'big') % len(message_sender_public_key)
        part1_key_sig += message_sender_public_key[idx]

    for _ in range(receiver_public_key_cut_size):
        idx = int.from_bytes(os.urandom(2), 'big') % len(message_receiver_public_key)
        part2_key_sig += message_receiver_public_key[idx]

    hashed_signature = hashlib.sha256((part1_key_sig + part2_key_sig).encode('utf-8')).hexdigest()
    content_signature = hashlib.sha256(message.encode('utf-8')).hexdigest()

    return hashed_signature, content_signature


def check_integrity(encrypted_hex: str, receiver_public_key: str, expected_message: str) -> bool:
    try:
        decrypted = decrypt_with_pub(encrypted_hex, receiver_public_key)
    except Exception:
        # failed to decrypt or HMAC check failed
        return False

    # decrypted might be bytes if UTF-8 fails
    if isinstance(decrypted, bytes):
        try:
            decrypted = decrypted.decode("utf-8")
        except UnicodeDecodeError:
            # can't decode, can't match
            return False

    return decrypted == expected_message
