"""Create a private PostgreSQL CA and server identity on an offline admin host.

Never copy ca.key to either runtime VM. Existing output is never overwritten.
"""

import argparse
import os
from pathlib import Path
import re
import subprocess


def create(output: Path, server_name: str) -> None:
    if (len(server_name) > 253 or not re.fullmatch(r"[A-Za-z0-9](?:[A-Za-z0-9.-]*[A-Za-z0-9])?", server_name)
            or any(not label or len(label) > 63 or label.startswith("-") or label.endswith("-") for label in server_name.split("."))):
        raise ValueError("Use the broker-visible private PostgreSQL DNS name")
    output.mkdir(mode=0o700, parents=False, exist_ok=False)
    previous = os.umask(0o077)
    try:
        def openssl(*arguments):
            subprocess.run(["openssl", *arguments], cwd=output, check=True, capture_output=True)

        (output / "ca.cnf").write_text("[req]\nprompt=no\ndistinguished_name=dn\nx509_extensions=ca\n[dn]\nCN=Milkyway PostgreSQL CA\n[ca]\nbasicConstraints=critical,CA:TRUE,pathlen:0\nkeyUsage=critical,keyCertSign,cRLSign\n")
        (output / "server.cnf").write_text("[req]\nprompt=no\ndistinguished_name=dn\n[dn]\nCN=" + server_name + "\n[server]\nbasicConstraints=critical,CA:FALSE\nkeyUsage=critical,digitalSignature,keyEncipherment\nextendedKeyUsage=serverAuth\nsubjectAltName=DNS:postgres,DNS:" + server_name + "\n")
        openssl("req", "-x509", "-newkey", "rsa:3072", "-nodes", "-days", "3650", "-config", "ca.cnf", "-keyout", "ca.key", "-out", "ca.crt")
        openssl("req", "-new", "-newkey", "rsa:3072", "-nodes", "-config", "server.cnf", "-keyout", "server.key", "-out", "server.csr")
        openssl("x509", "-req", "-in", "server.csr", "-CA", "ca.crt", "-CAkey", "ca.key", "-CAcreateserial", "-days", "365", "-extfile", "server.cnf", "-extensions", "server", "-out", "server.crt")
        openssl("verify", "-CAfile", "ca.crt", "server.crt")
        for name in ("ca.crt", "server.crt"):
            (output / name).chmod(0o444)
    finally:
        os.umask(previous)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--server-name", required=True)
    parser.add_argument("--output-dir", required=True, type=Path)
    arguments = parser.parse_args()
    create(arguments.output_dir, arguments.server_name)
    print("TLS material created. Keep ca.key offline; deploy only server.key, server.crt and ca.crt.")
