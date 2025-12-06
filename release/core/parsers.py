import os
import ast
import sys
import time
import json
import random
import hashlib
from datetime import datetime
import builtins

from .colours import Colour


# ---- helpers ----

timestamp = datetime.now().strftime("[%Y-%m-%d - %H:%M:%S]")
def random_num():
    return random.randint(0, 90000000)

# ---- file paths ----

keypairs_file = "data/keypairs.json"
messages_file = "data/messages.json"
contacts_file = "data/contacts.json"

configuration_file = "data/conf.config"
user_config_file = "data/user.config"
themes_file = "data/themes.config"

DEFAULT_CONFIG = {
    "storing_messages": True,
    "number_of_saved_messages": 10,
    "storing_keypairs": True,
    "number_of_saved_keypairs": 10,
    "storing_contacts": True,
    "number_of_saved_contacts": 10
}

DEFAULT_USER_CONFIG = {
    "username": f"user{random_num()}",
    "bio": f""
}


STATUS_TAGS = {
    "info": "INFO ⓘ",
    "success": "SUCCESS ✔",
    "warning": "WARNING ⚠",
    "error": "ERROR ✖",
    "debug": "[DEBUG]",
}

def cprint(status, message):
    tp = ThemeParser(themes_file) # is this inefficient? yes. what are YOU gonna do about it?
    colour = tp.get_colour(status)
    prefix = STATUS_TAGS.get(status, "")  # get symbol or empty string
    if prefix:
        print(f"{colour}{prefix} {message}{Colour.RESET}")
    else:
        print(f"{colour}{message}{Colour.RESET}")


class ConfigurationParser:
    def __init__(self, filepath):
        self.filepath = filepath
        self.config = {}
        self.load()

    def load(self):
        if not os.path.exists(self.filepath):
            print("error", f"{timestamp} Configuration file not found, creating one with defaults...")
            os.makedirs(os.path.dirname(self.filepath), exist_ok=True)
            self.config = DEFAULT_CONFIG.copy()
            self.save()
            return

        with open(self.filepath, 'r') as f:
            lines = f.readlines()

        if not lines:
            print(f"{timestamp} Configuration file found but empty, filling with defaults...")
            self.config = DEFAULT_CONFIG.copy()
            self.save()
            return

        for line in lines:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()
                try:
                    self.config[key] = ast.literal_eval(value)
                except Exception:
                    print(f"{timestamp} Warning: Could not parse line: '{line}'. Using default if available.")
                    if key in DEFAULT_CONFIG:
                        self.config[key] = DEFAULT_CONFIG[key]

        for key, value in DEFAULT_CONFIG.items():
            self.config.setdefault(key, value)


    def save(self):
        with open(self.filepath, 'w') as f:
            for key, value in self.config.items():
                f.write(f"{key} = {repr(value)}\n")

    def get(self, key, default=None):
        return self.config.get(key, default)

    def set(self, key, value):
        self.config[key] = value
        self.save()

    def delete(self, key):
        if key in self.config:
            del self.config[key]
            self.save()

class UserConfigParser():
    def __init__(self, filepath):
        self.filepath = filepath
        self.config = {}
        self.load()

    def load(self):
        if not os.path.exists(self.filepath):
            print(f"{timestamp} User configuration file not found, creating one with defaults...")
            os.makedirs(os.path.dirname(self.filepath), exist_ok=True)
            self.config = DEFAULT_USER_CONFIG.copy()
            self.save()
            return

        with open(self.filepath, 'r') as f:
            lines = f.readlines()

        if not lines:
            print(f"{timestamp} User configuration file found but empty, filling with defaults...")
            self.config = DEFAULT_USER_CONFIG.copy()
            self.save()
            return

        for line in lines:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()
                try:
                    self.config[key] = ast.literal_eval(value)
                except Exception:
                    print(f"{timestamp} Warning: Could not parse line: '{line}'. Using default if available.")
                    if key in DEFAULT_USER_CONFIG:
                        self.config[key] = DEFAULT_USER_CONFIG[key]

        for key, value in DEFAULT_USER_CONFIG.items():
            self.config.setdefault(key, value)


    def save(self):
        with open(self.filepath, 'w') as f:
            for key, value in self.config.items():
                f.write(f"{key} = {repr(value)}\n")

    def get(self, key, default=None):
        return self.config.get(key, default)

    def set(self, key, value):
        self.config[key] = value
        self.save()

    def delete(self, key):
        if key in self.config:
            del self.config[key]
            self.save()

