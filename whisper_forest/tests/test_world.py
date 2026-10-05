import os
import tempfile
import unittest

import world


class TestWhisperForest(unittest.TestCase):
    def setUp(self):
        self.state = world.new_game()

    def test_1_duplicate_echo_triggers_once(self):
        self.assertTrue(world.trigger_echo(self.state, "e1"))
        mana = self.state["mana"]
        self.assertFalse(world.trigger_echo(self.state, "e1"))
        self.assertEqual(self.state["mana"], mana)

    def test_2_full_glade_rejects_entry(self):
        self.assertTrue(world.enter_glade(self.state, "g2"))
        self.assertFalse(world.enter_glade(self.state, "g2"))

    def test_3_empty_bag_text(self):
        self.assertEqual(world.inventory_text(self.state), world.EMPTY_BAG_TEXT)
        world.trigger_echo(self.state, "e1")
        world.collect_echo(self.state, "e1")
        self.assertIn("风的低语", world.inventory_text(self.state))

    def test_4_first_arrival_does_not_collect(self):
        world.enter_glade(self.state, "g1")
        self.assertTrue(self.state["triggered"]["e1"])
        self.assertEqual(self.state["collected"], [])
        self.assertEqual(self.state["bag"], [])

    def test_5_locked_echo_does_not_trigger(self):
        self.assertFalse(world.trigger_echo(self.state, "e2"))
        self.assertNotIn("e2", self.state["triggered"])
        mana = self.state["mana"]
        self.assertTrue(world.unlock_echo(self.state, "e2"))
        self.assertTrue(world.trigger_echo(self.state, "e2"))
        self.assertEqual(self.state["mana"], mana - 5)

    def test_6_view_echo_does_not_delete(self):
        info = world.view_echo(self.state, "e1")
        self.assertEqual(info["name"], "风的低语")
        self.assertIn("e1", self.state["echoes"])
        world.view_echo(self.state, "e1")
        world.view_echo(self.state, "e1")
        self.assertEqual(set(self.state["echoes"]), {"e1", "e2", "e3"})

    def test_7_mana_cost_exact(self):
        self.state["mana"] = 3
        self.assertTrue(world.trigger_echo(self.state, "e1"))
        self.assertEqual(self.state["mana"], 0)
        self.assertFalse(world.trigger_echo(self.state, "e3"))
        self.assertEqual(self.state["mana"], 0)

    def test_8_single_collection_counts_once(self):
        world.trigger_echo(self.state, "e1")
        self.assertTrue(world.collect_echo(self.state, "e1"))
        self.assertFalse(world.collect_echo(self.state, "e1"))
        self.assertEqual(len(self.state["bag"]), 1)
        self.assertEqual(self.state["collected"], ["e1"])

    def test_9_reset_clears_progress(self):
        world.trigger_echo(self.state, "e1")
        world.collect_echo(self.state, "e1")
        world.enter_glade(self.state, "g1")
        world.reset(self.state)
        self.assertEqual(self.state["mana"], world.START_MANA)
        self.assertEqual(self.state["triggered"], {})
        self.assertEqual(self.state["collected"], [])
        self.assertEqual(self.state["bag"], [])
        self.assertTrue(all(not v for v in self.state["visitors"].values()))
        self.assertEqual(set(self.state["echoes"]), {"e1", "e2", "e3"})

    def test_10_load_continues_ids_without_skip(self):
        world.trigger_echo(self.state, "e1")
        world.collect_echo(self.state, "e1")
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "save.json")
            world.save_game(self.state, path)
            loaded = world.load_game(path)
        self.assertIn("e1", loaded["collected"])
        new_id = world.add_echo(loaded, "夜的余响", "g1", 2)
        self.assertEqual(new_id, "e4")
        self.assertNotIn("e4", self.state["echoes"])
        loaded["next_echo_id"] = 1
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "save.json")
            world.save_game(loaded, path)
            reloaded = world.load_game(path)
        self.assertEqual(world.add_echo(reloaded, "雨的尾音", "g1", 1), "e5")

    def test_failed_action_leaves_no_partial_change(self):
        before = {
            "mana": self.state["mana"],
            "triggered": dict(self.state["triggered"]),
            "visitors": {k: list(v) for k, v in self.state["visitors"].items()},
        }
        world.enter_glade(self.state, "g2")
        world.enter_glade(self.state, "g2")
        self.assertFalse(world.trigger_echo(self.state, "e2"))
        self.assertFalse(world.collect_echo(self.state, "e3"))
        self.assertEqual(self.state["mana"], before["mana"])
        self.assertEqual(self.state["triggered"], before["triggered"])
        self.assertEqual(len(self.state["visitors"]["g2"]), 1)

    def test_load_continues_progress(self):
        world.trigger_echo(self.state, "e1")
        world.collect_echo(self.state, "e1")
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "save.json")
            world.save_game(self.state, path)
            loaded = world.load_game(path)
        self.assertEqual(loaded["mana"], self.state["mana"])
        self.assertTrue(loaded["triggered"]["e1"])
        self.assertTrue(world.trigger_echo(loaded, "e3"))
        self.assertTrue(world.collect_echo(loaded, "e3"))
        self.assertEqual(loaded["collected"], ["e1", "e3"])

    def test_full_bag_rejects_collection(self):
        for echo_id in ("e1",):
            world.trigger_echo(self.state, echo_id)
        self.state["bag"] = [{"id": "x%d" % i, "name": "x"} for i in range(world.BAG_CAPACITY)]
        self.assertFalse(world.collect_echo(self.state, "e1"))
        self.assertNotIn("e1", self.state["collected"])


if __name__ == "__main__":
    unittest.main()
