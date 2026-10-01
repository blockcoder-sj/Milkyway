"""Small, spawn-safe fake workers for local secret delivery contract checks.

Keeping targets outside the test module prevents a child from importing FastAPI
and the whole credential broker just to send a synthetic byte string. Production
workers, deadlines, pipe bounds and child cleanup are unchanged.
"""

import time


def stalled_identity_or_refresh(sender, settings, purpose):
    time.sleep(30)


def bounded_test_release(sender, settings, purpose):
    sender.send_bytes(b"sk-test-release-abcdefghijklmnopqrstuvwxyz0123456789")
    sender.close()


def oversized_test_release(sender, settings, purpose):
    sender.send_bytes(b"x" * 5000)
    sender.close()
