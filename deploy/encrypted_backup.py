"""Authenticated envelope encryption for PostgreSQL custom-format dumps."""

from __future__ import annotations

import argparse
import base64
import json
import os
import stat
import struct
from pathlib import Path

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes


MAGIC = b"MILKYWAY-ENCRYPTED-BACKUP-V1\n"
MAX_HEADER_BYTES = 16 * 1024
CHUNK_BYTES = 1024 * 1024
TAG_BYTES = 16


def _open_input(path: Path):
    descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    metadata = os.fstat(descriptor)
    if not stat.S_ISREG(metadata.st_mode) or metadata.st_size <= 0:
        os.close(descriptor)
        raise ValueError("backup input must be a non-empty regular file")
    return os.fdopen(descriptor, "rb"), metadata.st_size


def _open_output(path: Path):
    descriptor = os.open(
        path,
        os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0),
        0o600,
    )
    return os.fdopen(descriptor, "wb")


def _read_key(path: Path) -> bytes:
    descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    try:
        metadata = os.fstat(descriptor)
        if not stat.S_ISREG(metadata.st_mode) or not 1 <= metadata.st_size <= 64 * 1024:
            raise ValueError("backup key file is invalid")
        if metadata.st_mode & 0o077:
            raise ValueError("backup key file must have mode 0600 or stricter")
        with os.fdopen(descriptor, "rb", closefd=False) as handle:
            value = handle.read(64 * 1024 + 1)
    finally:
        os.close(descriptor)
    if len(value) != metadata.st_size:
        raise ValueError("backup key file changed while it was read")
    return value


def _oaep():
    return padding.OAEP(
        mgf=padding.MGF1(algorithm=hashes.SHA256()),
        algorithm=hashes.SHA256(),
        label=b"milkyway-postgres-backup-v1",
    )


def encrypt(input_path: Path, output_path: Path, public_key_path: Path) -> None:
    public_key = serialization.load_pem_public_key(_read_key(public_key_path))
    if not isinstance(public_key, rsa.RSAPublicKey) or public_key.key_size < 3072:
        raise ValueError("backup public key must be RSA 3072 bits or stronger")
    data_key = os.urandom(32)
    nonce = os.urandom(12)
    header = json.dumps(
        {
            "algorithm": "RSA-OAEP-SHA256+AES-256-GCM",
            "nonce": base64.b64encode(nonce).decode("ascii"),
            "wrapped_key": base64.b64encode(
                public_key.encrypt(data_key, _oaep())
            ).decode("ascii"),
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    if len(header) > MAX_HEADER_BYTES:
        raise ValueError("encrypted backup header is too large")
    authenticated_header = MAGIC + struct.pack(">I", len(header)) + header
    encryptor = Cipher(algorithms.AES(data_key), modes.GCM(nonce)).encryptor()
    encryptor.authenticate_additional_data(authenticated_header)
    source, _source_size = _open_input(input_path)
    output_created = False
    try:
        destination = _open_output(output_path)
        output_created = True
        with source, destination:
            destination.write(authenticated_header)
            while True:
                chunk = source.read(CHUNK_BYTES)
                if not chunk:
                    break
                destination.write(encryptor.update(chunk))
            destination.write(encryptor.finalize())
            destination.write(encryptor.tag)
            destination.flush()
            os.fsync(destination.fileno())
    except BaseException:
        if output_created:
            try:
                output_path.unlink()
            except FileNotFoundError:
                pass
        raise


def decrypt(input_path: Path, output_path: Path, private_key_path: Path) -> None:
    private_key = serialization.load_pem_private_key(
        _read_key(private_key_path), password=None
    )
    if not isinstance(private_key, rsa.RSAPrivateKey) or private_key.key_size < 3072:
        raise ValueError("backup private key must be RSA 3072 bits or stronger")
    source, source_size = _open_input(input_path)
    try:
        with source:
            magic = source.read(len(MAGIC))
            if magic != MAGIC:
                raise ValueError("encrypted backup magic is invalid")
            length_bytes = source.read(4)
            if len(length_bytes) != 4:
                raise ValueError("encrypted backup header is truncated")
            header_length = struct.unpack(">I", length_bytes)[0]
            if not 1 <= header_length <= MAX_HEADER_BYTES:
                raise ValueError("encrypted backup header length is invalid")
            header_bytes = source.read(header_length)
            if len(header_bytes) != header_length:
                raise ValueError("encrypted backup header is truncated")
            header = json.loads(header_bytes.decode("utf-8"))
            if header.get("algorithm") != "RSA-OAEP-SHA256+AES-256-GCM":
                raise ValueError("encrypted backup algorithm is unsupported")
            nonce = base64.b64decode(header["nonce"], validate=True)
            wrapped_key = base64.b64decode(header["wrapped_key"], validate=True)
            data_key = private_key.decrypt(wrapped_key, _oaep())
            ciphertext_start = len(MAGIC) + 4 + header_length
            ciphertext_bytes = source_size - ciphertext_start - TAG_BYTES
            if ciphertext_bytes <= 0:
                raise ValueError("encrypted backup ciphertext is empty")
            source.seek(source_size - TAG_BYTES)
            tag = source.read(TAG_BYTES)
            source.seek(ciphertext_start)
            decryptor = Cipher(algorithms.AES(data_key), modes.GCM(nonce, tag)).decryptor()
            decryptor.authenticate_additional_data(
                magic + length_bytes + header_bytes
            )
            remaining = ciphertext_bytes
            output_created = False
            try:
                destination = _open_output(output_path)
                output_created = True
                with destination:
                    while remaining:
                        chunk = source.read(min(CHUNK_BYTES, remaining))
                        if not chunk:
                            raise ValueError("encrypted backup ciphertext is truncated")
                        remaining -= len(chunk)
                        destination.write(decryptor.update(chunk))
                    destination.write(decryptor.finalize())
                    destination.flush()
                    os.fsync(destination.fileno())
            except BaseException:
                if output_created:
                    try:
                        output_path.unlink()
                    except FileNotFoundError:
                        pass
                raise
    finally:
        if not source.closed:
            source.close()


def main() -> int:
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest="command", required=True)
    encrypt_parser = commands.add_parser("encrypt")
    encrypt_parser.add_argument("--input", required=True, type=Path)
    encrypt_parser.add_argument("--output", required=True, type=Path)
    encrypt_parser.add_argument("--public-key", required=True, type=Path)
    decrypt_parser = commands.add_parser("decrypt")
    decrypt_parser.add_argument("--input", required=True, type=Path)
    decrypt_parser.add_argument("--output", required=True, type=Path)
    decrypt_parser.add_argument("--private-key", required=True, type=Path)
    args = parser.parse_args()
    if args.command == "encrypt":
        encrypt(args.input, args.output, args.public_key)
    else:
        decrypt(args.input, args.output, args.private_key)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
