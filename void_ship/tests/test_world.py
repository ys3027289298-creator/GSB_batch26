import unittest

import world


class TestWorld(unittest.TestCase):
    def test_case_a(self):
        state = world.new_game()
        world.add_route(state, "R1")
        self.assertFalse(world.add_route(state, "R1"))
        self.assertEqual(state["routes"], ["R1"])

    def test_case_b(self):
        state = world.new_game()
        state["cargo"] = ["a", "b", "c"]
        self.assertFalse(world.board_cargo(state, "d"))
        self.assertEqual(state["cargo"], ["a", "b", "c"])

    def test_case_c(self):
        state = world.new_game()
        self.assertIsNone(world.route_detail(state, "ghost"))

    def test_case_d(self):
        state = world.new_game()
        self.assertFalse(world.pass_segment(state, 2))
        self.assertEqual(state["segments"], [])

    def test_case_e(self):
        state = world.new_game()
        state["paused"] = True
        self.assertEqual(world.sail(state, 5), 0)
        self.assertEqual(state["distance"], 0)

    def test_case_f(self):
        state = world.new_game()
        state["routes"] = ["R1", "R2"]
        self.assertEqual(world.list_routes(state), ["R1", "R2"])
        self.assertEqual(state["routes"], ["R1", "R2"])

    def test_case_g(self):
        state = world.new_game()
        state["used"] = 3
        self.assertEqual(world.energy_remain(state), 7)

    def test_case_h(self):
        state = world.new_game()
        self.assertEqual(world.finish_voyage(state), 1)
        self.assertEqual(state["voyages"], 1)

    def test_case_i(self):
        state = world.new_game()
        state["voyages"] = 3
        state["distance"] = 9
        world.reset_voyages(state)
        self.assertEqual(state["voyages"], 0)
        self.assertEqual(state["distance"], 0)

    def test_case_j(self):
        state = world.new_game()
        state["next_id"] = 5
        blob = world.save_game(state)
        loaded = world.load_game(blob)
        self.assertEqual(loaded["next_id"], 5)

    def test_replay_deterministic(self):
        fresh = world.new_game()
        fresh["next_id"] = 5
        checkpoint = world.save_game(fresh)
        commands = [
            ("add_route", "R1"),
            ("add_route", "R1"),
            ("board", "a"),
            ("board", "b"),
            ("board", "c"),
            ("board", "d"),
            ("route_detail", "ghost"),
            ("pass_segment", 2),
            ("sail", 5),
            ("set_paused", True),
            ("sail", 3),
            ("list_routes",),
            ("energy",),
            ("finish_voyage",),
            ("reset",),
            ("save",),
            ("load", checkpoint),
            ("add_route", "R2"),
            ("sail", 1),
            ("save",),
        ]
        baseline = None
        for _ in range(3):
            state = world.new_game()
            outputs = world.replay(state, commands)
            snapshot = (outputs, world.save_game(state))
            if baseline is None:
                baseline = snapshot
            self.assertEqual(snapshot, baseline)


if __name__ == "__main__":
    unittest.main()
