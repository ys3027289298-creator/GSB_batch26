import copy
import unittest

import main


class TestSkyLighthouse(unittest.TestCase):
    def test_repeated_arrival_does_not_duplicate_ship(self):
        state = main.new_game()
        first = main.arrive_ship(state, "海燕号")
        again = main.arrive_ship(state, "海燕号")
        self.assertEqual(first, again)
        self.assertEqual(len(state["ships"]), 1)
        self.assertEqual(state["waiting"], ["海燕号"])
        self.assertEqual(state["next_ship_no"], 2)

    def test_full_lane_rejects_guide_without_side_effects(self):
        state = main.new_game()
        for name in ("甲", "乙", "丙"):
            main.arrive_ship(state, name)
        main.guide_next(state, "north")
        main.guide_next(state, "north")
        snapshot = copy.deepcopy(state)
        self.assertIsNone(main.guide_next(state, "north"))
        self.assertEqual(state, snapshot)

    def test_empty_lane_returns_none_not_text(self):
        state = main.new_game()
        self.assertIsNone(main.lane_ships(state, "north"))
        main.arrive_ship(state, "海燕号")
        main.guide_next(state, "north")
        ships = main.lane_ships(state, "north")
        self.assertEqual([s["name"] for s in ships], ["海燕号"])

    def test_first_arrived_ship_guided_first(self):
        state = main.new_game()
        main.arrive_ship(state, "先到")
        main.arrive_ship(state, "后到")
        guided = main.guide_next(state, "north")
        self.assertEqual(guided["name"], "先到")
        self.assertEqual(state["waiting"], ["后到"])

    def test_locked_lane_cannot_be_lit(self):
        state = main.new_game()
        main.lock_lane(state, "north")
        self.assertFalse(main.light_lane(state, "north"))
        self.assertNotIn("north", state["lit"])
        main.unlock_lane(state, "north")
        self.assertTrue(main.light_lane(state, "north"))
        main.lock_lane(state, "north")
        self.assertNotIn("north", state["lit"])

    def test_peek_does_not_remove_ship(self):
        state = main.new_game()
        main.arrive_ship(state, "海燕号")
        snapshot = copy.deepcopy(state)
        self.assertEqual(main.peek_waiting(state)["name"], "海燕号")
        self.assertEqual(main.peek_waiting(state)["name"], "海燕号")
        self.assertEqual(state, snapshot)

    def test_fuel_counts_base_and_per_ship(self):
        state = main.new_game()
        main.arrive_ship(state, "海燕号")
        main.guide_next(state, "north")
        self.assertEqual(state["fuel_used"], main.FUEL_BASE + main.FUEL_PER_SHIP)

    def test_single_guidance_counted_once(self):
        state = main.new_game()
        main.arrive_ship(state, "海燕号")
        main.guide_next(state, "north")
        main.arrive_ship(state, "海燕号")
        snapshot = copy.deepcopy(state)
        self.assertIsNone(main.guide_next(state, "north"))
        self.assertEqual(state, snapshot)
        self.assertEqual(state["guided_total"], 1)

    def test_reset_clears_everything(self):
        state = main.new_game()
        main.arrive_ship(state, "海燕号")
        main.guide_next(state, "north")
        main.light_lane(state, "south")
        main.reset(state)
        self.assertEqual(state, main.new_game())
        main.reset(state)
        self.assertEqual(state, main.new_game())

    def test_load_preserves_ship_numbering(self):
        state = main.new_game()
        main.arrive_ship(state, "甲")
        main.arrive_ship(state, "乙")
        archive = main.save(state)
        restored = main.load(main.new_game(), archive)
        self.assertEqual(main.arrive_ship(restored, "丙")["no"], 3)
        once = main.load(main.new_game(), archive)
        twice = main.load(main.new_game(), archive)
        self.assertEqual(once, twice)
        self.assertEqual(once["next_ship_no"], 3)


if __name__ == "__main__":
    unittest.main()
