import copy
import json
import unittest

import save


class TestSave(unittest.TestCase):
    def test_duplicate_route_rejected(self):
        state = save.new_game()
        first = save.add_route(state, "晨光航线", [0, 1, 2])
        self.assertEqual(first, 1)
        self.assertIsNone(save.add_route(state, "晨光航线", [0, 1, 2]))
        self.assertEqual(len(state["routes"]), 1)
        self.assertEqual(state["next_route_id"], 2)
        other = save.add_route(state, "暮光航线", [0, 1, 2])
        self.assertEqual(other, 2)

    def test_deploy_when_full(self):
        state = save.new_game()
        for _ in range(state["sail_capacity"]):
            self.assertTrue(save.deploy_sail(state))
        self.assertEqual(state["sails_deployed"], state["sail_capacity"])
        self.assertFalse(save.deploy_sail(state))
        self.assertEqual(state["sails_deployed"], state["sail_capacity"])

    def test_empty_route_returns_none_not_text(self):
        state = save.new_game()
        self.assertIsNone(save.view_route(state, 99))
        route_id = save.add_route(state, "空线", [])
        self.assertIsNone(save.view_route(state, route_id))

    def test_view_does_not_delete(self):
        state = save.new_game()
        route_id = save.add_route(state, "环线", [0, 1])
        before = copy.deepcopy(state)
        save.view_route(state, route_id)
        self.assertEqual(state, before)

    def test_segments_must_be_passed_in_order(self):
        state = save.new_game()
        route_id = save.add_route(state, "序号线", [0, 1, 2])
        save.start_voyage(state, route_id)
        self.assertFalse(save.pass_segment(state, 2))
        self.assertEqual(state["passed_segments"], [])
        self.assertTrue(save.pass_segment(state, 0))
        self.assertTrue(save.pass_segment(state, 1))
        self.assertTrue(save.pass_segment(state, 2))

    def test_paused_ship_does_not_sail(self):
        state = save.new_game()
        save.deploy_sail(state)
        save.set_paused(state, True)
        self.assertEqual(save.sail(state), 0)
        self.assertEqual(state["light_energy"], 0)
        self.assertEqual(state["position"], 0)

    def test_light_energy_counts_all_sails(self):
        state = save.new_game()
        for _ in range(3):
            save.deploy_sail(state)
        gain = save.sail(state)
        self.assertEqual(gain, 30)
        self.assertEqual(state["light_energy"], 30)

    def test_voyage_counted_once(self):
        state = save.new_game()
        self.assertTrue(save.complete_voyage(state, "v1"))
        self.assertFalse(save.complete_voyage(state, "v1"))
        self.assertEqual(state["voyage_count"], 1)
        self.assertTrue(save.complete_voyage(state, "v2"))
        self.assertEqual(state["voyage_count"], 2)

    def test_reset_clears_progress(self):
        state = save.new_game()
        route_id = save.add_route(state, "线", [0, 1])
        save.start_voyage(state, route_id)
        save.deploy_sail(state)
        save.sail(state)
        save.pass_segment(state, 0)
        save.reset_voyage(state)
        self.assertIsNone(state["active_route"])
        self.assertEqual(state["position"], 0)
        self.assertEqual(state["passed_segments"], [])
        self.assertEqual(state["sails_deployed"], 0)
        self.assertEqual(state["light_energy"], 0)
        self.assertFalse(state["paused"])

    def test_save_load_roundtrip_and_id_continues(self):
        state = save.new_game()
        save.add_route(state, "线A", [0, 1])
        save.add_route(state, "线B", [0])
        route_id = save.add_route(state, "线C", [0, 1, 2])
        save.start_voyage(state, route_id)
        save.deploy_sail(state)
        save.deploy_sail(state)
        save.sail(state)
        save.pass_segment(state, 0)
        save.complete_voyage(state, "v1")

        restored = save.load_game(save.save_game(state))
        self.assertEqual(save.save_game(restored), save.save_game(state))
        next_id = save.add_route(restored, "线D", [3])
        self.assertEqual(next_id, state["next_route_id"])
        self.assertEqual(restored["next_route_id"], state["next_route_id"] + 1)
        self.assertEqual(restored["active_route"], route_id)
        self.assertEqual(restored["passed_segments"], [0])
        self.assertEqual(restored["completed_voyages"], ["v1"])

    def test_start_unknown_route_rolls_back(self):
        state = save.new_game()
        self.assertFalse(save.start_voyage(state, 123))
        self.assertIsNone(state["active_route"])


if __name__ == "__main__":
    unittest.main()
