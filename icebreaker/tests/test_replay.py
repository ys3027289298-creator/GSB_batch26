import os
import tempfile
import unittest

import save


SCRIPT = ["a", "c", "e", "f", "g", "i", "h", "", "a", "j", "e"]


class TestReplay(unittest.TestCase):
    def test_same_inputs_same_results(self):
        first = save.run_script(SCRIPT)
        second = save.run_script(SCRIPT)
        self.assertEqual(first, second)

    def test_empty_route_returns_text(self):
        _, _, text = save.apply_input(save.new_game(), [], "")
        self.assertTrue(text)

    def test_save_load_replay_consistent(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "slot1.json")
            state, history, _ = save.run_script(SCRIPT + ["save " + path])

            loaded_state, loaded_history = save.load_game(path)
            self.assertEqual(loaded_state, state)
            self.assertEqual(loaded_history, history)

            loaded_state, loaded_history, _ = save.apply_input(loaded_state, loaded_history, "a")
            self.assertEqual(loaded_state["audit"][-1][1], len(loaded_state["audit"]))

            self.assertEqual(save.replay_save(path), state)


if __name__ == "__main__":
    unittest.main()
