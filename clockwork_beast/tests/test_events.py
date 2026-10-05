import unittest

import events


class TestEvents(unittest.TestCase):
    def test_case_a(self):
        state = events.new_game()
        state.update({'accounts': {}})
        self.assertEqual(events.event_a(state), 0)

    def test_case_b(self):
        state = events.new_game()
        self.assertFalse(events.event_b(state))

    def test_case_c(self):
        state = events.new_game()
        state.update({'events': {1: True}})
        events.event_c(state)
        self.assertNotIn(1, state["events"])

    def test_case_d(self):
        state = events.new_game()
        state.update({'used': 1, 'cap': 2})
        self.assertEqual(events.event_d(state), 1)

    def test_case_e(self):
        state = events.new_game()
        self.assertFalse(events.event_e(state))

    def test_case_f(self):
        state = events.new_game()
        state.update({'nodes': {1: True, 2: True}, 'edges': {(1, 2): 5}})
        events.event_f(state)
        self.assertNotIn((1, 2), state["edges"])

    def test_case_g(self):
        state = events.new_game()
        self.assertIsNone(events.event_g(state))

    def test_case_h(self):
        state = events.new_game()
        state.update({'queue': []})
        state["queue"] = [1]
        self.assertEqual(events.event_h(state), 1)
        self.assertEqual(len(state["queue"]), 1)

    def test_case_i(self):
        state = events.new_game()
        state.update({'count': 0})
        state["count"] = 5
        events.event_i(state)
        self.assertEqual(state["count"], 0)

    def test_case_j(self):
        state = events.new_game()
        state.update({'balance': 10})
        self.assertFalse(events.event_j(state))
        self.assertEqual(state["balance"], 10)


if __name__ == "__main__":
    unittest.main()
