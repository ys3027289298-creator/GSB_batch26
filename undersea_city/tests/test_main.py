import os
import tempfile
import unittest

import main


def find_section(state, name):
    for sec in state["sections"].values():
        if sec["name"] == name:
            return sec
    return None


class TestDispatch(unittest.TestCase):
    def setUp(self):
        self.state = main.new_game()

    def test_01_duplicate_section_rejected(self):
        self.assertIsNotNone(main.cmd_add(self.state, "A", 5))
        self.assertIsNone(main.cmd_add(self.state, "A", 5))
        self.assertEqual(len(self.state["sections"]), 1)

    def test_02_full_cabin_rejects_entry(self):
        main.cmd_add(self.state, "A", 3)
        self.assertTrue(main.cmd_enter(self.state, "A", 3))
        self.assertFalse(main.cmd_enter(self.state, "A", 1))
        self.assertEqual(find_section(self.state, "A")["occupants"], 3)

    def test_03_missing_section_view_returns_none(self):
        self.assertIsNone(main.cmd_view(self.state, "ghost"))

    def test_04_supplies_dispatched_fifo(self):
        main.cmd_add(self.state, "A", 10)
        sid = next(iter(self.state["sections"]))
        main.cmd_deliver(self.state, "A", 5)
        main.cmd_deliver(self.state, "A", 3)
        main.cmd_dispatch(self.state)
        self.assertEqual(self.state["delivered"][sid], [5, 3])
        self.assertEqual(self.state["queue"], [])

    def test_05_paused_dispatch_is_noop(self):
        main.cmd_add(self.state, "A", 10)
        main.cmd_deliver(self.state, "A", 5)
        main.cmd_pause(self.state)
        self.assertEqual(main.cmd_dispatch(self.state), 0)
        self.assertEqual(len(self.state["queue"]), 1)
        main.cmd_resume(self.state)
        self.assertEqual(main.cmd_dispatch(self.state), 5)

    def test_06_view_does_not_delete_section(self):
        main.cmd_add(self.state, "A", 5)
        main.cmd_view(self.state, "A")
        self.assertIsNotNone(find_section(self.state, "A"))

    def test_07_oxygen_counts_every_section(self):
        main.cmd_add(self.state, "A", 10)
        main.cmd_add(self.state, "B", 10)
        main.cmd_enter(self.state, "A", 3)
        main.cmd_enter(self.state, "B", 4)
        self.assertEqual(main.cmd_oxygen(self.state), 100 - (3 + 4) * 2)

    def test_08_dispatch_counted_once_per_round(self):
        main.cmd_add(self.state, "A", 10)
        main.cmd_deliver(self.state, "A", 5)
        main.cmd_deliver(self.state, "A", 3)
        main.cmd_deliver(self.state, "A", 2)
        main.cmd_dispatch(self.state)
        self.assertEqual(self.state["dispatch_count"], 1)

    def test_09_reset_returns_to_fresh_state(self):
        main.cmd_add(self.state, "A", 10)
        main.cmd_deliver(self.state, "A", 5)
        main.cmd_dispatch(self.state)
        main.cmd_pause(self.state)
        main.cmd_oxygen(self.state)
        main.cmd_reset(self.state)
        self.assertEqual(self.state, main.new_game())

    def test_10_load_preserves_id_sequence(self):
        main.cmd_add(self.state, "A", 5)
        main.cmd_add(self.state, "B", 5)
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "save.json")
            main.cmd_save(self.state, path)
            loaded = main.new_game()
            main.cmd_load(loaded, path)
            sid = main.cmd_add(loaded, "C", 5)
        self.assertEqual(sid, 3)


if __name__ == "__main__":
    unittest.main()
