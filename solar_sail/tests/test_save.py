import unittest

import save


class TestSave(unittest.TestCase):
    def test_duplicate_route(self):
        state = save.new_game()
        self.assertTrue(save.add_route(state, "地球-火星"))
        self.assertFalse(save.add_route(state, "地球-火星"))
        self.assertEqual(state["routes"], ["地球-火星"])

    def test_sail_capacity(self):
        state = save.new_game()
        for i in range(save.SAIL_CAPACITY):
            self.assertTrue(save.deploy_sail(state, f"帆{i}"))
        self.assertFalse(save.deploy_sail(state, "帆满"))
        self.assertEqual(len(state["sails"]), save.SAIL_CAPACITY)

    def test_empty_route_returns_none(self):
        state = save.new_game()
        self.assertIsNone(save.first_route(state))

    def test_first_leg_first_out(self):
        state = save.new_game()
        state["legs"] = ["内圈", "外圈"]
        self.assertEqual(save.pass_leg(state), "内圈")
        self.assertEqual(save.pass_leg(state), "外圈")
        self.assertIsNone(save.pass_leg(state))

    def test_paused_blocks_sailing(self):
        state = save.new_game()
        state["energy"] = 100
        state["paused"] = True
        self.assertFalse(save.sail(state, "航段A"))
        self.assertEqual(state["energy"], 100)

    def test_view_routes_does_not_delete(self):
        state = save.new_game()
        save.add_route(state, "近地")
        seen = save.view_routes(state)
        seen.clear()
        self.assertEqual(state["routes"], ["近地"])

    def test_light_counts_fully(self):
        state = save.new_game()
        self.assertEqual(save.add_light(state, 3, 4, 5), 12)
        self.assertEqual(state["energy"], 12)

    def test_voyage_counted_once(self):
        state = save.new_game()
        self.assertTrue(save.record_voyage(state, "v1"))
        self.assertFalse(save.record_voyage(state, "v1"))
        self.assertEqual(state["voyage_count"], 1)

    def test_insufficient_energy_rolls_back(self):
        state = save.new_game()
        state["energy"] = 5
        state["legs"] = ["航段A"]
        before = dict(state)
        self.assertFalse(save.sail(state, "航段A"))
        self.assertEqual(state, before)

    def test_reset_clears_everything(self):
        state = save.new_game()
        save.add_route(state, "近地")
        save.add_light(state, 50)
        save.record_voyage(state, "v1")
        save.reset(state)
        self.assertEqual(state, save.new_game())

    def test_save_load_round_trip_and_no_slot_skip(self):
        state = save.new_game()
        save.add_route(state, "地球-火星")
        save.add_light(state, 30)
        save.record_voyage(state, "v1", legs=2)
        payload1 = save.save(state)
        payload2 = save.save(state)
        slot1, restored1 = save.load(payload1)
        slot2, _ = save.load(payload2)
        self.assertEqual((slot1, slot2), (1, 2))
        self.assertEqual(save.save(restored1, slot1), payload1)
        self.assertEqual(restored1["routes"], ["地球-火星"])
        self.assertEqual(restored1["energy"], 30)
        self.assertEqual(restored1["voyage_count"], 1)


if __name__ == "__main__":
    unittest.main()
