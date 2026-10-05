import os
import tempfile
import unittest

import save


class TestRules(unittest.TestCase):
    def test_case_a(self):
        state = save.new_game()
        state.update({'src': 5, 'dst': 0})
        self.assertFalse(save.rule_a(state))
        self.assertEqual(state["src"], 5)
        self.assertEqual(state["dst"], 0)

    def test_case_a_consumes_when_enough(self):
        state = save.new_game()
        state.update({'src': 50, 'dst': 10})
        self.assertTrue(save.rule_a(state))
        self.assertEqual(state["src"], 40)
        self.assertEqual(state["dst"], 20)

    def test_case_b(self):
        state = save.new_game()
        state.update({'closed': True})
        self.assertFalse(save.rule_b(state))

    def test_case_c(self):
        state = save.new_game()
        state.update({'events': {}})
        self.assertTrue(save.rule_c(state))
        self.assertFalse(save.rule_c(state))

    def test_case_d(self):
        state = save.new_game()
        self.assertIsNone(save.rule_d(state))
        self.assertFalse(save.rule_d(state))

    def test_case_e(self):
        state = save.new_game()
        state.update({'events': {1: (5, 6), 2: (1, 2)}})
        self.assertEqual(save.rule_e(state), 2)
        self.assertEqual(state["events"], {1: (5, 6), 2: (1, 2)})

    def test_case_f(self):
        state = save.new_game()
        self.assertFalse(save.rule_f(state))

    def test_case_g(self):
        state = save.new_game()
        self.assertTrue(save.rule_g(state))
        self.assertFalse(save.rule_g(state))

    def test_case_h(self):
        state = save.new_game()
        state.update({'queue': []})
        state["queue"] = [1, 2]
        self.assertEqual(save.rule_h(state), 1)
        self.assertEqual(state["queue"], [2])

    def test_case_i(self):
        state = save.new_game()
        state.update({'items': []})
        state["items"] = [1]
        self.assertEqual(save.rule_i(state), 1)

    def test_case_j(self):
        state = save.new_game()
        state.update({'next_id': 1})
        state["next_id"] = 7
        self.assertEqual(save.rule_j(state), 7)
        self.assertEqual(state["next_id"], 8)


class TestCollectAndBay(unittest.TestCase):
    def test_collect_assigns_sequential_ids(self):
        state = save.new_game()
        self.assertEqual(save.collect_sample(state), 1)
        self.assertEqual(save.collect_sample(state), 2)
        self.assertEqual(save.rule_i(state), 2)

    def test_bay_full_rejects_collect(self):
        state = save.new_game()
        for _ in range(state["capacity"]):
            self.assertIsNotNone(save.collect_sample(state))
        self.assertTrue(save.rule_f(state))
        before = save.rule_i(state)
        self.assertIsNone(save.collect_sample(state))
        self.assertEqual(save.rule_i(state), before)

    def test_first_arrived_registered_first(self):
        state = save.new_game()
        save.collect_sample(state, "a")
        save.collect_sample(state, "b")
        self.assertEqual(state["queue"], [1, 2])
        self.assertEqual(save.rule_h(state), 1)
        self.assertEqual(save.rule_e(state), 1)

    def test_view_is_read_only(self):
        state = save.new_game()
        save.collect_sample(state)
        save.view_sample(state, 1)
        save.rule_d(state)
        save.rule_e(state)
        self.assertEqual(save.rule_i(state), 1)
        self.assertIn(1, state["events"])

    def test_duplicate_collection_counts_once(self):
        state = save.new_game()
        self.assertTrue(save.rule_g(state))
        self.assertFalse(save.rule_g(state))
        self.assertEqual(state["collected"], 1)


class TestPauseResume(unittest.TestCase):
    def test_pause_freezes_dive_and_collect(self):
        state = save.new_game()
        self.assertTrue(save.dive(state))
        self.assertEqual(state["depth"], 100)
        self.assertTrue(save.pause_mission(state))
        self.assertFalse(save.dive(state))
        self.assertIsNone(save.collect_sample(state))
        self.assertEqual(state["depth"], 100)
        self.assertEqual(state["src"], save.START_OXYGEN - save.DIVE_OXYGEN_COST)
        self.assertEqual(save.rule_i(state), 0)

    def test_resume_continues_from_frozen_point(self):
        state = save.new_game()
        save.dive(state)
        save.pause_mission(state)
        self.assertFalse(save.dive(state))
        self.assertTrue(save.resume_mission(state))
        self.assertTrue(save.dive(state))
        self.assertEqual(state["depth"], 200)
        self.assertEqual(state["src"], save.START_OXYGEN - 2 * save.DIVE_OXYGEN_COST)
        self.assertEqual(save.collect_sample(state), 1)

    def test_pause_resume_are_idempotent(self):
        state = save.new_game()
        self.assertTrue(save.pause_mission(state))
        self.assertFalse(save.pause_mission(state))
        self.assertTrue(save.resume_mission(state))
        self.assertFalse(save.resume_mission(state))
        self.assertEqual(state["depth"], 0)


class TestReset(unittest.TestCase):
    def test_reset_clears_everything(self):
        state = save.new_game()
        save.dive(state)
        save.collect_sample(state)
        save.collect_sample(state)
        save.reset_mission(state)
        self.assertEqual(state, save.new_game())
        self.assertEqual(state["next_id"], 1)


class TestSaveLoad(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.path = os.path.join(self.tmp, "save.json")

    def tearDown(self):
        if os.path.exists(self.path):
            os.remove(self.path)
        os.rmdir(self.tmp)

    def test_roundtrip_keeps_ids_continuous(self):
        state = save.new_game()
        save.collect_sample(state)
        save.collect_sample(state)
        save.save_game(state, self.path)
        loaded = save.load_game(self.path)
        self.assertEqual(loaded["next_id"], 3)
        self.assertEqual(save.collect_sample(loaded), 3)
        self.assertEqual(save.rule_i(loaded), 3)

    def test_paused_state_persists(self):
        state = save.new_game()
        save.pause_mission(state)
        save.save_game(state, self.path)
        loaded = save.load_game(self.path)
        self.assertTrue(loaded["paused"])
        self.assertFalse(save.dive(loaded))
        self.assertTrue(save.resume_mission(loaded))

    def test_events_survive_roundtrip(self):
        state = save.new_game()
        save.collect_sample(state)
        save.save_game(state, self.path)
        loaded = save.load_game(self.path)
        self.assertEqual(loaded["events"], {1: (1, 0)})

    def test_corrupted_json_starts_new_game_without_crash(self):
        with open(self.path, "w", encoding="utf-8") as fh:
            fh.write("{not valid json")
        loaded = save.load_game(self.path)
        self.assertTrue(loaded.get("save_recovered"))
        self.assertEqual(
            {k: v for k, v in loaded.items() if k != "save_recovered"},
            save.new_game(),
        )
        with open(self.path, encoding="utf-8") as fh:
            self.assertIn("not valid json", fh.read())

    def test_invalid_fields_starts_new_game(self):
        with open(self.path, "w", encoding="utf-8") as fh:
            fh.write('{"depth": 0, "next_id": "oops"}')
        loaded = save.load_game(self.path)
        self.assertTrue(loaded.get("save_recovered"))
        self.assertEqual(loaded["next_id"], 1)

    def test_missing_file_starts_new_game(self):
        loaded = save.load_game(os.path.join(self.tmp, "missing.json"))
        self.assertTrue(loaded.get("save_recovered"))
        self.assertEqual(loaded["items"], [])


if __name__ == "__main__":
    unittest.main()
