import unittest

import main


class TestMain(unittest.TestCase):
    def test_case_a(self):
        state = main.new_game()
        state.update({'balance': 10})
        self.assertFalse(main.cmd_a(state))
        self.assertEqual(state["balance"], 10)

    def test_case_b(self):
        state = main.new_game()
        state.update({'accounts': {}})
        self.assertEqual(main.cmd_b(state), 0)

    def test_case_c(self):
        state = main.new_game()
        self.assertFalse(main.cmd_c(state))

    def test_case_d(self):
        state = main.new_game()
        state.update({'events': {1: True}})
        main.cmd_d(state)
        self.assertNotIn(1, state["events"])

    def test_case_e(self):
        state = main.new_game()
        state.update({'used': 1, 'cap': 2})
        self.assertEqual(main.cmd_e(state), 1)

    def test_case_f(self):
        state = main.new_game()
        self.assertFalse(main.cmd_f(state))

    def test_case_g(self):
        state = main.new_game()
        state.update({'nodes': {1: True, 2: True}, 'edges': {(1, 2): 5}})
        main.cmd_g(state)
        self.assertNotIn((1, 2), state["edges"])

    def test_case_h(self):
        state = main.new_game()
        self.assertIsNone(main.cmd_h(state))

    def test_case_i(self):
        state = main.new_game()
        state.update({'queue': []})
        state["queue"] = [1]
        self.assertEqual(main.cmd_i(state), 1)
        self.assertEqual(len(state["queue"]), 1)

    def test_case_j(self):
        state = main.new_game()
        state.update({'count': 0})
        state["count"] = 5
        main.cmd_j(state)
        self.assertEqual(state["count"], 0)


if __name__ == "__main__":
    unittest.main()
