import unittest

import world


def dump(state):
    return world.save_game(state)


SCRIPT = [
    ("add_timeline", "alpha"),
    ("add_timeline", "beta"),
    ("add_timeline", "alpha"),
    ("enter", "rift-1"),
    ("jump", "beta"),
    ("enter", "rift-2"),
    ("lock",),
    ("jump", "alpha"),
    ("unlock",),
    ("jump", "alpha"),
    ("enter", "rift-3"),
    ("enter", "rift-4"),
    ("current",),
    ("view", 1),
    ("repair",),
    ("repair",),
    ("enter", "rift-5"),
    ("repair",),
]


class TestWorld(unittest.TestCase):
    def test_no_duplicate_timeline(self):
        state = world.new_game()
        self.assertTrue(world.add_timeline(state, "alpha"))
        self.assertFalse(world.add_timeline(state, "alpha"))
        self.assertEqual(state["timelines"], ["alpha"])

    def test_rift_full_rejects_entry(self):
        state = world.new_game()
        world.add_timeline(state, "alpha")
        ids = [world.enter_rift(state, "e%d" % i) for i in range(state["capacity"])]
        self.assertNotIn(None, ids)
        self.assertIsNone(world.enter_rift(state, "overflow"))
        self.assertEqual(len(state["events"]), state["capacity"])

    def test_empty_timeline_returns_none(self):
        state = world.new_game()
        world.add_timeline(state, "alpha")
        self.assertIsNone(world.current_event(state))

    def test_repair_picks_earliest_event(self):
        state = world.new_game()
        world.add_timeline(state, "alpha")
        late = world.enter_rift(state, "late", tick=9)
        early = world.enter_rift(state, "early", tick=1)
        self.assertEqual(world.repair(state), early)
        self.assertIn(late, state["events"])

    def test_locked_timeline_cannot_jump(self):
        state = world.new_game()
        world.add_timeline(state, "alpha")
        world.add_timeline(state, "beta")
        world.set_lock(state, True)
        self.assertFalse(world.jump(state, "beta"))
        self.assertEqual(state["current"], "alpha")
        world.set_lock(state, False)
        self.assertTrue(world.jump(state, "beta"))

    def test_view_event_does_not_delete(self):
        state = world.new_game()
        world.add_timeline(state, "alpha")
        event_id = world.enter_rift(state, "e")
        self.assertEqual(world.view_event(state, event_id)["id"], event_id)
        self.assertIn(event_id, state["events"])

    def test_repair_awards_full_coins(self):
        state = world.new_game()
        world.add_timeline(state, "alpha")
        world.enter_rift(state, "e")
        world.repair(state)
        self.assertEqual(state["coins"], world.REPAIR_REWARD)

    def test_single_repair_counts_once(self):
        state = world.new_game()
        world.add_timeline(state, "alpha")
        world.enter_rift(state, "e")
        world.repair(state)
        self.assertEqual(state["repairs"], 1)
        self.assertIsNone(world.repair(state))
        self.assertEqual(state["repairs"], 1)

    def test_reset_clears_everything(self):
        state = world.new_game()
        world.add_timeline(state, "alpha")
        world.enter_rift(state, "e")
        world.repair(state)
        world.reset(state)
        self.assertEqual(state, world.new_game())

    def test_load_preserves_next_id(self):
        state = world.new_game()
        world.add_timeline(state, "alpha")
        world.enter_rift(state, "e1")
        world.enter_rift(state, "e2")
        loaded = world.load_game(world.save_game(state))
        self.assertEqual(loaded["next_id"], state["next_id"])
        new_id = world.enter_rift(loaded, "e3")
        self.assertEqual(new_id, state["next_id"])
        self.assertNotIn(new_id, state["events"])

    def test_load_restores_int_event_keys(self):
        state = world.new_game()
        world.add_timeline(state, "alpha")
        event_id = world.enter_rift(state, "e")
        loaded = world.load_game(world.save_game(state))
        self.assertIn(event_id, loaded["events"])
        self.assertEqual(loaded["events"][event_id]["desc"], "e")

    def test_replay_is_deterministic(self):
        runs = []
        for _ in range(3):
            state = world.new_game()
            outputs = world.replay(state, SCRIPT)
            runs.append((outputs, dump(state)))
        self.assertEqual(runs[0], runs[1])
        self.assertEqual(runs[1], runs[2])

    def test_save_load_replay_matches_straight_run(self):
        straight = world.new_game()
        straight_outputs = world.replay(straight, SCRIPT)

        split = world.new_game()
        cut = 7
        head_outputs = world.replay(split, SCRIPT[:cut])
        restored = world.load_game(world.save_game(split))
        tail_outputs = world.replay(restored, SCRIPT[cut:])

        self.assertEqual(head_outputs + tail_outputs, straight_outputs)
        self.assertEqual(dump(restored), dump(straight))

    def test_reloaded_save_replays_identically(self):
        state = world.new_game()
        world.replay(state, SCRIPT)
        snapshot = world.save_game(state)
        for _ in range(2):
            loaded = world.load_game(snapshot)
            outputs = world.replay(loaded, SCRIPT)
            fresh = world.new_game()
            world.replay(fresh, SCRIPT)
            fresh_outputs = world.replay(fresh, SCRIPT)
            self.assertEqual(outputs, fresh_outputs)
            self.assertEqual(dump(loaded), dump(fresh))


if __name__ == "__main__":
    unittest.main()
