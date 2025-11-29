# Antidote  
<img src="src/docs/antidote.png" alt="Antidote Logo" width="300">

Antidote is a work in progress encryption tool with a simple UI for encrypting and decrypting messages locally.

# DISCLAIMER!
Antidote is currently a proof of concept I put together in about a month for a school project (powered by six energy drinks, a couple of cigs, and questionable life choices).
Do not treat it as a secure communication platform. It’s a learning project, not a military-grade cipher.

Use proper OPSEC. This comes with zero warranty, and I do not condone or endorse illegal or malicious activity.

## Why should you care?

Honestly? Because I don’t.  
Talk about aliens, send your Fortnite strats, confess your sins, whatever.  
Antidote makes sure nobody else is peeking.

This isn’t another messaging app.  
It’s a protest against forced identification and chat surveillance.  
No sign-ins. No phone numbers. No cloud.  
Just math and silicon.  


# About
Antidote currently uses very minimal encryption — mostly XOR operations. The goal of this project was to explore the basics of end-to-end encryption: generating keypairs, encrypting and decrypting data, and experimenting with secure routing systems like the Tor protocol. I wasn’t trying to reinvent Signal in a month — I don’t have the time, the resources, or the brain cells for that.

Antidote uses a custom, stripped-down version of the ed25519 algorithm to generate user keypairs.
Why ed25519?
I needed something simple, fast, and usable for generating user identifiers. ed25519 allows deriving a public key from a private key, which makes it ideal for integrating into a future desktop application. Private keys can be stored locally, and public keys can be derived quickly when needed.
These keypairs are intended to be single-use.

Antidote currently has zero external requirements — just a device that can run Python.
### Outline of the project:
```
antidote/
├── release/
│ ├── core/
│ │    ├─ __init__.py
│ │    ├─ cli.py
│ │    ├─ colours.py
│ │    ├─ ed25519.pu
│ │    ├─ encryption.py
│ │    ├─ parsers.py
│ │    └─ qrcode.py
│ ├── data/
│ │    ├─ conf.config
│ │    ├─ contacts.json
│ │    ├─ keypairs.json
│ │    ├─ messages.json
│ │    └─ user.config
│ ├── expirimental/         # work in progress
│ │    ├─ __init__.py
│ │    └─ networking.py     # tor networking
│ └ app.py                  # actuall cli client
│
├── src/
│ ├── core/
│ │    ├─ encryption.py
│ │    ├─ decryption.py
│ │    └─ ed25519.py
│ ├── network/              # work in progress
│ └── docs/                 # assets for README
│
├── README.md
├── LICENCE
├── .gitignore
└── requierments.txt
```



## Plans for the future
Future Plans

Right now, Antidote has a basic CLI and simple encryption logic with some messaging-app features.
Future work includes:

Implementing Tor-based networking  
Designing a handshake system that lets users swap keypairs for every message while staying in the same “tunnel”  
Replacing XOR “encryption” with a real, secure algorithm  
Possibly building a desktop GUI if the project grows

## Usage guide:

1. Download the release folder from the repo.

2. (Optional) Move it somewhere private or secure.

3. Install Python if you haven’t already:
    https://www.python.org/downloads/

4. Run app.py.

Thats it.

These are all of the commands that are currently implemented into the antidote client:
```
    "help" -> returns all commands
    "npair" -> generates a new keypair
    "econf" -> edit client configuration
    "euconf" -> edit user configuration
    "encrypt" -> encrypt a message
    "dcrypt" -> decrypt a message
    "tmsg" -> makes a test message

    "kpshow" -> shows saved keypairs
    "kpimport" -> import a keypair or public key
    "kpexport" -> export a keypair or public key
    "kpdel" -> delete a saved keypair

    "msgshow" -> shows saved messages
    "msgdel" -> delete a saved message

    "ctshow" -> shows saved contacts
    "ctadd" -> add a new contact
    "ctremove" -> remove a saved contact
    "ctupdate" -> update a saved contact

    "backup" -> export all data to a backup file
    "restore" -> restore data from a backup file
    "clear" -> wipe all stored data (requires confirmation)

    "version" -> show tool version information
    "config" -> show combined configuration summary
    "path" -> show storage/config directories
    "ping" -> send an encrypted ping to a contact

    "debug" -> toggle verbose debug logging
    "hexdump" -> display raw bytes of a given file/key/message
    "benchmark" -> test encryption/decryption performance

    "exit" -> exit the program
    "quit" -> exit the program

```

# Patchnotes:

