import unittest

import world


class TestWorld(unittest.TestCase):
    def test_case_a(self):
        state = world.new_game()
        state.update({'count': 0})
        state["count"] = 5
        world.action_a(state)
        self.assertEqual(state["count"], 0)

    def test_case_b(self):
        state = world.new_game()
        state.update({'balance': 10})
        self.assertFalse(world.action_b(state))
        self.assertEqual(state["balance"], 10)

    def test_case_c(self):
        state = world.new_game()
        state.update({'accounts': {}})
        self.assertEqual(world.action_c(state), 0)

    def test_case_d(self):
        state = world.new_game()
        self.assertFalse(world.action_d(state))

    def test_case_e(self):
        state = world.new_game()
        state.update({'events': {1: True}})
        world.action_e(state)
        self.assertNotIn(1, state["events"])

    def test_case_f(self):
        state = world.new_game()
        state.update({'used': 1, 'cap': 2})
        self.assertEqual(world.action_f(state), 1)

    def test_case_g(self):
        state = world.new_game()
        self.assertFalse(world.action_g(state))

    def test_case_h(self):
        state = world.new_game()
        state.update({'nodes': {1: True, 2: True}, 'edges': {(1, 2): 5}})
        world.action_h(state)
        self.assertNotIn((1, 2), state["edges"])

    def test_case_i(self):
        state = world.new_game()
        self.assertIsNone(world.action_i(state))

    def test_case_j(self):
        state = world.new_game()
        state.update({'queue': []})
        state["queue"] = [1]
        self.assertEqual(world.action_j(state), 1)
        self.assertEqual(len(state["queue"]), 1)


if __name__ == "__main__":
    unittest.main()
