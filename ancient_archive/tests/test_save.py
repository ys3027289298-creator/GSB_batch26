import json
import os
import shutil
import tempfile
import unittest

import save


def sample_state():
    return {
        "queue": ["典籍甲", "典籍乙"],
        "count": 7,
        "balance": 60,
        "next_id": 42,
        "locked": False,
        "used": 3,
        "cap": 9,
    }


class TestSave(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.old_dir = save.SAVE_DIR
        save.SAVE_DIR = self.tmp

    def tearDown(self):
        save.SAVE_DIR = self.old_dir
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_pause_resume_roundtrip(self):
        state = sample_state()
        save.save_game(state, 0)
        restored = save.load_game(0)
        self.assertEqual(restored, state)

    def test_load_is_idempotent_no_skip(self):
        state = sample_state()
        save.save_game(state, 0)
        first = save.load_game(0)
        second = save.load_game(0)
        self.assertEqual(first, second)
        self.assertEqual(second["next_id"], 42)
        self.assertEqual(second["count"], 7)

    def test_load_does_not_mutate_caller_state(self):
        state = sample_state()
        snapshot = json.loads(json.dumps(state))
        save.save_game(state, 0)
        save.load_game(0)
        self.assertEqual(state, snapshot)

    def test_missing_slot_returns_none(self):
        self.assertIsNone(save.load_game(99))

    def test_corrupted_save_returns_none_and_backups(self):
        save.save_game(sample_state(), 1)
        path = save._slot_path(1)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write("{not valid json")
        self.assertIsNone(save.load_game(1))
        self.assertFalse(os.path.exists(path))
        self.assertTrue(os.path.exists(path + ".corrupt"))

    def test_tampered_checksum_rejected(self):
        save.save_game(sample_state(), 2)
        path = save._slot_path(2)
        with open(path, "r", encoding="utf-8") as fh:
            envelope = json.load(fh)
        envelope["state"]["balance"] = 999999
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(envelope, fh)
        self.assertIsNone(save.load_game(2))

    def test_slots_stay_contiguous(self):
        self.assertEqual(save.next_slot(), 0)
        save.save_game(sample_state(), save.next_slot())
        self.assertEqual(save.next_slot(), 1)
        save.save_game(sample_state(), save.next_slot())
        self.assertEqual(save.list_slots(), [0, 1])

    def test_overwrite_same_slot(self):
        save.save_game(sample_state(), 0)
        newer = sample_state()
        newer["count"] = 100
        save.save_game(newer, 0)
        self.assertEqual(save.load_game(0)["count"], 100)
        self.assertEqual(save.list_slots(), [0])


if __name__ == "__main__":
    unittest.main()
