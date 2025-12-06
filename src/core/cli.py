import os
import ast
import sys
import time
import json
import random
import hashlib
from datetime import datetime
import builtins
import platform

from core.encryption import get_ssn
from core.encryption import generate_keypair
from core.encryption import secure_keystream
from core.encryption import encrypt
from core.encryption import decrypt_with_priv
from core.encryption import decrypt_with_pub
from core.encryption import sign
from core.encryption import check_integrity

from core.parsers import ConfigurationParser
from core.parsers import UserConfigParser
from core.parsers import KeypairParser
from core.parsers import MessageParser
from core.parsers import ContactParser
from core.parsers import ThemeParser

from core.parsers import DEFAULT_CONFIG
from core.parsers import DEFAULT_USER_CONFIG

from .qrcode import generate_qr_ascii
from core.parsers import cprint




# ---- file paths ----

keypairs_file = "data/keypairs.json"
messages_file = "data/messages.json"
contacts_file = "data/contacts.json"

configuration_file = "data/conf.config"
user_config_file = "data/user.config"
themes_file = "data/themes.config"



# ---- helpers + func ----

VERSION = 'v1.1 Official POC Release'
timestamp = datetime.now().strftime("[%Y-%m-%d - %H:%M:%S]")





def new_keypair():
    seed, public_key, private_key, valid_status = generate_keypair()
    
    cfg = ConfigurationParser(configuration_file)
    storing_keypairs = cfg.get("storing_keypairs")

    if storing_keypairs == True:
        save_keypair(seed, public_key, private_key, valid_status)

    return seed, public_key, private_key, valid_status

def save_keypair(seed, public_key, private_key, valid_status):
    kpk = KeypairParser(keypairs_file)

    # convert bytes to hex string if necessary
    if isinstance(seed, bytes):
        seed = seed.hex()
    if isinstance(public_key, bytes):
        public_key = public_key.hex()
    if isinstance(private_key, bytes):
        private_key = private_key.hex()

    keypair_data = {
        "seed": seed,
        "public_key": public_key,
        "private_key": private_key,
        "valid": bool(valid_status)  # make sure it's bool (boolymon)
    }

    kpk.append_keypair(keypair_data)
    cprint("success", f"[+] Keypair saved successfully.")

def save_contact(public_key):
    ssn = get_ssn(public_key)
    ctb = ContactParser(contacts_file)
    
    new_contact = {
        "name": ssn,
        "public_key": public_key
    }

    ctb.append_contact(new_contact)

