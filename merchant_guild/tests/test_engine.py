import unittest

import engine


class TestEngine(unittest.TestCase):
    def test_case_a(self):
        state = engine.new_game()
        state.update({'count': 0})
        self.assertEqual(engine.rule_a(state), 1)

    def test_case_b(self):
        state = engine.new_game()
        state.update({'amount': 0})
        self.assertFalse(engine.rule_b(state))

    def test_case_c(self):
        state = engine.new_game()
        state.update({'src': 10, 'dst': 0})
        engine.rule_c(state)
        self.assertEqual(state["dst"], 5)

    def test_case_d(self):
        state = engine.new_game()
        state.update({'audit': [('a', 1), ('b', 2)]})
        rows = engine.rule_d(state)
        self.assertTrue(all(row[0] == "a" for row in rows))

    def test_case_e(self):
        state = engine.new_game()
        state.update({'slots': 0, 'cap': 2})
        state["slots"] = 2
        self.assertFalse(engine.rule_e(state))

    def test_case_f(self):
        state = engine.new_game()
        self.assertTrue(engine.rule_f(state))

    def test_case_g(self):
        state = engine.new_game()
        state.update({'paused': False, 'clock': 0})
        state["paused"] = True
        self.assertEqual(engine.rule_g(state), 0)

    def test_case_h(self):
        state = engine.new_game()
        self.assertFalse(engine.rule_h(state))

    def test_case_i(self):
        state = engine.new_game()
        state.update({'items': [], 'cap': 2})
        state["items"] = ["a", "b"]
        self.assertFalse(engine.rule_i(state))

    def test_case_j(self):
        state = engine.new_game()
        state.update({'paused': False})
        state["paused"] = True
        self.assertFalse(engine.rule_j(state))


if __name__ == "__main__":
    unittest.main()
