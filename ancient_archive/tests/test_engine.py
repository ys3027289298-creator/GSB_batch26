import os
import tempfile
import unittest

import engine


class TestEngine(unittest.TestCase):
    def test_case_a(self):
        state = engine.new_game()
        self.assertIsNone(engine.rule_a(state))

    def test_case_b(self):
        state = engine.new_game()
        state.update({'queue': []})
        state["queue"] = [1]
        self.assertEqual(engine.rule_b(state), 1)
        self.assertEqual(len(state["queue"]), 1)

    def test_case_c(self):
        state = engine.new_game()
        state.update({'count': 0})
        state["count"] = 5
        engine.rule_c(state)
        self.assertEqual(state["count"], 0)

    def test_case_d(self):
        state = engine.new_game()
        state.update({'balance': 10})
        self.assertFalse(engine.rule_d(state))
        self.assertEqual(state["balance"], 10)

    def test_case_e(self):
        state = engine.new_game()
        state.update({'accounts': {}})
        self.assertEqual(engine.rule_e(state), 0)

    def test_case_f(self):
        state = engine.new_game()
        self.assertFalse(engine.rule_f(state))

    def test_case_g(self):
        state = engine.new_game()
        state.update({'events': {1: True}})
        engine.rule_g(state)
        self.assertNotIn(1, state["events"])

    def test_case_h(self):
        state = engine.new_game()
        state.update({'used': 1, 'cap': 2})
        self.assertEqual(engine.rule_h(state), 1)

    def test_case_i(self):
        state = engine.new_game()
        self.assertFalse(engine.rule_i(state))

    def test_case_j(self):
        state = engine.new_game()
        state.update({'nodes': {1: True, 2: True}, 'edges': {(1, 2): 5}})
        engine.rule_j(state)
        self.assertNotIn((1, 2), state["edges"])

    def test_pause_resume_roundtrip(self):
        state = engine.new_game()
        state.update({"queue": [1, 2], "count": 3, "balance": 40})
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "save.json")
            self.assertTrue(engine.save_game(state, path))
            self.assertEqual(engine.load_game(path), state)

    def test_resume_missing_save(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "absent.json")
            self.assertEqual(engine.load_game(path), engine.new_game())

    def test_resume_corrupted_save(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "save.json")
            with open(path, "w", encoding="utf-8") as fh:
                fh.write('{"queue": [1, 2], "count":')
            self.assertEqual(engine.load_game(path), engine.new_game())

    def test_resume_non_dict_save(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "save.json")
            with open(path, "w", encoding="utf-8") as fh:
                fh.write("[1, 2, 3]")
            self.assertEqual(engine.load_game(path), engine.new_game())


if __name__ == "__main__":
    unittest.main()
