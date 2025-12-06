import os
import ast
import sys
import time
import json
import random
import hashlib
import platform
from datetime import datetime
import builtins

from core.parsers import ConfigurationParser
from core.parsers import UserConfigParser
from core.parsers import KeypairParser
from core.parsers import MessageParser
from core.parsers import ContactParser
from core.parsers import ThemeParser


from core.parsers import cprint
from core.cli import cli



ASCII = """

 ▄▄▄       ███▄    █ ▄▄▄█████▓ ██▓▓█████▄  ▒█████  ▄▄▄█████▓▓█████ 
▒████▄     ██ ▀█   █ ▓  ██▒ ▓▒▓██▒▒██▀ ██▌▒██▒  ██▒▓  ██▒ ▓▒▓█   ▀ 
▒██  ▀█▄  ▓██  ▀█ ██▒▒ ▓██░ ▒░▒██▒░██   █▌▒██░  ██▒▒ ▓██░ ▒░▒███   
░██▄▄▄▄██ ▓██▒  ▐▌██▒░ ▓██▓ ░ ░██░░▓█▄   ▌▒██   ██░░ ▓██▓ ░ ▒▓█  ▄ 
 ▓█   ▓██▒▒██░   ▓██░  ▒██▒ ░ ░██░░▒████▓ ░ ████▓▒░  ▒██▒ ░ ░▒████▒
 ▒▒   ▓▒█░░ ▒░   ▒ ▒   ▒ ░░   ░▓   ▒▒▓  ▒ ░ ▒░▒░▒░   ▒ ░░   ░░ ▒░ ░
  ▒   ▒▒ ░░ ░░   ░ ▒░    ░     ▒ ░ ░ ▒  ▒   ░ ▒ ▒░     ░     ░ ░  ░
  ░   ▒      ░   ░ ░   ░       ▒ ░ ░ ░  ░ ░ ░ ░ ▒    ░         ░   
      ░  ░         ░           ░     ░        ░ ░              ░  ░
"""






timestamp = datetime.now().strftime("[%Y-%m-%d - %H:%M:%S]")
def random_num():
    return random.randint(0, 90000000)

keypairs_file = "data/keypairs.json"
messages_file = "data/messages.json"
contacts_file = "data/contacts.json"

configuration_file = "data/conf.config"
user_config_file = "data/user.config"
themes_file = "data/themes.config"

frames = [
    """ """,
    """ """,
    """ """,
    """ """,
    """ """,
    """ """,
    """ """,
    """ """,
    """ """,
    """ """,
]

def open_animation():
    if platform.system() == "Windows":
        os.system("cls")
    else:
        os.system("clear")
    for frame in frames: # 7ish frames for 1 sec animation
        print(frame)
        time.sleep(0.15)
        if platform.system() == "Windows":
                os.system("cls")
        else:
            os.system("clear")

def load_client_config():
    cprint("info", f"{timestamp} Initialising configuration parser...")
    cfg = ConfigurationParser(configuration_file)

    cprint("info", f"{timestamp} Loading configuration...")
    print("\n")
    storing_messages = cfg.get("storing_messages")
    storing_keypairs = cfg.get("storing_keypairs")
    storing_contacts = cfg.get("storing_contacts")

    if storing_keypairs == True:
        cprint("success", f"{timestamp} Storing keypairs is turned on")
        cprint("info", f"{timestamp} Initialising Keypair parser")
        kpk = KeypairParser(keypairs_file)
        cprint("success", f"{timestamp} Keypair parser intitialised")
        number_of_stored_keypairs = cfg.get("number_of_saved_keypairs")
        cprint("warning", f"{timestamp} Storing the last {number_of_stored_keypairs} used keypairs.")
        print("\n")
    else:
        cprint("warning", f"{timestamp} Storing keypairs is turned off")
        print("\n")

    if storing_messages == True:
        cprint("success", f"{timestamp} Storing messages is turned on")
        cprint("info", f"{timestamp} Initialising Message parser")
        msg = MessageParser(messages_file)
        cprint("success", f"{timestamp} Message parser intitialised")
        number_of_stored_messages = cfg.get("number_of_saved_messages")
        cprint("warning", f"{timestamp} Storing the last {number_of_stored_messages} sent messages.")
        print("\n")
    else:
        print(f"{timestamp} Storing messages is turned off")
        print("\n")

    if storing_contacts == True:
        cprint("success", f"{timestamp} Storing contacts is turned on")
        cprint("info", f"{timestamp} Initialising Contact parser")
        ctb = ContactParser(contacts_file)
        cprint("success", f"{timestamp} Contact parser intitialised")
        number_of_stored_contacts = cfg.get("number_of_saved_contacts")
        cprint("warning", f"{timestamp} Storing the last {number_of_stored_contacts} contacts.")
        print("\n")
    else:
        print(f"{timestamp} Storing contacts is turned off")
        print("\n")

def load_user_config():
    cprint("info", f"{timestamp} Initialising user configuration parser...")
    ucfg = UserConfigParser(user_config_file)

    cprint("info", f"{timestamp} Loading user configuration...")
    cprint("info", f"{timestamp} Loading username...")
    print("\n")
    client_username = ucfg.get("username")

    
    cprint("banner", f"{timestamp} Welcome to Antidote {client_username}")
    print("\n")




def main():
    # open_animation()
    cprint("error", ASCII)
    load_client_config()
    load_user_config()
    cli()

if __name__ == "__main__":
    main()