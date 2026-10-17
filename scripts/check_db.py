#!/usr/bin/env python3
"""
scripts/check_db.py — prove the FalkorDB credentials in .env work, safely.

Prints NEVER include the password. Reports which combination authenticates so
you can paste the correct pair back into .env.

Why this exists: the FalkorDB Cloud console showed a connection string, and two
things in it are easy to get subtly wrong — the username (FalkorDB Cloud often
uses the literal "default" ACL user rather than your account email) and the
password. A wrong guess produces an identical WRONGPASS either way, so guessing
in the REPL tells you nothing.

Run:  python scripts/check_db.py
"""

from __future__ import annotations

import os
import socket
import sys

from dotenv import load_dotenv

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(ROOT, ".env"))

HOST = os.getenv("FALKORDB_HOST", "")
PORT = int(os.getenv("FALKORDB_PORT", "6379"))
USER = os.getenv("FALKORDB_USERNAME", "")
PASSWORD = os.getenv("FALKORDB_PASSWORD", "")
SSL = os.getenv("FALKORDB_SSL", "").strip().lower() in ("1", "true", "yes", "on")


def resp(sock: socket.socket, cmd: str) -> str:
    sock.sendall(cmd.encode())
    return sock.recv(512).decode(errors="replace").strip()


def attempt(label: str, username: str, password: str) -> bool:
    if not username or not password:
        print(f"  {label:<28} skipped (missing value)")
        return False
    try:
        s = socket.create_connection((HOST, PORT), timeout=8)
    except Exception as exc:
        print(f"  {label:<28} TCP FAILED: {type(exc).__name__}")
        return False
    try:
        pw = password.replace("\\", "\\\\").replace('"', '\\"')
        out = resp(s, f'AUTH "{username}" "{pw}"\r\n')
        if out.startswith("-ERR") or "WRONGPASS" in out or "NOAUTH" in out:
            print(f"  {label:<28} rejected  ({out[:44]})")
            return False
        print(f"  {label:<28} AUTHENTICATED")
        if SSL:
            print(f"  {label:<28} note: FALKORDB_SSL=true but this port answered "
                  f"plaintext. Set it to false.")
        else:
            ping = resp(s, "PING\r\n")
            print(f"  {label:<28} PING -> {ping[:20]}")
        return True
    finally:
        s.close()


def main() -> int:
    print(f"host={HOST}")
    print(f"port={PORT}")
    print(f"ssl={SSL}")
    print(f"graph={os.getenv('FALKORDB_GRAPH', '(unset)')}")
    print(f"username in .env = {USER or '(empty)'}")
    print(f"password in .env = {'set, ' + str(len(PASSWORD)) + ' chars' if PASSWORD else '(EMPTY)'}")
    print("\nTrying combinations:")

    candidates = [("username from .env", USER, PASSWORD),
                  ("literal 'default'", "default", PASSWORD)]

    ok = False
    for label, u, p in candidates:
        if attempt(label, u, p):
            ok = True
            if u != USER:
                print(f"\n  -> use FALKORDB_USERNAME={u} in .env")
            break

    if not ok:
        print("\n  Nothing authenticated. The password is wrong.")
        print("  Copy it again from the FalkorDB console, Connect panel on the")
        print("  instance — the connection string it shows contains both the")
        print("  username and the password. Paste the password into .env only;")
        print("  do not send it in chat.")
        return 1

    print("\nOK — credentials work. Next: python scripts/load.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
