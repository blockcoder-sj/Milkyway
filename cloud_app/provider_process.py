"""Persistent, killable provider I/O process with bounded IPC and wall time."""

import json
import multiprocessing
import threading
import time


MAX_REQUEST_BYTES = 64 * 1024
MAX_RESPONSE_BYTES = 2 * 1024 * 1024


class ProviderOperationError(RuntimeError):
    def __init__(self, status_code, detail):
        super().__init__(detail)
        self.status_code, self.detail = status_code, detail


def _worker(connection, execute, configuration):
    import logging
    logging.disable(logging.CRITICAL)
    try:
        while True:
            payload = json.loads(connection.recv_bytes(MAX_REQUEST_BYTES))
            try:
                result = {"ok": execute(payload, configuration)}
            except Exception as exc:
                from fastapi import HTTPException
                if isinstance(exc, HTTPException) and exc.status_code in {401, 403, 409, 422, 429, 502, 503}:
                    result = {"error": {"status_code": exc.status_code, "detail": str(exc.detail)[:300]}}
                else:
                    result = {"error": {"status_code": 503, "detail": "provider operation unavailable"}}
            encoded = json.dumps(result, allow_nan=False, separators=(",", ":")).encode()
            if len(encoded) > MAX_RESPONSE_BYTES:
                encoded = b'{"error":"provider response exceeded limit"}'
            connection.send_bytes(encoded)
    except (EOFError, OSError, ValueError):
        pass
    finally:
        connection.close()


class ProviderProcess:
    """Keep provider OAuth state between successful calls, replace hung workers."""

    def __init__(self, execute):
        self.execute = execute
        self._lock = threading.Lock()
        self._process = self._connection = self._configuration = None

    def _stop(self):
        if self._process is not None:
            if self._process.is_alive():
                self._process.kill()
            self._process.join(timeout=1)
            self._process.close()
        if self._connection is not None:
            self._connection.close()
        self._process = self._connection = self._configuration = None

    def close(self):
        with self._lock:
            self._stop()

    def run(self, payload, configuration, *, deadline: float):
        # The request admission cap keeps send_bytes inside the pipe capacity.
        encoded = json.dumps(payload, allow_nan=False, separators=(",", ":")).encode()
        if len(encoded) > MAX_REQUEST_BYTES:
            raise ValueError("provider request exceeded limit")
        if not self._lock.acquire(timeout=max(0, deadline - time.monotonic())):
            raise TimeoutError("provider operation deadline was exhausted")
        try:
            if time.monotonic() >= deadline:
                raise TimeoutError("provider operation deadline was exhausted")
            if self._process is None or not self._process.is_alive() or self._configuration != configuration:
                self._stop()
                context = multiprocessing.get_context("spawn")
                parent, child = context.Pipe(duplex=True)
                process = context.Process(target=_worker, args=(child, self.execute, configuration), daemon=True)
                try:
                    process.start()
                except Exception:
                    parent.close()
                    child.close()
                    raise
                child.close()
                self._process, self._connection, self._configuration = process, parent, configuration
            sent = threading.Event()
            send_error = []
            connection = self._connection

            def send_request():
                try:
                    connection.send_bytes(encoded)
                except (OSError, EOFError) as exc:
                    send_error.append(exc)
                finally:
                    sent.set()

            sender = threading.Thread(target=send_request, daemon=True)
            sender.start()
            if not sent.wait(max(0, deadline - time.monotonic())):
                self._stop()  # Closing the child end unblocks the bounded send.
                sender.join(timeout=1)
                raise TimeoutError("provider operation deadline was exhausted")
            if send_error:
                raise RuntimeError("provider operation unavailable") from None
            if not self._connection.poll(max(0, deadline - time.monotonic())):
                raise TimeoutError("provider operation deadline was exhausted")
            result = json.loads(self._connection.recv_bytes(MAX_RESPONSE_BYTES))
            if time.monotonic() >= deadline:
                raise TimeoutError("provider operation deadline was exhausted")
            if isinstance(result, dict) and isinstance(result.get("error"), dict):
                error = result["error"]
                if error.get("status_code") in {401, 403, 409, 422, 429, 502, 503} and isinstance(error.get("detail"), str) and len(error["detail"]) <= 300:
                    raise ProviderOperationError(error["status_code"], error["detail"])
            if not isinstance(result, dict) or "ok" not in result:
                raise RuntimeError("provider operation unavailable")
            return result["ok"]
        except ProviderOperationError:
            # Ordinary rejections preserve OAuth state and admission counters.
            raise
        except Exception:
            self._stop()
            raise
        finally:
            self._lock.release()
