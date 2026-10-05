import os
import tempfile
import unittest

import world


SCRIPT = [
    ("add_timeline", ("alpha",)),
    ("add_timeline", ("beta",)),
    ("add_timeline", ("alpha",)),
    ("schedule_event", ("alpha", "rift storm")),
    ("schedule_event", ("beta", "echo")),
    ("schedule_event", ("alpha", "surge")),
    ("enter_rift", ("scout",)),
    ("jump", ("alpha",)),
    ("lock", ()),
    ("jump", ("beta",)),
    ("unlock", ()),
    ("view_event", (1,)),
    ("repair_event", ()),
    ("repair_event", ()),
    ("describe_timeline", ("alpha",)),
]


def run_script(script, save_path=None, load_at=None):
    state = world.new_game()
    outputs = []
    for index, (op, args) in enumerate(script):
        if load_at is not None and index == load_at:
            world.save_game(state, save_path)
            state = world.load_game(save_path)
        outputs.append(getattr(world, op)(state, *args))
    return state, outputs


class TestWorld(unittest.TestCase):
    def test_add_timeline_rejects_duplicates(self):
        state = world.new_game()
        self.assertTrue(world.add_timeline(state, "alpha"))
        self.assertFalse(world.add_timeline(state, "alpha"))
        self.assertEqual(list(state["timelines"]), ["alpha"])

    def test_rift_rejects_entry_when_full(self):
        state = world.new_game()
        for index in range(state["rift_capacity"]):
            self.assertTrue(world.enter_rift(state, "t%d" % index))
        self.assertFalse(world.enter_rift(state, "extra"))
        self.assertEqual(len(state["rift_occupants"]), state["rift_capacity"])

    def test_empty_timeline_describe_returns_none(self):
        state = world.new_game()
        world.add_timeline(state, "empty_line")
        self.assertIsNone(world.describe_timeline(state, "empty_line"))
        self.assertIsNone(world.describe_timeline(state, "missing"))

    def test_repair_picks_earliest_event(self):
        state = world.new_game()
        world.add_timeline(state, "alpha")
        first = world.schedule_event(state, "alpha", "early")
        world.schedule_event(state, "alpha", "late")
        self.assertEqual(world.repair_event(state), first)
        self.assertNotIn(first, state["events"])

    def test_locked_timeline_blocks_jump(self):
        state = world.new_game()
        world.add_timeline(state, "beta")
        world.lock(state)
        self.assertFalse(world.jump(state, "beta"))
        self.assertEqual(state["location"], "prime")
        world.unlock(state)
        self.assertTrue(world.jump(state, "beta"))
        self.assertEqual(state["location"], "beta")

    def test_view_event_does_not_delete(self):
        state = world.new_game()
        world.add_timeline(state, "alpha")
        event_id = world.schedule_event(state, "alpha", "storm")
        record = world.view_event(state, event_id)
        self.assertIsNotNone(record)
        self.assertEqual(record["text"], "storm")
        self.assertIn(event_id, state["events"])

    def test_repair_grants_full_coins(self):
        state = world.new_game()
        world.add_timeline(state, "alpha")
        world.schedule_event(state, "alpha", "storm")
        world.repair_event(state)
        self.assertEqual(state["coins"], world.REPAIR_REWARD)

    def test_repair_counts_once(self):
        state = world.new_game()
        world.add_timeline(state, "alpha")
        world.schedule_event(state, "alpha", "one")
        world.repair_event(state)
        self.assertEqual(state["repairs"], 1)
        self.assertIsNone(world.repair_event(state))
        self.assertEqual(state["repairs"], 1)

    def test_reset_clears_everything(self):
        state = world.new_game()
        world.add_timeline(state, "alpha")
        world.schedule_event(state, "alpha", "storm")
        world.enter_rift(state, "scout")
        world.lock(state)
        world.repair_event(state)
        world.reset(state)
        self.assertEqual(state, world.new_game())

    def test_load_does_not_skip_ids(self):
        state = world.new_game()
        world.add_timeline(state, "alpha")
        world.schedule_event(state, "alpha", "one")
        world.schedule_event(state, "alpha", "two")
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "save.json")
            world.save_game(state, path)
            loaded = world.load_game(path)
        self.assertEqual(loaded["next_event_id"], 3)
        self.assertEqual(world.schedule_event(loaded, "alpha", "three"), 3)

    def test_save_load_replay_is_deterministic(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "save.json")
            base_state, base_outputs = run_script(SCRIPT)
            for _ in range(3):
                direct_state, direct_outputs = run_script(SCRIPT)
                self.assertEqual(direct_outputs, base_outputs)
                self.assertEqual(direct_state, base_state)
                loaded_state, loaded_outputs = run_script(SCRIPT, path, load_at=7)
                self.assertEqual(loaded_outputs, base_outputs)
                self.assertEqual(loaded_state, base_state)


if __name__ == "__main__":
    unittest.main()
