import copy
import unittest

import world


class TestWorld(unittest.TestCase):
    def setUp(self):
        self.state = world.new_game()

    def test_duplicate_cargo_event_is_idempotent(self):
        first = world.submit_cargo(self.state, "丝绸", 3, "e1")
        second = world.submit_cargo(self.state, "丝绸", 99, "e1")
        self.assertEqual(first, second)
        self.assertEqual(self.state["cargo"]["丝绸"], 3)

    def test_same_item_merges_single_entry(self):
        world.submit_cargo(self.state, "丝绸", 3, "e1")
        world.submit_cargo(self.state, "丝绸", 2, "e2")
        self.assertEqual(self.state["cargo"], {"丝绸": 5})

    def test_full_beasts_reject_load_atomically(self):
        self.state["beast_cap"] = 5
        world.load_beasts(self.state, 5)
        before = copy.deepcopy(self.state)
        with self.assertRaises(world.CaravanError):
            world.load_beasts(self.state, 1)
        self.assertEqual(before, self.state)

    def test_empty_manifest_returns_none_not_text(self):
        self.assertIsNone(world.view_cargo(self.state))
        self.assertNotIn("cargo_view", self.state)

    def test_arrivals_unload_fifo(self):
        world.receive_arrival(self.state, "先到", 1)
        world.receive_arrival(self.state, "后到", 1)
        self.assertEqual(world.unload_next(self.state)["item"], "先到")
        self.assertEqual(world.unload_next(self.state)["item"], "后到")

    def test_paused_blocks_trades_and_resume_continues(self):
        self.state["gold"] = 50
        world.submit_cargo(self.state, "丝绸", 2, "e1")
        world.pause(self.state)
        with self.assertRaises(world.CaravanError):
            world.settle_trade(self.state, "丝绸", 1, 10)
        world.resume(self.state)
        total = world.settle_trade(self.state, "丝绸", 1, 10)
        self.assertEqual(total, 10)

    def test_view_cargo_is_readonly(self):
        world.submit_cargo(self.state, "丝绸", 2, "e1")
        view = world.view_cargo(self.state)
        view["丝绸"] = 999
        self.assertEqual(self.state["cargo"]["丝绸"], 2)

    def test_gold_settled_exactly_once_per_trade(self):
        self.state["gold"] = 100
        world.submit_cargo(self.state, "丝绸", 3, "e1")
        total = world.settle_trade(self.state, "丝绸", 2, 15)
        self.assertEqual(total, 30)
        self.assertEqual(self.state["gold"], 70)
        self.assertEqual(self.state["round_count"], 1)

    def test_insufficient_gold_leaves_no_half_change(self):
        self.state["gold"] = 5
        world.submit_cargo(self.state, "丝绸", 3, "e1")
        before = copy.deepcopy(self.state)
        with self.assertRaises(world.CaravanError):
            world.settle_trade(self.state, "丝绸", 1, 10)
        self.assertEqual(before, self.state)

    def test_missing_account_counts_as_zero(self):
        self.assertEqual(world.account_balance(self.state, "nobody"), 0)

    def test_reset_round_clears_count(self):
        self.state["gold"] = 100
        world.submit_cargo(self.state, "丝绸", 5, "e1")
        world.settle_trade(self.state, "丝绸", 1, 1)
        world.reset_round(self.state)
        self.assertEqual(self.state["round_count"], 0)

    def test_load_game_continues_instead_of_restarting(self):
        world.submit_cargo(self.state, "丝绸", 2, "e1")
        world.pause(self.state)
        restored = world.load_game(world.save_game(self.state))
        self.assertEqual(restored["phase"], world.PHASE_PAUSED)
        self.assertEqual(restored["next_id"], self.state["next_id"])
        world.resume(restored)
        new_id = world.submit_cargo(restored, "茶叶", 1, "e2")
        self.assertEqual(new_id, self.state["next_id"])
        self.assertEqual(restored["cargo"]["丝绸"], 2)

    def test_peek_does_not_dequeue(self):
        world.receive_arrival(self.state, "货", 1)
        self.assertEqual(world.peek_arrival(self.state)["item"], "货")
        self.assertEqual(len(self.state["arrivals"]), 1)


if __name__ == "__main__":
    unittest.main()
