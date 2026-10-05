import json
import unittest

import main


def fresh():
    return main.new_game()


class TestExploration(unittest.TestCase):
    def test_first_relic_registered(self):
        state = fresh()
        ok, _ = main.explore(state)
        self.assertTrue(ok)
        self.assertIn("1", state["registry"])
        self.assertEqual(state["last_found"], 1)

    def test_single_explore_counts_once(self):
        state = fresh()
        main.explore(state)
        self.assertEqual(state["explorations"], 1)
        self.assertEqual(state["stamina"], 9)

    def test_stamina_exact_one(self):
        state = fresh()
        state["stamina"] = 1
        ok, _ = main.explore(state)
        self.assertTrue(ok)
        self.assertEqual(state["stamina"], 0)
        ok, _ = main.explore(state)
        self.assertFalse(ok)
        self.assertEqual(state["stamina"], 0)
        self.assertEqual(state["explorations"], 1)

    def test_paused_explore_is_atomic_noop(self):
        state = fresh()
        main.explore(state)
        before = json.loads(main.to_save(state))
        main.set_paused(state, True)
        ok, _ = main.explore(state)
        self.assertFalse(ok)
        after = json.loads(main.to_save(state))
        self.assertEqual(after["stamina"], before["stamina"])
        self.assertEqual(after["explorations"], before["explorations"])
        self.assertEqual(after["next_id"], before["next_id"])
        self.assertEqual(after["registry"], before["registry"])


class TestBag(unittest.TestCase):
    def test_duplicate_pickup_rejected_and_state_unchanged(self):
        state = fresh()
        main.explore(state)
        main.pickup(state, 1)
        before = json.loads(main.to_save(state))
        ok, _ = main.pickup(state, 1)
        self.assertFalse(ok)
        self.assertEqual(state["bag"], [1])
        self.assertEqual(json.loads(main.to_save(state)), before)

    def test_pickup_when_full_rejected_and_state_unchanged(self):
        state = fresh()
        for _ in range(4):
            main.explore(state)
        for rid in (1, 2, 3):
            self.assertTrue(main.pickup(state, rid)[0])
        before = json.loads(main.to_save(state))
        ok, msg = main.pickup(state, 4)
        self.assertFalse(ok)
        self.assertIn("满", msg)
        self.assertEqual(state["bag"], [1, 2, 3])
        self.assertEqual(json.loads(main.to_save(state)), before)

    def test_empty_bag_returns_none(self):
        state = fresh()
        self.assertIsNone(main.view_bag(state))

    def test_inspect_never_removes(self):
        state = fresh()
        main.explore(state)
        main.pickup(state, 1)
        ok, msg = main.inspect(state, 1)
        self.assertTrue(ok)
        self.assertIn("石斧", msg)
        self.assertEqual(state["bag"], [1])

    def test_pickup_unknown_relic_rejected(self):
        state = fresh()
        ok, _ = main.pickup(state, 99)
        self.assertFalse(ok)
        self.assertEqual(state["bag"], [])


class TestResetAndSave(unittest.TestCase):
    def test_reset_clears_everything(self):
        state = fresh()
        main.explore(state)
        main.pickup(state, 1)
        main.set_paused(state, True)
        main.reset(state)
        self.assertEqual(state, main.new_game())

    def test_save_load_roundtrip_no_id_skip(self):
        state = fresh()
        for _ in range(5):
            main.explore(state)
        for rid in (1, 2, 3):
            main.pickup(state, rid)
        text = main.to_save(state)
        self.assertEqual(json.loads(text), state)
        restored = fresh()
        main.from_save(restored, text)
        self.assertEqual(restored, state)
        self.assertEqual(restored["next_id"], 6)
        ok, _ = main.explore(restored)
        self.assertTrue(ok)
        self.assertIn("6", restored["registry"])
        self.assertEqual(restored["next_id"], 7)

    def test_serialization_roundtrip_identity(self):
        state = fresh()
        main.explore(state)
        main.pickup(state, 1)
        main.set_paused(state, True)
        clone = fresh()
        main.from_save(clone, main.to_save(state))
        self.assertEqual(clone, state)


if __name__ == "__main__":
    unittest.main()
