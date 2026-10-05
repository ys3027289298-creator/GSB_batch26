import unittest

import save


class TestSave(unittest.TestCase):
    def test_case_a(self):
        state = save.new_game()
        state.update({'paused': False, 'clock': 0})
        state["paused"] = True
        self.assertEqual(save.state_a(state), 0)

    def test_case_b(self):
        state = save.new_game()
        self.assertFalse(save.state_b(state))

    def test_case_c(self):
        state = save.new_game()
        state.update({'items': [], 'cap': 2})
        state["items"] = ["a", "b"]
        self.assertFalse(save.state_c(state))

    def test_case_d(self):
        state = save.new_game()
        state.update({'paused': False})
        state["paused"] = True
        self.assertFalse(save.state_d(state))

    def test_case_e(self):
        state = save.new_game()
        state.update({'count': 0})
        self.assertEqual(save.state_e(state), 1)

    def test_case_f(self):
        state = save.new_game()
        state.update({'amount': 0})
        self.assertFalse(save.state_f(state))

    def test_case_g(self):
        state = save.new_game()
        state.update({'src': 10, 'dst': 0})
        save.state_g(state)
        self.assertEqual(state["dst"], 5)

    def test_case_h(self):
        state = save.new_game()
        state.update({'audit': [('a', 1), ('b', 2)]})
        rows = save.state_h(state)
        self.assertTrue(all(row[0] == "a" for row in rows))

    def test_case_i(self):
        state = save.new_game()
        state.update({'slots': 0, 'cap': 2})
        state["slots"] = 2
        self.assertFalse(save.state_i(state))

    def test_case_j(self):
        state = save.new_game()
        self.assertTrue(save.state_j(state))


if __name__ == "__main__":
    unittest.main()
