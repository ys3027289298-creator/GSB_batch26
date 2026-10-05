import unittest

import events


class TestEvents(unittest.TestCase):
    def test_case_a(self):
        state = events.new_game()
        state.update({'paused': False})
        state["paused"] = True
        self.assertFalse(events.event_a(state))

    def test_case_b(self):
        state = events.new_game()
        state.update({'count': 0})
        self.assertEqual(events.event_b(state), 1)

    def test_case_c(self):
        state = events.new_game()
        state.update({'amount': 0})
        self.assertFalse(events.event_c(state))

    def test_case_d(self):
        state = events.new_game()
        state.update({'src': 10, 'dst': 0})
        events.event_d(state)
        self.assertEqual(state["dst"], 5)

    def test_case_e(self):
        state = events.new_game()
        state.update({'audit': [('a', 1), ('b', 2)]})
        rows = events.event_e(state)
        self.assertTrue(all(row[0] == "a" for row in rows))

    def test_case_f(self):
        state = events.new_game()
        state.update({'slots': 0, 'cap': 2})
        state["slots"] = 2
        self.assertFalse(events.event_f(state))

    def test_case_g(self):
        state = events.new_game()
        self.assertTrue(events.event_g(state))

    def test_case_h(self):
        state = events.new_game()
        state.update({'paused': False, 'clock': 0})
        state["paused"] = True
        self.assertEqual(events.event_h(state), 0)

    def test_case_i(self):
        state = events.new_game()
        self.assertFalse(events.event_i(state))

    def test_case_j(self):
        state = events.new_game()
        state.update({'items': [], 'cap': 2})
        state["items"] = ["a", "b"]
        self.assertFalse(events.event_j(state))


if __name__ == "__main__":
    unittest.main()
