import unittest

import main


class TestMain(unittest.TestCase):
    def test_case_a(self):
        state = main.new_game()
        state.update({'items': []})
        state["items"] = [1]
        self.assertEqual(main.cmd_a(state), 1)

    def test_case_b(self):
        state = main.new_game()
        state.update({'next_id': 1})
        state["next_id"] = 7
        self.assertEqual(main.cmd_b(state), 7)

    def test_case_c(self):
        state = main.new_game()
        state.update({'src': 5, 'dst': 0})
        main.cmd_c(state)
        self.assertEqual(state["src"], 5)

    def test_case_d(self):
        state = main.new_game()
        state.update({'closed': False})
        state["closed"] = True
        self.assertFalse(main.cmd_d(state))

    def test_case_e(self):
        state = main.new_game()
        state.update({'events': {}})
        self.assertTrue(main.cmd_e(state))
        self.assertFalse(main.cmd_e(state))

    def test_case_f(self):
        state = main.new_game()
        self.assertFalse(main.cmd_f(state))

    def test_case_g(self):
        state = main.new_game()
        state.update({'events': {1: (5, 6), 2: (1, 2)}})
        self.assertEqual(main.cmd_g(state), 2)

    def test_case_h(self):
        state = main.new_game()
        self.assertFalse(main.cmd_h(state))

    def test_case_i(self):
        state = main.new_game()
        self.assertTrue(main.cmd_i(state))
        self.assertFalse(main.cmd_i(state))

    def test_case_j(self):
        state = main.new_game()
        state.update({'queue': []})
        state["queue"] = [1, 2]
        self.assertEqual(main.cmd_j(state), 1)


if __name__ == "__main__":
    unittest.main()
