from datetime import datetime
from pathlib import Path
import tempfile
import unittest

from power_progress.countdown import CountdownEvent, CountdownStore, countdown_snapshot, parse_target


class CountdownTests(unittest.TestCase):
    def test_countdown_snapshot_future(self) -> None:
        now = datetime(2026, 5, 17, 10, 0, 0)
        target = datetime(2026, 5, 19, 12, 30, 10)

        snapshot = countdown_snapshot(target, now)

        self.assertFalse(snapshot.is_past)
        self.assertEqual(snapshot.days, 2)
        self.assertEqual(snapshot.hours, 2)
        self.assertEqual(snapshot.minutes, 30)
        self.assertEqual(snapshot.seconds, 10)
        self.assertEqual(snapshot.label(), "2D 2H 30M")

    def test_countdown_snapshot_past(self) -> None:
        now = datetime(2026, 5, 17, 10, 0, 0)
        target = datetime(2026, 5, 16, 8, 0, 0)

        snapshot = countdown_snapshot(target, now)

        self.assertTrue(snapshot.is_past)
        self.assertEqual(snapshot.days, 1)
        self.assertEqual(snapshot.hours, 2)
        self.assertEqual(snapshot.label(), "1D 2H 0M")

    def test_parse_target(self) -> None:
        self.assertEqual(parse_target("2026-05-17 20:30"), datetime(2026, 5, 17, 20, 30))

    def test_parse_target_rejects_invalid_format(self) -> None:
        with self.assertRaisesRegex(ValueError, "YYYY-MM-DD HH:MM"):
            parse_target("2026/05/17")

    def test_store_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            store = CountdownStore(path=Path(temp_dir) / "countdowns.json")
            event = CountdownEvent(title="发布", target=datetime(2026, 6, 1, 9, 0))

            store.save([event])
            loaded = store.load()

            self.assertEqual(len(loaded), 1)
            self.assertEqual(loaded[0].title, "发布")
            self.assertEqual(loaded[0].target, datetime(2026, 6, 1, 9, 0))


if __name__ == "__main__":
    unittest.main()
