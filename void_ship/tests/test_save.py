import unittest

import save


class TestSave(unittest.TestCase):
    def test_case_a(self):
        state = save.new_game()
        state.update({'queue': []})
        state["queue"] = [1]
        self.assertEqual(save.state_a(state), 1)
        self.assertEqual(len(state["queue"]), 1)

    def test_case_b(self):
        state = save.new_game()
        state.update({'count': 0})
        state["count"] = 5
        save.state_b(state)
        self.assertEqual(state["count"], 0)

    def test_case_c(self):
        state = save.new_game()
        state.update({'balance': 10})
        self.assertFalse(save.state_c(state))
        self.assertEqual(state["balance"], 10)

    def test_case_d(self):
        state = save.new_game()
        state.update({'accounts': {}})
        self.assertEqual(save.state_d(state), 0)

    def test_case_e(self):
        state = save.new_game()
        self.assertFalse(save.state_e(state))

    def test_case_f(self):
        state = save.new_game()
        state.update({'events': {1: True}})
        save.state_f(state)
        self.assertNotIn(1, state["events"])

    def test_case_g(self):
        state = save.new_game()
        state.update({'used': 1, 'cap': 2})
        self.assertEqual(save.state_g(state), 1)

    def test_case_h(self):
        state = save.new_game()
        self.assertFalse(save.state_h(state))

    def test_case_i(self):
        state = save.new_game()
        state.update({'nodes': {1: True, 2: True}, 'edges': {(1, 2): 5}})
        save.state_i(state)
        self.assertNotIn((1, 2), state["edges"])

    def test_case_j(self):
        state = save.new_game()
        self.assertIsNone(save.state_j(state))


if __name__ == "__main__":
    unittest.main()
