import unittest

import world


class TestWorld(unittest.TestCase):
    def test_case_a(self):
        state = world.new_game()
        state.update({'src': 10, 'dst': 0})
        world.action_a(state)
        self.assertEqual(state["dst"], 5)

    def test_case_b(self):
        state = world.new_game()
        state.update({'audit': [('a', 1), ('b', 2)]})
        rows = world.action_b(state)
        self.assertTrue(all(row[0] == "a" for row in rows))

    def test_case_c(self):
        state = world.new_game()
        state.update({'slots': 0, 'cap': 2})
        state["slots"] = 2
        self.assertFalse(world.action_c(state))

    def test_case_d(self):
        state = world.new_game()
        self.assertTrue(world.action_d(state))

    def test_case_e(self):
        state = world.new_game()
        state.update({'paused': False, 'clock': 0})
        state["paused"] = True
        self.assertEqual(world.action_e(state), 0)

    def test_case_f(self):
        state = world.new_game()
        self.assertFalse(world.action_f(state))

    def test_case_g(self):
        state = world.new_game()
        state.update({'items': [], 'cap': 2})
        state["items"] = ["a", "b"]
        self.assertFalse(world.action_g(state))

    def test_case_h(self):
        state = world.new_game()
        state.update({'paused': False})
        state["paused"] = True
        self.assertFalse(world.action_h(state))

    def test_case_i(self):
        state = world.new_game()
        state.update({'count': 0})
        self.assertEqual(world.action_i(state), 1)

    def test_case_j(self):
        state = world.new_game()
        state.update({'amount': 0})
        self.assertFalse(world.action_j(state))


if __name__ == "__main__":
    unittest.main()
