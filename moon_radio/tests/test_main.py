import unittest

import main


class TestMain(unittest.TestCase):
    def test_case_a(self):
        state = main.new_game()
        state.update({'items': [], 'cap': 2})
        state["items"] = ["a", "b"]
        self.assertFalse(main.cmd_a(state))

    def test_case_b(self):
        state = main.new_game()
        state.update({'paused': False})
        state["paused"] = True
        self.assertFalse(main.cmd_b(state))

    def test_case_c(self):
        state = main.new_game()
        state.update({'count': 0})
        self.assertEqual(main.cmd_c(state), 1)

    def test_case_d(self):
        state = main.new_game()
        state.update({'amount': 0})
        self.assertFalse(main.cmd_d(state))

    def test_case_e(self):
        state = main.new_game()
        state.update({'src': 10, 'dst': 0})
        main.cmd_e(state)
        self.assertEqual(state["dst"], 5)

    def test_case_f(self):
        state = main.new_game()
        state.update({'audit': [('a', 1), ('b', 2)]})
        rows = main.cmd_f(state)
        self.assertTrue(all(row[0] == "a" for row in rows))

    def test_case_g(self):
        state = main.new_game()
        state.update({'slots': 0, 'cap': 2})
        state["slots"] = 2
        self.assertFalse(main.cmd_g(state))

    def test_case_h(self):
        state = main.new_game()
        self.assertTrue(main.cmd_h(state))

    def test_case_i(self):
        state = main.new_game()
        state.update({'paused': False, 'clock': 0})
        state["paused"] = True
        self.assertEqual(main.cmd_i(state), 0)

    def test_case_j(self):
        state = main.new_game()
        self.assertFalse(main.cmd_j(state))


if __name__ == "__main__":
    unittest.main()