class ThemeParser:
    def __init__(self, filepath):
        self.filepath = filepath
        self.themes = {}
        self.active = "default"
        self.load()

    def load(self):
        if not os.path.exists(self.filepath):
            raise FileNotFoundError(f"Theme file missing: {self.filepath}")

        raw = open(self.filepath, "r").read()

        themes_block = self._extract_block(raw, "THEMES")
        if themes_block:
            try:
                self.themes = ast.literal_eval(themes_block)
            except:
                print("Could not parse THEMES block in themes.config")
                print("Please use default config (can be found on GitHub) or fix issues")
                sys.exit(0)

        active = self._extract_assignment(raw, "ACTIVE_THEME")
        if active and active.strip():
            self.active = active.strip('"').strip("'")
        else:
            self.active = "default"

        # fallback if user put weird shit
        if self.active not in self.themes:
            self.active = "default"

    def _extract_block(self, text, name):
        start = text.find(name)
        if start == -1:
            return None

        start_brace = text.find("{", start)
        if start_brace == -1:
            return None

        brace_count = 0
        i = start_brace
        while i < len(text):
            if text[i] == "{":
                brace_count += 1
            elif text[i] == "}":
                brace_count -= 1
                if brace_count == 0:
                    return text[start_brace:i+1]
            i += 1
        return None

    def _extract_assignment(self, text, name):
        for line in text.splitlines():
            if line.strip().startswith(name):
                if "=" in line:
                    return line.split("=", 1)[1].strip()
        return None

    def get_colour(self, key):
        theme = self.themes.get(self.active, {})
        default = self.themes.get("default", {})
        colour_name = theme.get(key) or default.get(key)
        
        try:
            return getattr(Colour, colour_name, Colour.RESET)
        except TypeError:
            cprint("error", f"Value '{key}', is NOT valid!")


    def get_theme(self):
        return self.themes.get(self.active, {})





class KeypairParser:
    def __init__(self, filepath, limit=300):
        self.filepath = filepath
        self.limit = limit
        self.keypairs = []
        self.load()

    def load(self):
        if not os.path.exists(self.filepath):
            print(f"{timestamp} No keypair file found, creating a new one...")
            os.makedirs(os.path.dirname(self.filepath), exist_ok=True)
            self.save()
            return
        try:
            with open(self.filepath, "r") as f:
                self.keypairs = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            print(f"{timestamp} Keypair file corrupted or empty, resetting...")
            self.keypairs = []
            self.save()

    def save(self):
        with open(self.filepath, "w") as f:
            json.dump(self.keypairs[-self.limit:], f, indent=4)

    def append_keypair(self, keypair_dict):
        self.keypairs.append(keypair_dict)
        self.save()

    def delete_keypair(self, index):
        if 0 <= index < len(self.keypairs):
            del self.keypairs[index]
            self.save()

    def get_all(self):
        return self.keypairs

class MessageParser:
    def __init__(self, filepath, limit=300):
        self.filepath = filepath
        self.limit = limit
        self.messages = []
        self.load()

    def load(self):
        if not os.path.exists(self.filepath):
            print(f"{timestamp} No message file found, creating a new one...")
            os.makedirs(os.path.dirname(self.filepath), exist_ok=True)
            self.save()
            return
        try:
            with open(self.filepath, "r") as f:
                self.messages = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            print(f"{timestamp} Message file corrupted or empty, resetting...")
            self.messages = []
            self.save()

    def save(self):
        with open(self.filepath, "w") as f:
            json.dump(self.messages[-self.limit:], f, indent=4)

    def append_message(self, msg_dict):
        self.messages.append(msg_dict)
        self.save()

    def delete_message(self, index):
        if 0 <= index < len(self.messages):
            del self.messages[index]
            self.save()

    def get_all(self):
        return self.messages

class ContactParser:
    def __init__(self, filepath, limit=300):
        self.filepath = filepath
        self.limit = limit
        self.contacts = []
        self.load()

    def load(self):
        if not os.path.exists(self.filepath):
            print(f"{timestamp} No contact file found, creating a new one...")
            os.makedirs(os.path.dirname(self.filepath), exist_ok=True)
            self.save()
            return
        try:
            with open(self.filepath, "r") as f:
                self.contacts = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            print(f"{timestamp} Contact file corrupted or empty, resetting...")
            self.contacts = []
            self.save()

    def save(self):
        with open(self.filepath, "w") as f:
            json.dump(self.contacts[-self.limit:], f, indent=4)

    def append_contact(self, contact_dict):
        self.contacts.append(contact_dict)
        self.save()

    def delete_contact(self, index):
        if 0 <= index < len(self.contacts):
            del self.contacts[index]
            self.save()

    def get_all(self):
        return self.contacts
