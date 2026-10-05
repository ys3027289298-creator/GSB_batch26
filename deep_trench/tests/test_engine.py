import unittest

import engine


class TestEngine(unittest.TestCase):
    def test_case_a(self):
        state = engine.new_game()
        state.update({'src': 5, 'dst': 0})
        engine.rule_a(state)
        self.assertEqual(state["src"], 5)

    def test_case_b(self):
        state = engine.new_game()
        state.update({'closed': False})
        state["closed"] = True
        self.assertFalse(engine.rule_b(state))

    def test_case_c(self):
        state = engine.new_game()
        state.update({'events': {}})
        self.assertTrue(engine.rule_c(state))
        self.assertFalse(engine.rule_c(state))

    def test_case_d(self):
        state = engine.new_game()
        self.assertFalse(engine.rule_d(state))

    def test_case_e(self):
        state = engine.new_game()
        state.update({'events': {1: (5, 6), 2: (1, 2)}})
        self.assertEqual(engine.rule_e(state), 2)

    def test_case_f(self):
        state = engine.new_game()
        self.assertFalse(engine.rule_f(state))

    def test_case_g(self):
        state = engine.new_game()
        self.assertTrue(engine.rule_g(state))
        self.assertFalse(engine.rule_g(state))

    def test_case_h(self):
        state = engine.new_game()
        state.update({'queue': []})
        state["queue"] = [1, 2]
        self.assertEqual(engine.rule_h(state), 1)

    def test_case_i(self):
        state = engine.new_game()
        state.update({'items': []})
        state["items"] = [1]
        self.assertEqual(engine.rule_i(state), 1)

    def test_case_j(self):
        state = engine.new_game()
        state.update({'next_id': 1})
        state["next_id"] = 7
        self.assertEqual(engine.rule_j(state), 7)


if __name__ == "__main__":
    unittest.main()
