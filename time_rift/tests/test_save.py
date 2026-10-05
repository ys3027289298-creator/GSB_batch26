import unittest

import save


class TestSave(unittest.TestCase):
    def test_case_a(self):
        state = save.new_game()
        state.update({'closed': False})
        state["closed"] = True
        self.assertFalse(save.state_a(state))

    def test_case_b(self):
        state = save.new_game()
        state.update({'events': {}})
        self.assertTrue(save.state_b(state))
        self.assertFalse(save.state_b(state))

    def test_case_c(self):
        state = save.new_game()
        self.assertFalse(save.state_c(state))

    def test_case_d(self):
        state = save.new_game()
        state.update({'events': {1: (5, 6), 2: (1, 2)}})
        self.assertEqual(save.state_d(state), 2)

    def test_case_e(self):
        state = save.new_game()
        self.assertFalse(save.state_e(state))

    def test_case_f(self):
        state = save.new_game()
        self.assertTrue(save.state_f(state))
        self.assertFalse(save.state_f(state))

    def test_case_g(self):
        state = save.new_game()
        state.update({'queue': []})
        state["queue"] = [1, 2]
        self.assertEqual(save.state_g(state), 1)

    def test_case_h(self):
        state = save.new_game()
        state.update({'items': []})
        state["items"] = [1]
        self.assertEqual(save.state_h(state), 1)

    def test_case_i(self):
        state = save.new_game()
        state.update({'next_id': 1})
        state["next_id"] = 7
        self.assertEqual(save.state_i(state), 7)

    def test_case_j(self):
        state = save.new_game()
        state.update({'src': 5, 'dst': 0})
        save.state_j(state)
        self.assertEqual(state["src"], 5)


if __name__ == "__main__":
    unittest.main()
