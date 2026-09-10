"""Bounded readers for lower-trust files and HTTP response bodies."""

from __future__ import annotations

import json
import os
import stat
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


class ResponseTooLarge(ValueError):
    """The peer attempted to send more bytes than the endpoint permits."""


class FileBudgetExceeded(ValueError):
    """A file capture would exceed the caller's remaining read allowance."""


@dataclass
class FileReadBudget:
    remaining: int

    def reserve(self, size: int) -> None:
        if size < 0 or size > self.remaining:
            raise FileBudgetExceeded("input files exceed the aggregate byte limit")
        # Reserve before I/O. A failed read or later parse never refunds bytes.
        self.remaining -= size


def _declared_length(headers) -> int | None:
    value = headers.get("Content-Length") if headers is not None else None
    if value in {None, ""}:
        return None
    try:
        length = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError("response Content-Length is invalid") from exc
    if length < 0:
        raise ValueError("response Content-Length is invalid")
    return length


def _bounded_chunks(response, chunks: Iterable[bytes], maximum_bytes: int) -> bytes:
    if maximum_bytes < 1:
        raise ValueError("maximum_bytes must be positive")
    declared = _declared_length(getattr(response, "headers", None))
    if declared is not None and declared > maximum_bytes:
        response.close()
        raise ResponseTooLarge("response exceeds the allowed byte limit")
    payload = bytearray()
    for chunk in chunks:
        if not chunk:
            continue
        if len(payload) + len(chunk) > maximum_bytes:
            response.close()
            raise ResponseTooLarge("response exceeds the allowed byte limit")
        payload.extend(chunk)
    return bytes(payload)


def _decode_json(payload: bytes):
    if not payload:
        return {}
    try:
        return json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("response body is not valid UTF-8 JSON") from exc


def read_httpx_json(response, *, maximum_bytes: int):
    """Read an httpx streaming response without unbounded buffering."""

    return _decode_json(
        _bounded_chunks(response, response.iter_bytes(), maximum_bytes)
    )


def read_requests_json(response, *, maximum_bytes: int):
    """Read a requests streaming response without unbounded buffering."""

    try:
        return _decode_json(
            _bounded_chunks(
                response,
                response.iter_content(chunk_size=min(64 * 1024, maximum_bytes)),
                maximum_bytes,
            )
        )
    finally:
        response.close()


def read_requests_bytes(response, *, maximum_bytes: int) -> bytes:
    try:
        return _bounded_chunks(
            response,
            response.iter_content(chunk_size=min(64 * 1024, maximum_bytes)),
            maximum_bytes,
        )
    finally:
        response.close()


def read_bounded_file(
    path: Path | str,
    *,
    maximum_bytes: int,
    allow_empty: bool = False,
    budget: FileReadBudget | None = None,
) -> bytes:
    """Capture one regular-file generation through a no-follow descriptor."""

    path = Path(path)
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(path, flags)
    try:
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode):
            raise ValueError("input must be a regular file")
        minimum = 0 if allow_empty else 1
        if before.st_size < minimum or before.st_size > maximum_bytes:
            raise ValueError("input file size is outside the allowed range")
        if budget is not None:
            budget.reserve(before.st_size)
        with os.fdopen(descriptor, "rb", buffering=0, closefd=False) as handle:
            # Read only the reserved generation, even if the file grows now.
            payload = handle.read(before.st_size)
        after = os.fstat(descriptor)
    finally:
        os.close(descriptor)
    if (
        len(payload) != before.st_size
        or len(payload) > maximum_bytes
        or (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns)
        != (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns)
    ):
        raise ValueError("input file changed while it was being read")
    return payload


def read_bounded_text(path: Path | str, *, maximum_bytes: int) -> str:
    try:
        return read_bounded_file(path, maximum_bytes=maximum_bytes).decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError("input file is not valid UTF-8") from exc


def read_bounded_json(path: Path | str, *, maximum_bytes: int):
    try:
        return json.loads(read_bounded_text(path, maximum_bytes=maximum_bytes))
    except json.JSONDecodeError as exc:
        raise ValueError("input file is not valid JSON") from exc


def bounded_paths(paths: Iterable[Path | str], *, maximum_count: int) -> tuple[Path, ...]:
    """Materialize a glob/list only up to its explicit file-count budget."""

    result: list[Path] = []
    for raw in paths:
        result.append(Path(raw))
        if len(result) > maximum_count:
            raise ValueError("input file count exceeds the allowed limit")
    return tuple(result)
