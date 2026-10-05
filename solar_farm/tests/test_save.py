import json
import os
import tempfile
import unittest

import save


class TestSolarFarm(unittest.TestCase):
    def setUp(self):
        self.state = save.new_game()
        save.add_array(self.state, "A", 2)

    def test_duplicate_panel_rejected(self):
        save.add_panel(self.state, "A", 1)
        with self.assertRaises(save.InvalidInputError):
            save.add_panel(self.state, "A", 1)
        self.assertEqual(save.array_panels(self.state, "A"), [1])

    def test_full_array_rejected_without_id_skip(self):
        save.add_panel(self.state, "A")
        save.add_panel(self.state, "A")
        with self.assertRaises(save.CapacityError):
            save.add_panel(self.state, "A")
        self.assertEqual(self.state["next_id"], 3)
        save.add_array(self.state, "B", 1)
        self.assertEqual(save.add_panel(self.state, "B"), 3)

    def test_empty_array_returns_empty_not_text(self):
        self.assertEqual(save.array_panels(self.state, "A"), [])
        self.assertIsNone(save.calibrate_next(self.state))

    def test_first_arrived_panel_calibrated_first(self):
        save.add_panel(self.state, "A", 10)
        save.add_panel(self.state, "A", 20)
        self.assertEqual(save.calibrate_next(self.state), 10)
        self.assertEqual(save.calibrate_next(self.state), 20)

    def test_locked_discharge_rejected(self):
        save.charge(self.state, 30)
        save.lock(self.state)
        with self.assertRaises(save.StateLockedError):
            save.discharge(self.state, 10)
        self.assertEqual(self.state["storage"], 30)
        save.unlock(self.state)
        self.assertEqual(save.discharge(self.state, 10), 10)

    def test_view_panel_does_not_delete(self):
        save.add_panel(self.state, "A", 7)
        panel = save.view_panel(self.state, 7)
        self.assertEqual(panel["id"], 7)
        self.assertIn(7, self.state["panels"])
        self.assertEqual(save.array_panels(self.state, "A"), [7])

    def test_storage_remaining_not_under_counted(self):
        self.assertEqual(save.storage_remaining(self.state), 100)
        save.charge(self.state, 40)
        self.assertEqual(save.storage_remaining(self.state), 60)
        with self.assertRaises(save.CapacityError):
            save.charge(self.state, 61)

    def test_single_discharge_not_counted_twice(self):
        save.charge(self.state, 50)
        self.assertEqual(save.discharge(self.state, 20, event_id="e1"), 20)
        self.assertEqual(save.discharge(self.state, 20, event_id="e1"), 0)
        self.assertEqual(self.state["storage"], 30)
        self.assertEqual(self.state["discharged_events"], ["e1"])

    def test_reset_clears_everything(self):
        save.add_panel(self.state, "A")
        save.charge(self.state, 10)
        save.lock(self.state)
        save.reset(self.state)
        fresh = save.new_game()
        self.assertEqual(self.state, fresh)

    def test_load_does_not_skip_ids(self):
        save.add_panel(self.state, "A")
        save.add_panel(self.state, "A")
        save.reset(self.state)
        save.add_array(self.state, "X", 5)
        save.add_panel(self.state, "X", 42)
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "save.json")
            save.save_game(self.state, path)
            loaded = save.load_game(path)
        self.assertEqual(loaded["next_id"], 43)
        self.assertEqual(save.add_panel(loaded, "X"), 43)

    def test_missing_and_corrupt_save_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            missing = os.path.join(tmp, "nope.json")
            with self.assertRaises(save.InvalidInputError):
                save.load_game(missing)
            corrupt = os.path.join(tmp, "bad.json")
            with open(corrupt, "w", encoding="utf-8") as fh:
                fh.write("{not json")
            with self.assertRaises(save.InvalidInputError):
                save.load_game(corrupt)

    def test_invalid_input_leaves_state_untouched(self):
        with self.assertRaises(save.InvalidInputError):
            save.add_panel(self.state, "A", object())
        with self.assertRaises(save.InvalidInputError):
            save.add_array(self.state, "Z", -3)
        self.assertEqual(self.state, save.new_game() | {"arrays": self.state["arrays"]})
        self.assertEqual(save.array_panels(self.state, "A"), [])

    def test_failure_types_are_distinct(self):
        for exc_type in (save.InvalidInputError, save.CapacityError,
                         save.StateLockedError):
            self.assertTrue(issubclass(exc_type, save.SolarFarmError))
        self.assertNotEqual(save.InvalidInputError, save.CapacityError)
        self.assertNotEqual(save.CapacityError, save.StateLockedError)


if __name__ == "__main__":
    unittest.main()