def save_message(message_sender_public_key, message_receiver_public_key, message):
    msg = MessageParser(messages_file)

    message_obj = {
        "content": message,
        "sender_public_key": message_sender_public_key,
        "receiver_public_key": message_receiver_public_key,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    msg.append_message(message_obj)





def choose_keypair(prompt="Choose keypair index (or press Enter to paste key): "):
    kpk = KeypairParser(keypairs_file)
    pairs = kpk.get_all()
    if pairs:
        print("Saved keypairs:")
        for i, kp in enumerate(pairs):
            print(f"  {i}: {kp.get('seed','<no-seed>')}  SSN:{get_ssn(kp['public_key'])}")
    choice = input(prompt).strip()
    if choice == "":
        return None
    if choice.isdigit():
        idx = int(choice)
        if 0 <= idx < len(pairs):
            return pairs[idx]
    print("[!] Invalid selection.")
    return None





def kp_show(): # FIX LATER
    try:
        kpk = KeypairParser(keypairs_file)
        pairs = kpk.get_all()
    except Exception as e:
        cprint("error", f"Failed to load keypairs: {e}")
        return

    if not pairs:
        print("\n")
        cprint("warning", "No saved keypairs.")
        return

    print("\n")
    for i, kp in enumerate(pairs):
        try:
            cprint("status", f"{i}. SSN:{get_ssn(kp['public_key'])}")
            cprint("cipher", f"    seed: {kp.get('seed', '[missing]')}")
            cprint("key", f"    public: {kp.get('public_key', '[missing]')}")
            cprint("key", f"    private: {kp.get('private_key', '[missing]')}")
        except Exception as e:
            cprint("error", f"Corrupt keypair at index {i}: {e}")
        print()


def kp_import():
    print("\n")
    pub = input("Enter public key: ").strip()
    if not pub:
        cprint("error", "No public key provided.")
        return

    priv = input("Enter private key (optional, press Enter to skip): ").strip() or None
    seed = input("Enter seed (optional, press Enter to skip): ").strip() or None

    keypair = {"public_key": pub}
    if priv:
        keypair["private_key"] = priv
    if seed:
        keypair["seed"] = seed

    try:
        kpk = KeypairParser(keypairs_file)
        kpk.append_keypair(keypair)
        cprint("success", "Keypair imported successfully.")
    except Exception as e:
        cprint("error", f"Failed to import: {e}")

    print("\n")


def kp_export():
    try:
        kpk = KeypairParser(keypairs_file)
        pairs = kpk.get_all()
    except Exception as e:
        cprint("error", f"Failed to load keypairs: {e}")
        return

    print("\n")

    if not pairs:
        cprint("error", "No saved keypairs.")
        return

    for i, kp in enumerate(pairs):
        try:
            cprint("key", f"{i}: SSN {get_ssn(kp['public_key'])}")
        except Exception:
            cprint("key", f"{i}: SSN [invalid]")

    print("\n")
    idx = input("Index to export: ").strip()

    if not idx.isdigit():
        cprint("error", "Invalid index.")
        return

    idx = int(idx)

    if idx < 0 or idx >= len(pairs):
        cprint("error", "Out of range.")
        return

    print("\n")
    try:
        print(json.dumps(pairs[idx], indent=4))
    except Exception as e:
        cprint("error", f"Failed to export keypair: {e}")
    print("\n")


def kp_delete():
    try:
        kpk = KeypairParser(keypairs_file)
        pairs = kpk.get_all()
    except Exception as e:
        cprint("error", f"Failed to load keypairs: {e}")
        return

    if not pairs:
        cprint("error", "No saved keypairs.")
        return

    print("\n")

    for i, kp in enumerate(pairs):
        try:
            cprint("key", f"{i}: SSN {get_ssn(kp['public_key'])}")
        except Exception:
            cprint("key", f"{i}: SSN [invalid]")

    print("\n")

    idx = input("Index to delete: ").strip()

    if not idx.isdigit():
        cprint("error", "Invalid index.")
        return

    idx = int(idx)

    if idx < 0 or idx >= len(pairs):
        cprint("error", "Out of range.")
        return

    confirm = input("Type DELETE to confirm: ").strip()
    if confirm != "DELETE":
        cprint("warning", "Deletion cancelled.")
        return

    try:
        kpk.delete_keypair(idx)
        print("\n")
        cprint("success", "Deleted.")
        print("\n")
    except Exception as e:
        cprint("error", f"Failed to delete: {e}")







def msg_show():
    try:
        mp = MessageParser(messages_file)
        msgs = mp.get_all()
    except Exception as e:
        cprint("error", f"Failed to load messages: {e}")
        return

    if not msgs:
        cprint("warning", "No messages.")
        return

    print("\n")
    for i, m in enumerate(msgs):
        try:
            cprint(
                "status",
                f"{i}. [{m['timestamp']}] "
                f"From:{get_ssn(m['sender_public_key'])} "
                f"To:{get_ssn(m['receiver_public_key'])}"
            )
            cprint("key", f"    {m['content']}")
        except Exception as e:
            cprint("error", f"Corrupt message at index {i}: {e}")

        print()


def msg_delete():
    try:
        mp = MessageParser(messages_file)
        msgs = mp.get_all()
    except Exception as e:
        cprint("error", f"Failed to load messages: {e}")
        return

    if not msgs:
        cprint("warning", "No messages.")
        return

    print("\n")
    for i, m in enumerate(msgs):
        try:
            preview = m.get("content", "")[:60]
            cprint("key", f"{i}. [{m.get('timestamp', '??')}] {preview}")
        except Exception:
            cprint("key", f"{i}. [corrupt message]")

    print("\n")
    idx = input("Index to delete: ").strip()

    if not idx.isdigit():
        cprint("error", "Invalid index.")
        return

    idx = int(idx)

    if idx < 0 or idx >= len(msgs):
        cprint("error", "Out of range.")
        return

    confirm = input("Type DELETE to confirm: ").strip()
    if confirm != "DELETE":
        cprint("warning", "Deletion cancelled.")
        return

    try:
        mp.delete_message(idx)
        print("\n")
        cprint("success", "Deleted.")
        print("\n")
    except Exception as e:
        cprint("error", f"Failed to delete: {e}")






def ct_show():
    try:
        cp = ContactParser(contacts_file)
        cs = cp.get_all()
    except Exception as e:
        cprint("error", f"Failed to load contacts: {e}")
        return

    if not cs:
        cprint("warning", "No contacts.")
        return

    print("\n")
    for i, c in enumerate(cs):
        try:
            name = c.get("name", "[no name]")
            pub = c.get("public_key", "[missing key]")
            cprint("key", f"{i}. {name} -> {pub}")
        except Exception as e:
            cprint("error", f"Corrupt contact at index {i}: {e}")

    print()


def ct_add():
    name = input("Contact name (or press Enter to use SSN): ").strip()
    pub = input("Paste public key: ").strip()

    if not pub:
        cprint("error", "No public key provided.")
        return

    try:
        if not name:
            name = get_ssn(pub)

        cp = ContactParser(contacts_file)
        cp.append_contact({"name": name, "public_key": pub})
        cprint("success", "Contact added.")
    except Exception as e:
        cprint("error", f"Failed to add contact: {e}")

    print()


def ct_remove():
    try:
        cp = ContactParser(contacts_file)
        cs = cp.get_all()
    except Exception as e:
        cprint("error", f"Failed to load contacts: {e}")
        return

    if not cs:
        cprint("warning", "No contacts.")
        return

    print("\n")
    for i, c in enumerate(cs):
        try:
            cprint("key", f"{i}: {c.get('name', '[no name]')}")
        except Exception:
            cprint("key", f"{i}: [corrupt contact]")

    print("\n")
    idx = input("Index to delete: ").strip()

    if not idx.isdigit():
        cprint("error", "Invalid index.")
        return

    idx = int(idx)

    if idx < 0 or idx >= len(cs):
        cprint("error", "Out of range.")
        return

    confirm = input("Type DELETE to confirm: ").strip()
    if confirm != "DELETE":
        cprint("warning", "Deletion cancelled.")
        return

    try:
        cp.delete_contact(idx)
        print("\n")
        cprint("success", "Deleted.")
        print("\n")
    except Exception as e:
        cprint("error", f"Failed to delete: {e}")


def ct_update():
    try:
        cp = ContactParser(contacts_file)
        cs = cp.get_all()
    except Exception as e:
        cprint("error", f"Failed to load contacts: {e}")
        return

    if not cs:
        cprint("warning", "No contacts.")
        return

    print("\n")
    for i, c in enumerate(cs):
        try:
            cprint("key", f"{i}: {c.get('name', '[no name]')}")
        except Exception:
            cprint("key", f"{i}: [corrupt contact]")

    print("\n")
    idx = input("Index to update: ").strip()

    if not idx.isdigit():
        cprint("error", "Invalid index.")
        return

    idx = int(idx)

    if idx < 0 or idx >= len(cs):
        cprint("error", "Out of range.")
        return

    cur = cs[idx]

    new_name = input(f"New name [{cur.get('name', '')}]: ").strip()
    new_pk = input("New public key (leave empty to keep): ").strip()

    updated = {
        "name": new_name or cur.get("name"),
        "public_key": new_pk or cur.get("public_key"),
    }

    try:
        cs[idx] = updated
        cp.save()
        print("\n")
        cprint("success", "Updated.")
        print("\n")
    except Exception as e:
        cprint("error", f"Failed to update: {e}")







def random_content(word_count=90):
    syllables = ["ka", "ri", "do", "ma", "se", "to", "lu", "ven", "chi", "gra", "lo", "fa"]
    words = ["".join(random.choices(syllables, k=random.randint(2, 4))) for _ in range(word_count)]
    return " ".join(words).capitalize() + "."

def test_message():
    print("\n")
    cprint("info", "Generating keypair A (user 1)")
    seed_A, public_key_A, private_key_A, valid_status_A = new_keypair()
    cprint("info", "Generating keypair B (user 2)")
    seed_B, public_key_B, private_key_B, valid_status_B = new_keypair()

    print("\n")

    cprint("status", "Keypairs generated...\n")

    print("Keypair A:")
    cprint("cipher", f"    seed: {seed_A}")
    cprint("key", f"    public key: {public_key_A}")
    cprint("key", f"    private key: {private_key_A}")
    cprint("info", f"    valid status: {valid_status_A}")
    print("\n")

    print("Keypair B:")
    cprint("cipher", f"    seed: {seed_B}")
    cprint("key", f"    public key: {public_key_B}")
    cprint("key", f"    private key: {private_key_B}")
    cprint("info", f"    valid status: {valid_status_B}")
    print("\n")

    print("Generating random message content...\n")
    random_words = random_content()
    print("Message content:")
    cprint("cipher", f"{random_words}\n")
    
    # print("Shaping message:")
    # print(f"    Sender: {private_key_A}")
    # print(f"    Receiver: {public_key_B}")    # not needed 
    # print(f"    Content: {random_words}")

    cprint("status", "Encrypting and forming message..")
    encrypted_message = shape(public_key_A, public_key_B, random_words)

    cprint("status", "Decrypting message with sender public key...")
    print("\n")
    print(f"    Message receiver public key: {public_key_B}")
    print(f"    Message encrypted hex: {encrypted_message}")
    dm = decrypt_with_pub(encrypted_message, public_key_B)
    print("\n")
    print(f"Decrypted message: {dm}")

    if dm == random_words:
        print("\n")
        cprint("success", "Encryption and decryption is valid\n")
    
    else:
        cprint("error", "Decryption didn't work, something went wrong.")





def do_backup():
    try:
        out = {
            "config": ConfigurationParser(configuration_file).config,
            "user": UserConfigParser(user_config_file).config,
            "keypairs": KeypairParser(keypairs_file).get_all(),
            "messages": MessageParser(messages_file).get_all(),
            "contacts": ContactParser(contacts_file).get_all()
        }

        fname = f"backup_{int(time.time())}.json"

        with open(fname, "w") as f:
            json.dump(out, f, indent=4)

        cprint("success", f"Backup written to {fname}")

    except Exception as e:
        cprint("error", f"Backup failed: {e}")


def do_restore():
    fname = input("Backup filename to restore: ").strip()

    if not fname:
        cprint("error", "No filename provided.")
        return

    if not os.path.exists(fname):
        cprint("error", "File not found.")
        return

    confirm = input("Type RESTORE to confirm overwrite: ").strip()
    if confirm != "RESTORE":
        cprint("warning", "Restore cancelled.")
        return

    try:
        with open(fname, "r") as f:
            data = json.load(f)
    except json.JSONDecodeError:
        cprint("error", "Invalid or corrupted backup file.")
        return
    except Exception as e:
        cprint("error", f"Failed to read backup: {e}")
        return

    try:
        if "config" in data:
            cfg = ConfigurationParser(configuration_file)
            cfg.config = data["config"]
            cfg.save()

        if "user" in data:
            uc = UserConfigParser(user_config_file)
            uc.config = data["user"]
            uc.save()

        if "keypairs" in data:
            k = KeypairParser(keypairs_file)
            k.keypairs = data["keypairs"]
            k.save()

        if "messages" in data:
            m = MessageParser(messages_file)
            m.messages = data["messages"]
            m.save()

        if "contacts" in data:
            c = ContactParser(contacts_file)
            c.contacts = data["contacts"]
            c.save()

        cprint("success", "Restore complete.")

    except Exception as e:
        cprint("error", f"Restore failed: {e}")


def do_clear():
    confirm = input(
        "This will wipe keypairs/messages/contacts.\n"
        "Type WIPE to confirm: "
    ).strip()

    if confirm != "WIPE":
        cprint("warning", "Aborted.")
        return

    failed = False

    for f in (keypairs_file, messages_file, contacts_file):
        try:
            if os.path.exists(f):
                os.remove(f)
        except Exception as e:
            failed = True
            cprint("error", f"Failed to delete {f}: {e}")

    if not failed:
        cprint("success", "Data cleared.")



def do_npair():
    cprint("info", f"{timestamp} Generating new keypair..")
    seed, public_key, private_key, valid_status = new_keypair()
    print("\n")
    show = input("Show keypair? (y/N): ").strip().lower()
    if show == "y":
        print("\nKeypair:")
        cprint("cipher", f"    seed: {seed}")
        cprint("key", f"    public key: {public_key}")
        cprint("key", f"    private key: {private_key}")
        cprint("debug", f"    valid status: {valid_status}\n")


def show_path():
    print("\n")
    print("Paths:")
    cprint("path", f"  keypairs: {os.path.abspath(keypairs_file)}")
    cprint("path", f"  messages: {os.path.abspath(messages_file)}")
    cprint("path", f"  contacts: {os.path.abspath(contacts_file)}")
    cprint("path", f"  config: {os.path.abspath(configuration_file)}")
    cprint("path", f"  user config: {os.path.abspath(user_config_file)}")
    print("\n")


def hexdump():
    target = input("Paste string or file path to hex-dump: ").strip()

    if not target:
        cprint("error", "No input provided.")
        return

    try:
        if os.path.exists(target):
            with open(target, "rb") as f:
                data = f.read()
        else:
            data = target.encode()

        print("\n")
        cprint("success", "Hexdump:")
        print(data.hex())
        print()

    except Exception as e:
        cprint("error", f"Hexdump failed: {e}")


def do_benchmark(iterations=100):
    if not isinstance(iterations, int) or iterations <= 0:
        cprint("error", "Invalid iteration count.")
        return

    cprint("status", f"Running simple benchmark ({iterations} iterations)")

    try:
        kp = choose_keypair("Use saved keypair index for both sides (or Enter to paste): ")
    except Exception as e:
        cprint("error", f"Keypair selection failed: {e}")
        return

    if kp:
        pub_a = kp.get("public_key")
        priv_a = kp.get("private_key")
        pub_b = pub_a
    else:
        pub_a = input("Sender public key: ").strip()
        priv_a = input("Sender private key (optional): ").strip() or None
        pub_b = input("Receiver public key: ").strip()

    if not pub_a or not pub_b:
        cprint("error", "Missing required public key(s).")
        return

    test_message = "bench " * 10

    try:
        start = time.time()

        for _ in range(iterations):
            c = encrypt(pub_a, pub_b, test_message)

            if priv_a:
                _ = decrypt_with_priv(c, priv_a)
            else:
                _ = decrypt_with_pub(c, pub_b)

        elapsed = time.time() - start

        cprint(
            "success",
            f"Completed {iterations} iterations in {elapsed:.3f}s "
            f"(avg {elapsed / iterations:.6f}s)"
        )

    except Exception as e:
        cprint("error", f"Benchmark failed: {e}")


def do_ping():
    try:
        cp = ContactParser(contacts_file)
        cs = cp.get_all()
    except Exception as e:
        cprint("error", f"Failed to load contacts: {e}")
        return

    if not cs:
        cprint("error", "No contacts saved.")
        return

    print("\n")
    for i, c in enumerate(cs):
        cprint("key", f"{i}: {c.get('name', '[no name]')}")

    print("\n")
    idx = input("Contact index: ").strip()

    if not idx.isdigit():
        cprint("error", "Invalid index.")
        return

    idx = int(idx)

    if idx < 0 or idx >= len(cs):
        cprint("error", "Out of range.")
        return

    pub = cs[idx].get("public_key")

    if not pub:
        cprint("error", "Selected contact has no public key.")
        return

    try:
        kp = choose_keypair(
            "Choose sender keypair index (or press Enter to paste sender private key): "
        )
    except Exception as e:
        cprint("error", f"Keypair selection failed: {e}")
        return

    if kp:
        sender_pub = kp.get("public_key")
        sender_priv = kp.get("private_key")
    else:
        sender_pub = input("Sender public key: ").strip()
        sender_priv = input("Sender private key (optional): ").strip() or None

    if not sender_pub:
        cprint("error", "No sender public key provided.")
        return

    payload = "PING " + datetime.now().isoformat()

    try:
        cmsg = encrypt(sender_pub, pub, payload)
        cprint("success", "Encrypted ping:")
        print(cmsg)
    except Exception as e:
        cprint("error", f"Ping encryption failed: {e}")
        return

    if sender_priv:
        try:
            dec = decrypt_with_priv(cmsg, sender_priv)
            cprint("success", "Self-check decrypted:")
            print(dec)
        except Exception:
            cprint("warning", "Self-check decryption failed.")





def do_encrypt():
    try:
        kpk = KeypairParser(keypairs_file)
        pairs = kpk.get_all() or []
    except Exception as e:
        cprint("error", f"Failed to load keypairs: {e}")
        return

    if pairs:
        print("\n")
        cprint("status", "Saved keypairs:")
        for i, kp in enumerate(pairs):
            seed = kp.get("seed", "<no-seed>")
            ssn = get_ssn(kp["public_key"])
            cprint("key", f"  {i}: {seed}  SSN:{ssn}")
        print()

    choice = input(
        "Choose sender keypair index (Enter = manual, 'n' = new): "
    ).strip()

    # --- Sender selection ---
    if choice == "":
        spub = input("Sender public key: ").strip()
        if not spub:
            cprint("error", "No sender public key provided.")
            return

    elif choice.lower() == "n":
        try:
            kp = new_keypair()
            spub = kp[1]
            cprint("success", "Generated new sender keypair.")
        except Exception as e:
            cprint("error", f"Keypair generation failed: {e}")
            return

    elif choice.isdigit():
        idx = int(choice)
        if 0 <= idx < len(pairs):
            spub = pairs[idx].get("public_key")
            if not spub:
                cprint("error", "Selected keypair has no public key.")
                return
        else:
            cprint("error", "Invalid index.")
            return
    else:
        cprint("error", "Invalid selection.")
        return

    rpub = input("Receiver public key: ").strip()
    if not rpub:
        cprint("error", "No receiver public key provided.")
        return

    msg = input("Message: ")
    if not msg:
        cprint("error", "Message is empty.")
        return

    try:
        shape(spub, rpub, msg)
    except Exception as e:
        cprint("error", f"Encryption failed: {e}")



def do_decrypt():
    c = input("Paste encrypted message: ").strip()
    if not c:
        cprint("error", "No ciphertext provided.")
        return

    mode = input("Decrypt with (priv/pub)?: ").strip().lower()

    if mode == "priv":
        try:
            kpk = KeypairParser(keypairs_file)
            _ = kpk.get_all() or []  # just to ensure file is valid
        except Exception as e:
            cprint("error", f"Failed to load keypairs: {e}")
            return

        priv = input("Paste receiver private key (64-byte hex): ").strip()
        priv = "".join(x for x in priv if x in "0123456789abcdefABCDEF")

        if not priv:
            cprint("error", "No valid private key provided.")
            return

        try:
            out = decrypt_with_priv(c, priv)
            print("\n")
            cprint("success", "Decrypted:")
            print(out)
            print()
        except Exception as e:
            cprint("error", f"Decryption failed: {e}")

    elif mode == "pub":
        pub = input("Paste receiver public key (hex): ").strip()
        pub = "".join(x for x in pub if x in "0123456789abcdefABCDEF")

        if not pub:
            cprint("error", "No valid public key provided.")
            return

        try:
            out = decrypt_with_pub(c, pub)
            print("\n")
            cprint("success", "Decrypted:")
            print(out)
            print()
        except Exception as e:
            cprint("error", f"Decryption failed: {e}")

    else:
        cprint("error", "Invalid mode. Use 'priv' or 'pub'.")






def shape(message_sender_public_key, message_receiver_public_key, message):
    top_marking = "\n========== BEGIN ANI MESSAGE ==========\n\n"
    bottom_marking = "\n\n  ==========  END MESSAGE  =========="

    encrypted_message = encrypt(message_sender_public_key, message_receiver_public_key, message)
    timestamp = time.strftime("%d:%m:%Y %H:%M:%S")
    message_timestamp = f"\n\nSender's clock timezone: {timestamp}"
    
    integrity_of_message = check_integrity(
        encrypted_hex = encrypted_message, 
        receiver_public_key = message_receiver_public_key, 
        expected_message = message
    )

    integrity = f"\nMessage integrity: {integrity_of_message}"

    message_sender = message_sender_public_key
    ssn = f"\nSender SSN: {get_ssn(message_sender_public_key)}"

    message_signature, content_signature = sign(message_sender_public_key, message_receiver_public_key, message)
    signature1 = f"\nMessage signature: {message_signature}"
    signature2 = f"\nContent signature: {content_signature}\n"

    signature2_qr = generate_qr_ascii(content_signature, return_string=True)
    output_message = f"{top_marking}{encrypted_message}{bottom_marking}{message_timestamp}{integrity}{ssn}{signature1}{signature2}{signature2_qr}"
    
    cfg = ConfigurationParser(configuration_file)
    storing_messages = cfg.get("storing_messages")
    storing_contacts = cfg.get("storing_contacts")

    if storing_contacts == True:
        save_contact(message_receiver_public_key)

    if storing_messages == True:
        save_message(message_sender_public_key, message_receiver_public_key, message)

    
    print(output_message)

    return encrypted_message





def show_config():
    c = ConfigurationParser(configuration_file).config
    u = UserConfigParser(user_config_file).config
    print("\n")
    cprint("info", "Client config:")

    for k,v in c.items():
        print(f"  {k}: {v}")

    print("\n")

    cprint("info", "User config:")

    for k,v in u.items():
        print(f"  {k}: {v}")
    print("\n")


def show_theme():
    try:
        tp = ThemeParser(themes_file)
    except Exception as e:
        cprint("error", f"Failed to load themes: {e}")
        return

    themes = tp.themes
    active = tp.active

    if not themes:
        cprint("warning", "No themes available.")
        return

    print("\n")
    cprint("info", f"Active theme: {active}")
    print()

    for theme_name, values in themes.items():
        if theme_name == active:
            cprint("success", f"[{theme_name}]")
        else:
            cprint("status", f"{theme_name}")

        if not isinstance(values, dict):
            cprint("error", "  Invalid theme format.")
            continue

        for k, v in values.items():
            print(f"  {k}: {v}")

        print()

    print()


def debug_stats():
    try:
        import sys
        import os
        import platform
        import time
        import shutil
        import gc
        import threading
        import tracemalloc

        print("\n")
        cprint("info", "=== Debug Stats ===")
        print()

        # --- Python & OS ---
        cprint("status", "Runtime")
        print(f"  Python: {sys.version.split()[0]}")
        print(f"  Executable: {sys.executable}")
        print(f"  Platform: {platform.system()} {platform.release()}")
        print(f"  Arch: {platform.machine()}")
        print(f"  PID: {os.getpid()}")
        print(f"  CWD: {os.getcwd()}")
        print()

        cprint("status", "Process")
        print(f"  Uptime: {time.time() - ps_start_time:.2f}s" if "ps_start_time" in globals() else "  Uptime: unknown")
        print(f"  Threads: {threading.active_count()}")
        print(f"  GC Objects: {len(gc.get_objects())}")
        print()

        cprint("status", "Memory")
        try:
            tracemalloc.start()
            cur, peak = tracemalloc.get_traced_memory()
            print(f"  Current: {cur / 1024:.2f} KB")
            print(f"  Peak: {peak / 1024:.2f} KB")
        except Exception:
            print("  Tracemalloc unavailable")
        print()

        cprint("status", "Disk")
        try:
            usage = shutil.disk_usage(os.getcwd())
            print(f"  Total: {usage.total / 1e9:.2f} GB")
            print(f"  Used: {usage.used / 1e9:.2f} GB")
            print(f"  Free: {usage.free / 1e9:.2f} GB")
        except Exception:
            print("  Disk usage unavailable")
        print()

        cprint("status", "Storage Files")
        for name, path in {
            "Config": configuration_file,
            "User": user_config_file,
            "Keypairs": keypairs_file,
            "Messages": messages_file,
            "Contacts": contacts_file,
        }.items():
            exists = os.path.exists(path)
            size = os.path.getsize(path) if exists else 0
            print(f"  {name}: {'OK' if exists else 'MISSING'} ({size} bytes)")

        print()
        cprint("success", "Debug stats collected successfully.")
        print()

    except Exception as e:
        cprint("error", f"Debug stats failed: {e}")



def do_etheme():
    try:
        tp = ThemeParser(themes_file)
    except Exception as e:
        cprint("error", f"Failed to load themes: {e}")
        return

    themes = tp.themes
    active = tp.active

    if not themes:
        cprint("error", "No themes available.")
        return

    print("\n")
    cprint("info", f"Active theme: {active}")
    print()

    for name in themes:
        if name == active:
            cprint("success", f"  {name} (active)")
        else:
            cprint("status", f"  {name}")

    print("\n")
    cprint("info", "Options:")
    print("  1. Set active theme")
    print("  2. Edit theme colour")
    print("  3. Show active theme")
    print("  4. Exit")

    choice = input("\nSelect option: ").strip()

    if choice == "1":
        name = input("Theme name to activate: ").strip()
        if name not in themes:
            cprint("error", "Theme does not exist.")
            return

        try:
            raw = open(themes_file, "r").read()
            lines = raw.splitlines()

            for i, line in enumerate(lines):
                if line.strip().startswith("ACTIVE_THEME"):
                    lines[i] = f'ACTIVE_THEME = "{name}"'
                    break
            else:
                lines.append(f'\nACTIVE_THEME = "{name}"')

            with open(themes_file, "w") as f:
                f.write("\n".join(lines))

            cprint("success", f"Active theme set to '{name}'")

        except Exception as e:
            cprint("error", f"Failed to set active theme: {e}")

    elif choice == "2":
        name = input("Theme name to edit: ").strip()
        if name not in themes:
            cprint("error", "Theme does not exist.")
            return

        theme = themes[name]

        print("\n")
        cprint("info", f"Editing theme: {name}")
        print()

        for k, v in theme.items():
            print(f"  {k}: {v}")

        print()
        key = input("Key to change (e.g. error, success, info): ").strip()
        if key not in theme:
            cprint("error", "Invalid theme key.")
            return

        value = input("New colour value (e.g. RED, BLUE, DIM): ").strip().upper()
        VALID_COLOURS = {
            "RESET", "BOLD", "DIM", "ITALIC", "UNDER",
            "BLACK", "RED", "GREEN", "YELLOW", "BLUE", "MAGENTA", "CYAN", "WHITE",
            "BRIGHT_BLACK", "BRIGHT_RED", "BRIGHT_GREEN", "BRIGHT_YELLOW",
            "BRIGHT_BLUE", "BRIGHT_MAGENTA", "BRIGHT_CYAN", "BRIGHT_WHITE",
            "BG_BLACK", "BG_RED", "BG_GREEN", "BG_YELLOW",
            "BG_BLUE", "BG_MAGENTA", "BG_CYAN", "BG_WHITE"
            }
            
        if value not in VALID_COLOURS:
            cprint("error", f"Invalid colour name: {value}")
            return

        theme[key] = value

        try:
            raw = open(themes_file, "r").read()
            start = raw.find("THEMES")
            start = raw.find("{", start)
            end = start
            brace = 0

            while end < len(raw):
                if raw[end] == "{":
                    brace += 1
                elif raw[end] == "}":
                    brace -= 1
                    if brace == 0:
                        end += 1
                        break
                end += 1

            # Use json.dumps with indentation for readability
            new_block = "THEMES = " + json.dumps(themes, indent=4)
            new_raw = raw[:raw.find("THEMES")] + new_block + raw[end:]

            with open(themes_file, "w") as f:
                f.write(new_raw)

            cprint("success", "Theme updated successfully.")

        except Exception as e:
            cprint("error", f"Failed to update theme: {e}")


    elif choice == "3":
        theme = themes.get(active, {})
        print("\n")
        cprint("info", f"Theme: {active}")
        print()

        for k, v in theme.items():
            print(f"  {k}: {v}")

        print()

    elif choice == "4":
        cprint("status", "Theme editor exited.")

    else:
        cprint("error", "Invalid selection.")



def do_econf():
    cp = ConfigurationParser(configuration_file)

    while True:
        print("\n")
        cprint("info", "Client Configuration Editor")
        print()

        for k, v in cp.config.items():
            print(f"  {k} = {v}")

        print("\n")
        cprint("info", "Options:")
        print("  1. Toggle message storage")
        print("  2. Set max saved messages")
        print("  3. Toggle keypair storage")
        print("  4. Set max saved keypairs")
        print("  5. Toggle contact storage")
        print("  6. Set max saved contacts")
        print("  7. Exit")

        choice = input("\nSelect option: ").strip()

        if choice == "1":
            val = not cp.get("storing_messages")
            cp.set("storing_messages", val)
            cprint("success", f"storing_messages set to {val}")

        elif choice == "3":
            val = not cp.get("storing_keypairs")
            cp.set("storing_keypairs", val)
            cprint("success", f"storing_keypairs set to {val}")

        elif choice == "5":
            val = not cp.get("storing_contacts")
            cp.set("storing_contacts", val)
            cprint("success", f"storing_contacts set to {val}")

        elif choice == "2":
            n = input("New max saved messages: ").strip()
            if n.isdigit():
                cp.set("number_of_saved_messages", int(n))
                cprint("success", "Max saved messages updated.")
            else:
                cprint("error", "Invalid number.")

        elif choice == "4":
            n = input("New max saved keypairs: ").strip()
            if n.isdigit():
                cp.set("number_of_saved_keypairs", int(n))
                cprint("success", "Max saved keypairs updated.")
            else:
                cprint("error", "Invalid number.")

        elif choice == "6":
            n = input("New max saved contacts: ").strip()
            if n.isdigit():
                cp.set("number_of_saved_contacts", int(n))
                cprint("success", "Max saved contacts updated.")
            else:
                cprint("error", "Invalid number.")

        elif choice == "7":
            cprint("status", "Client config editor exited.")
            return

        else:
            cprint("error", "Invalid option.")



def do_euconf():
    ucp = UserConfigParser(user_config_file)

    while True:
        print("\n")
        cprint("info", "User Configuration Editor")
        print()

        for k, v in ucp.config.items():
            print(f"  {k} = {v}")

        print("\n")
        cprint("info", "Options:")
        print("  1. Change username")
        print("  2. Change bio")
        print("  3. Reset to defaults")
        print("  4. Exit")

        choice = input("\nSelect option: ").strip()

        if choice == "1":
            new_name = input("New username: ").strip()
            if not new_name:
                cprint("error", "Username cannot be empty.")
                continue

            ucp.set("username", new_name)
            cprint("success", "Username updated.")

        elif choice == "2":
            new_bio = input("New bio: ").strip()
            ucp.set("bio", new_bio)
            cprint("success", "Bio updated.")

        elif choice == "3":
            confirm = input("Reset user config to defaults? (y/n): ").strip().lower()
            if confirm == "y":
                ucp.config = DEFAULT_USER_CONFIG.copy()
                ucp.save()
                cprint("success", "User configuration reset.")
            else:
                cprint("status", "Cancelled.")

        elif choice == "4":
            cprint("status", "User config editor exited.")
            return

        else:
            cprint("error", "Invalid option.")






def cli():
    ucfg = UserConfigParser(user_config_file)
    client_username = ucfg.get("username")

    cli_commands = {
        "help": "returns all commands",

        "econf": "edit client configuration",
        "euconf": "edit user configuration",
        "etheme": "edit theme",

        "npair": "generates a new keypair",
        "encrypt": "encrypt a message",
        "dcrypt": "decrypt a message",
        
        "tmsg": "makes a test message",

        "kpshow": "shows saved keypairs",
        "kpimport": "import a keypair or public key",
        "kpexport": "export a keypair or public key",
        "kpdel": "delete a saved keypair",

        "msgshow": "shows saved messages",
        "msgdel": "delete a saved message",

        "ctshow": "shows saved contacts",
        "ctadd": "add a new contact",
        "ctremove": "remove a saved contact",
        "ctupdate": "update a saved contact",

        "backup": "export all data to a backup file",
        "restore": "restore data from a backup file",
        "clear": "wipe all stored data (requires confirmation)",

        "version": "show tool version information",
        "config": "show combined configuration summary",
        "theme": "show theme summery",
        "path": "show storage/config directories",
        "ping": "send an encrypted ping to a contact",

        "debug": "shows general debug stats",
        "hexdump": "display raw bytes of a given file/key/message",
        "benchmark": "test encryption/decryption performance",

        "pp": "clear the terminal",
        "exit": "exit the program",
        "quit": "exit the program"
    }





    while True:
        try:
            user_input = input(f"antidote@ani$ ").strip()

        except (KeyboardInterrupt, EOFError):
            print("\n")
            print(f"\n{timestamp} closing antidote")
            break

        if not user_input:
            continue

        if user_input == "help":
            print("\n")
            for cmd in sorted(cli_commands):
                cprint("command", f"{cmd:<12} - {cli_commands[cmd]}")
            print("\n")
            continue

        if user_input in ("exit", "quit"):
            print(f"\n{timestamp} closing antidote")
            sys.exit(0)

        if user_input == "npair":
            print("\n")
            do_npair()
            continue

        if user_input == "encrypt":
            do_encrypt()
            continue

        if user_input == "dcrypt" or user_input == "decrypt":
            do_decrypt()
            continue

        if user_input == "tmsg":
            test_message()
            continue

        if user_input == "kpshow":
            kp_show()
            continue

        if user_input == "kpimport":
            kp_import()
            continue

        if user_input == "kpexport":
            kp_export()
            continue

        if user_input == "kpdel":
            kp_delete()
            continue

        if user_input == "msgshow":
            msg_show()
            continue

        if user_input == "msgdel":
            msg_delete()
            continue

        if user_input == "ctshow":
            ct_show()
            continue

        if user_input == "ctadd":
            ct_add()
            continue

        if user_input == "ctremove":
            ct_remove()
            continue

        if user_input == "ctupdate":
            ct_update()
            continue

        if user_input == "backup":
            do_backup()
            continue

        if user_input == "restore":
            do_restore()
            continue

        if user_input == "clear":
            do_clear()
            continue

        if user_input == "config":
            show_config()
            continue
        
        if user_input == "theme":
            show_theme()
            continue

        if user_input == "version":
            cprint("info", f"Antidote {VERSION}")
            continue

        if user_input == "path":
            show_path()
            continue

        if user_input == "ping":
            do_ping()
            continue

        if user_input == "hexdump":
            hexdump()
            continue

        if user_input == "time":
            print(f"current time: {timestamp}")
            continue

        if user_input == "econf":
            do_econf()
            continue

        if user_input == "euconf":
            do_euconf()
            continue

        if user_input == "etheme":
            do_etheme()
            continue
        
        if user_input == "debug":
            debug_stats()
            continue

        if user_input == "pp":
            if platform.system() == "Windows":
                os.system("cls")
            else:
                os.system("clear")

            continue

        if user_input == "benchmark":
            it = input("Iterations (default 100): ").strip()
            try:
                itn = int(it) if it else 100
            except:
                itn = 100
            do_benchmark(itn)

            continue

        print(f"\nunknown command: '{user_input}' | use 'help' to see all commands")

ps_start_time = time.time()