"""Platform adapters for the single-owner Q-LAB classroom package."""
from contextlib import contextmanager
import csv
import io
import os
from pathlib import Path
import subprocess
import threading
import time

if os.name != "nt":
    from fcntl import flock, LOCK_EX, LOCK_NB, LOCK_UN
else:
    import msvcrt
    LOCK_EX, LOCK_NB, LOCK_UN = 2, 4, 8

    def flock(handle, operation):
        # Lock the same first byte in every process, including the backup worker.
        descriptor = handle if isinstance(handle, int) else handle.fileno()
        if not isinstance(handle, int):
            handle.flush()
        position = os.lseek(descriptor, 0, os.SEEK_CUR)
        try:
            if os.fstat(descriptor).st_size == 0 and not operation & LOCK_UN:
                os.write(descriptor, b"\0")
            os.lseek(descriptor, 0, os.SEEK_SET)
            mode = msvcrt.LK_UNLCK if operation & LOCK_UN else msvcrt.LK_NBLCK
            while True:
                try:
                    msvcrt.locking(descriptor, mode, 1)
                    break
                except OSError as error:
                    if error.errno not in {13, 36} or operation & LOCK_UN:
                        raise
                    if operation & LOCK_NB:
                        raise BlockingIOError("Local file is locked by another process") from error
                    time.sleep(.05)
        finally:
            os.lseek(descriptor, position, os.SEEK_SET)


def sync_directory(path):
    # Windows does not expose POSIX directory fsync. Files still use fsync and
    # atomic os.replace; keep the stronger directory guarantee on POSIX.
    if os.name == "nt":
        return
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def mode_is_private(metadata):
    # The native launcher applies a protected per-user Windows DACL before any
    # process starts. Windows st_mode does not represent that DACL.
    return os.name == "nt" or not metadata.st_mode & 0o077


def protect_directory(path):
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True, mode=0o700)
    if os.name != "nt":
        path.chmod(0o700)
        return
    identity = subprocess.run(["whoami", "/user", "/fo", "csv", "/nh"],
                              check=True, capture_output=True).stdout.decode(errors="replace")
    sid = next(csv.reader(io.StringIO(identity.strip())))[-1].strip()
    if not sid.startswith("S-1-") or any(char not in "S-0123456789" for char in sid):
        raise RuntimeError("Windows 사용자 권한을 확인하지 못했습니다")
    subprocess.run(["icacls", str(path), "/inheritance:r", "/grant:r",
                    "*" + sid + ":(OI)(CI)F"], check=True, capture_output=True)


@contextmanager
def windows_deadline(seconds):
    """Hard-stop a hung local worker; its supervisor restarts it.

    SQLite rolls back uncommitted transactions after the process exits. This
    retains a hard wall-time bound without emulating Unix signals on Windows.
    """
    def expired():
        os.write(2, b"Native worker deadline exceeded; supervisor will restart.\n")
        os._exit(124)
    timer = threading.Timer(max(0.001, float(seconds)), expired)
    timer.daemon = True
    timer.start()
    try:
        yield
    finally:
        timer.cancel()
