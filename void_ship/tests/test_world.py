import copy
import unittest

import world


class TestWorld(unittest.TestCase):
    def test_case_a(self):
        state = world.new_game()
        segments = ["alpha", "beta", "gamma"]
        first = world.add_route(state, segments)
        second = world.add_route(state, segments)
        self.assertIsNone(second)
        self.assertEqual(len(state["routes"]), 1)
        self.assertIn(first, state["routes"])

    def test_case_b(self):
        state = world.new_game()
        state["cabin_used"] = state["cabin_cap"]
        self.assertFalse(world.board(state))
        self.assertEqual(state["cabin_used"], state["cabin_cap"])

    def test_case_c(self):
        state = world.new_game()
        route_id = world.add_route(state, [])
        self.assertIsNone(world.route_text(state, route_id))

    def test_case_d(self):
        state = world.new_game()
        self.assertFalse(world.arrive(state, 2))
        self.assertEqual(state["position"], 0)
        self.assertEqual(state["passed"], [])
        self.assertTrue(world.arrive(state, 0))
        self.assertTrue(world.arrive(state, 1))
        self.assertTrue(world.arrive(state, 2))

    def test_case_e(self):
        state = world.new_game()
        state["paused"] = True
        self.assertFalse(world.sail(state))
        self.assertEqual(state["position"], 0)
        self.assertEqual(state["log"], [])

    def test_case_f(self):
        state = world.new_game()
        route_id = world.add_route(state, ["alpha", "beta"])
        self.assertIsNotNone(world.view_route(state, route_id))
        self.assertIn(route_id, state["routes"])
        self.assertEqual(world.view_route(state, route_id), ["alpha", "beta"])

    def test_case_g(self):
        state = world.new_game()
        state["energy"] = 10
        self.assertEqual(world.consume_energy(state, 4), 6)
        self.assertEqual(state["energy"], 6)

    def test_case_h(self):
        state = world.new_game()
        world.complete_voyage(state)
        self.assertEqual(state["voyages"], 1)

    def test_case_i(self):
        state = world.new_game()
        world.add_route(state, ["alpha"])
        world.complete_voyage(state)
        world.sail(state)
        world.reset(state)
        self.assertEqual(state["routes"], {})
        self.assertEqual(state["voyages"], 0)
        self.assertEqual(state["log"], [])
        self.assertEqual(state["next_route_id"], 1)

    def test_case_j(self):
        state = world.new_game()
        world.add_route(state, ["alpha"])
        snapshot = world.save_game(state)
        loaded = world.new_game()
        world.load_save(loaded, snapshot)
        self.assertEqual(loaded["next_route_id"], snapshot["next_route_id"])


class TestReplay(unittest.TestCase):
    def test_save_replay_is_deterministic(self):
        first_half = [
            ("add_route", (["alpha", "beta", "gamma"],)),
            ("add_route", (["delta", "epsilon"],)),
            ("board", ()),
            ("consume_energy", (3,)),
            ("arrive", (0,)),
            ("sail", ()),
            ("complete_voyage", ()),
        ]
        second_half = [
            ("board", ()),
            ("consume_energy", (2,)),
            ("arrive", (1,)),
            ("arrive", (2,)),
            ("sail", ()),
            ("route_text", (1,)),
            ("view_route", (2,)),
            ("complete_voyage", ()),
        ]

        def run_once():
            state = world.new_game()
            for name, args in first_half:
                getattr(world, name)(state, *args)
            snapshot = world.save_game(state)
            state = world.new_game()
            world.load_save(state, snapshot)
            outputs = []
            for name, args in second_half:
                outputs.append(getattr(world, name)(state, *args))
            return world.save_game(state), outputs

        runs = [run_once() for _ in range(3)]
        for run in runs[1:]:
            self.assertEqual(run, runs[0])

    def test_reset_then_replay_matches_fresh_run(self):
        script = [
            ("add_route", (["alpha"],)),
            ("board", ()),
            ("sail", ()),
            ("reset", ()),
            ("add_route", (["beta", "gamma"],)),
            ("arrive", (0,)),
            ("complete_voyage", ()),
        ]

        def run_once():
            state = world.new_game()
            outputs = []
            for name, args in script:
                outputs.append(getattr(world, name)(state, *args))
            return world.save_game(state), outputs

        baseline = run_once()
        for _ in range(2):
            self.assertEqual(run_once(), baseline)


if __name__ == "__main__":
    unittest.main()
