import os
import tempfile
import unittest

import engine


SCRIPT = [
    "explore",          # 1  found relic-1（先到遗物立即登记）
    "explore",          # 2  found relic-2
    "next",             # 3  窥视队首，不弹出（单次探索不重复累计）
    "pickup relic-1",   # 4  picked relic-1
    "pickup relic-1",   # 5  重复遗物被拒绝，余额回滚
    "pause",            # 6  paused
    "explore",          # 7  暂停仍触发 -> 被拒绝
    "resume",           # 8  resumed
    "bag",              # 9  bag: relic-1
    "commit",           # 10 committed 2（提交后计数清零）
    "commit",           # 11 committed 0（不跨次累计）
]

EXPECTED = [
    "found relic-1",
    "found relic-2",
    "next: relic-1",
    "picked relic-1",
    "背包已满或遗物重复，未拾取",
    "paused",
    "paused: 探索未触发",
    "resumed",
    "bag: relic-1",
    "committed 2",
    "committed 0",
]


class TestReplay(unittest.TestCase):
    def test_fixed_input_replay(self):
        state = engine.new_game()
        outputs = engine.replay(SCRIPT, state)
        self.assertEqual(outputs, EXPECTED)
        self.assertEqual(state["balance"], 80)   # 重复拾取已回滚，只扣一次
        self.assertEqual(state["found"], 2)
        self.assertEqual(state["count"], 0)      # 提交后清零
        self.assertEqual(state["bag"], ["relic-1"])
        self.assertEqual(state["next_id"], 3)

    def test_replay_is_deterministic(self):
        self.assertEqual(engine.replay(SCRIPT), engine.replay(SCRIPT))

    def test_stamina_rollback(self):
        state = engine.new_game()
        state["balance"] = 10
        outputs = engine.replay(["explore", "pickup relic-1"], state)
        self.assertEqual(outputs[-1], "体力不足，已回滚")
        self.assertEqual(state["balance"], 10)   # 体力不足不扣减
        self.assertEqual(state["bag"], [])

    def test_empty_bag_returns_none(self):
        state = engine.new_game()
        self.assertIsNone(engine.rule_f(state))
        outputs = engine.replay(["bag"], state)
        self.assertEqual(outputs, ["bag: (empty)"])

    def test_serialization_roundtrip_no_id_skip(self):
        state = engine.new_game()
        engine.replay(SCRIPT, state)
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "save.json")
            engine.save_game(state, path)
            loaded = engine.load_game(path)
        self.assertEqual(loaded, state)          # 序列化往返一致
        self.assertEqual(loaded["next_id"], 3)   # 读档不跳号
        outputs = engine.replay(["explore"], loaded)
        self.assertEqual(outputs, ["found relic-3"])

    def test_reset_clears_state(self):
        state = engine.new_game()
        engine.replay(SCRIPT, state)
        engine.replay(["reset"], state)
        self.assertEqual(state, engine.new_game())

    def test_view_relic_does_not_delete(self):
        state = engine.new_game()
        engine.replay(["explore", "explore"], state)
        first = engine.rule_g(state)
        second = engine.rule_g(state)
        self.assertEqual(first, second)          # 查看不弹出
        self.assertEqual(len(state["queue"]), 2)

    def test_node_removal_cleans_edges(self):
        state = engine.new_game()
        state.update({"nodes": {1: True, 2: True}, "edges": {(1, 2): 5}})
        engine.rule_e(state)
        self.assertNotIn((1, 2), state["edges"])
        payload = engine.serialize(state)
        self.assertEqual(engine.deserialize(payload)["edges"], {})


if __name__ == "__main__":
    unittest.main()
