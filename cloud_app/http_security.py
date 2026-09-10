"""HTTP controls that must run before FastAPI parses request bodies."""

from __future__ import annotations

import asyncio
import json


class RequestBodyLimitMiddleware:
    """Reject oversized fixed-length and streamed HTTP bodies before parsing."""

    def __init__(
        self,
        app,
        max_bytes: int,
        *,
        read_timeout_seconds: float = 15.0,
        max_messages: int = 64,
    ):
        self.app = app
        self.max_bytes = max(1, int(max_bytes))
        self.read_timeout_seconds = max(0.001, float(read_timeout_seconds))
        self.max_messages = max(1, int(max_messages))

    async def __call__(self, scope, receive, send):
        if scope.get("type") != "http":
            await self.app(scope, receive, send)
            return

        declared_lengths = []
        for name, raw_value in scope.get("headers", []):
            if name.lower() != b"content-length":
                continue
            try:
                declared_lengths.append(int(raw_value))
            except ValueError:
                await self._reject(send, 400, "Invalid Content-Length")
                return
        if len(set(declared_lengths)) > 1 or any(value < 0 for value in declared_lengths):
            await self._reject(send, 400, "Invalid Content-Length")
            return
        if declared_lengths and declared_lengths[0] > self.max_bytes:
            await self._reject(send, 413, "Request body too large")
            return

        messages = []
        received = 0
        deadline = asyncio.get_running_loop().time() + self.read_timeout_seconds
        while True:
            remaining = deadline - asyncio.get_running_loop().time()
            if remaining <= 0:
                await self._reject(send, 408, "Request body read timed out")
                return
            try:
                message = await asyncio.wait_for(receive(), timeout=remaining)
            except asyncio.TimeoutError:
                await self._reject(send, 408, "Request body read timed out")
                return
            messages.append(message)
            if len(messages) > self.max_messages:
                await self._reject(send, 400, "Too many request body chunks")
                return
            if message.get("type") == "http.disconnect":
                break
            if message.get("type") != "http.request":
                continue
            received += len(message.get("body", b""))
            if received > self.max_bytes:
                await self._reject(send, 413, "Request body too large")
                return
            if not message.get("more_body", False):
                break

        index = 0

        async def replay_receive():
            nonlocal index
            if index < len(messages):
                message = messages[index]
                index += 1
                return message
            # Once the buffered request is replayed, preserve the live receive
            # channel so streaming responses can observe http.disconnect.
            return await receive()

        await self.app(scope, replay_receive, send)

    @staticmethod
    async def _reject(send, status: int, detail: str) -> None:
        body = json.dumps({"detail": detail}, separators=(",", ":")).encode("utf-8")
        await send(
            {
                "type": "http.response.start",
                "status": status,
                "headers": [
                    (b"content-type", b"application/json"),
                    (b"content-length", str(len(body)).encode("ascii")),
                    (b"cache-control", b"no-store"),
                ],
            }
        )
        await send({"type": "http.response.body", "body": body})
