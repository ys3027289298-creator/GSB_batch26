import unittest

import events


class TestEvents(unittest.TestCase):
    def test_case_a(self):
        state = events.new_game()
        state.update({'next_id': 1})
        state["next_id"] = 7
        self.assertEqual(events.event_a(state), 7)

    def test_case_b(self):
        state = events.new_game()
        state.update({'src': 5, 'dst': 0})
        events.event_b(state)
        self.assertEqual(state["src"], 5)

    def test_case_c(self):
        state = events.new_game()
        state.update({'closed': False})
        state["closed"] = True
        self.assertFalse(events.event_c(state))

    def test_case_d(self):
        state = events.new_game()
        state.update({'events': {}})
        self.assertTrue(events.event_d(state))
        self.assertFalse(events.event_d(state))

    def test_case_e(self):
        state = events.new_game()
        self.assertFalse(events.event_e(state))

    def test_case_f(self):
        state = events.new_game()
        state.update({'events': {1: (5, 6), 2: (1, 2)}})
        self.assertEqual(events.event_f(state), 2)

    def test_case_g(self):
        state = events.new_game()
        self.assertFalse(events.event_g(state))

    def test_case_h(self):
        state = events.new_game()
        self.assertTrue(events.event_h(state))
        self.assertFalse(events.event_h(state))

    def test_case_i(self):
        state = events.new_game()
        state.update({'queue': []})
        state["queue"] = [1, 2]
        self.assertEqual(events.event_i(state), 1)

    def test_case_j(self):
        state = events.new_game()
        state.update({'items': []})
        state["items"] = [1]
        self.assertEqual(events.event_j(state), 1)


if __name__ == "__main__":
    unittest.main()
