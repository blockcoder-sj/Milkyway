"""Cold macOS cloud-file reads must not look like concurrent content changes."""
from pathlib import Path
from types import SimpleNamespace
import stat
import tempfile
import unittest
from unittest.mock import patch

from cloud_app.bounded_io import FileBudgetExceeded, FileReadBudget, read_bounded_file


DATALESS = 0x40000000


def metadata(original, *, flags=0, mtime_delta=0, size=None):
    return SimpleNamespace(
        st_mode=original.st_mode, st_dev=original.st_dev, st_ino=original.st_ino,
        st_size=original.st_size if size is None else size,
        st_mtime_ns=original.st_mtime_ns + mtime_delta, st_flags=flags,
    )


class CloudPlaceholderReadTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.path = Path(directory.name) / "public.json"
        self.payload = b'{"items": [1, 2, 3]}'
        self.path.write_bytes(self.payload)
        self.original = self.path.stat()

    def test_first_download_mtime_change_is_materialized_before_capture(self):
        placeholder = metadata(self.original, flags=DATALESS)
        hydrated = metadata(self.original, mtime_delta=64)
        budget = FileReadBudget(len(self.payload) + 1)
        with patch.object(stat, "SF_DATALESS", DATALESS, create=True), patch(
            "cloud_app.bounded_io.os.fstat", side_effect=[placeholder, hydrated, hydrated]
        ):
            self.assertEqual(read_bounded_file(
                self.path, maximum_bytes=len(self.payload), budget=budget
            ), self.payload)
        self.assertEqual(budget.remaining, 0)

    def test_real_change_after_materialization_is_still_rejected(self):
        placeholder = metadata(self.original, flags=DATALESS)
        hydrated = metadata(self.original, mtime_delta=64)
        changed = metadata(self.original, mtime_delta=65)
        with patch.object(stat, "SF_DATALESS", DATALESS, create=True), patch(
            "cloud_app.bounded_io.os.fstat", side_effect=[placeholder, hydrated, changed]
        ):
            with self.assertRaisesRegex(ValueError, "changed"):
                read_bounded_file(self.path, maximum_bytes=100)

    def test_materialization_does_not_read_an_already_oversized_file(self):
        placeholder = metadata(self.original, flags=DATALESS)
        with patch.object(stat, "SF_DATALESS", DATALESS, create=True), patch(
            "cloud_app.bounded_io.os.fstat", return_value=placeholder
        ), patch("cloud_app.bounded_io.os.read") as read:
            with self.assertRaisesRegex(ValueError, "size"):
                read_bounded_file(self.path, maximum_bytes=1)
            read.assert_not_called()

    def test_size_is_checked_again_after_download(self):
        placeholder = metadata(self.original, flags=DATALESS)
        grown = metadata(self.original, mtime_delta=64, size=101)
        with patch.object(stat, "SF_DATALESS", DATALESS, create=True), patch(
            "cloud_app.bounded_io.os.fstat", side_effect=[placeholder, grown]
        ):
            with self.assertRaisesRegex(ValueError, "size"):
                read_bounded_file(self.path, maximum_bytes=100)

    def test_probe_respects_the_aggregate_budget_before_reading(self):
        placeholder = metadata(self.original, flags=DATALESS)
        with patch.object(stat, "SF_DATALESS", DATALESS, create=True), patch(
            "cloud_app.bounded_io.os.fstat", return_value=placeholder
        ), patch("cloud_app.bounded_io.os.read") as read:
            with self.assertRaises(FileBudgetExceeded):
                read_bounded_file(self.path, maximum_bytes=100, budget=FileReadBudget(0))
            read.assert_not_called()

    def test_local_file_needs_no_extra_budget_or_download_probe(self):
        local = metadata(self.original)
        budget = FileReadBudget(len(self.payload))
        with patch("cloud_app.bounded_io.os.fstat", return_value=local), patch(
            "cloud_app.bounded_io.os.read"
        ) as probe:
            self.assertEqual(read_bounded_file(
                self.path, maximum_bytes=len(self.payload), budget=budget
            ), self.payload)
            probe.assert_not_called()
        self.assertEqual(budget.remaining, 0)


if __name__ == "__main__":
    unittest.main()
