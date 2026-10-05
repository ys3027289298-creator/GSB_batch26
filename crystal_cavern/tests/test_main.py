import unittest

import main


class TestMain(unittest.TestCase):
    def test_case_a(self):
        state = main.new_game()
        state.update({'balance': 10})
        self.assertFalse(main.cmd_a(state))
        self.assertEqual(state["balance"], 10)

    def test_case_b(self):
        state = main.new_game()
        state.update({'accounts': {}})
        self.assertEqual(main.cmd_b(state), 0)

    def test_case_c(self):
        state = main.new_game()
        self.assertFalse(main.cmd_c(state))

    def test_case_d(self):
        state = main.new_game()
        state.update({'events': {1: True}})
        main.cmd_d(state)
        self.assertNotIn(1, state["events"])

    def test_case_e(self):
        state = main.new_game()
        state.update({'used': 1, 'cap': 2})
        self.assertEqual(main.cmd_e(state), 1)

    def test_case_f(self):
        state = main.new_game()
        self.assertFalse(main.cmd_f(state))

    def test_case_g(self):
        state = main.new_game()
        state.update({'nodes': {1: True, 2: True}, 'edges': {(1, 2): 5}})
        main.cmd_g(state)
        self.assertNotIn((1, 2), state["edges"])

    def test_case_h(self):
        state = main.new_game()
        self.assertIsNone(main.cmd_h(state))

    def test_case_i(self):
        state = main.new_game()
        state.update({'queue': []})
        state["queue"] = [1]
        self.assertEqual(main.cmd_i(state), 1)
        self.assertEqual(len(state["queue"]), 1)

    def test_case_j(self):
        state = main.new_game()
        state.update({'count': 0})
        state["count"] = 5
        main.cmd_j(state)
        self.assertEqual(state["count"], 0)


if __name__ == "__main__":
    unittest.main()


class TestCrystalCavern(unittest.TestCase):
    """十个状态覆盖故障的复现 + 修复回归。"""

    def test_duplicate_cluster_rejected(self):
        # 重复晶簇: 同一晶簇二次进入矿层被拒绝, 矿层只保留一份
        s = main.new_game()
        cid = main.apply(s, main.spawn_cluster, 5)
        self.assertTrue(main.apply(s, main.enter_layer, cid))
        self.assertFalse(main.apply(s, main.enter_layer, cid))
        self.assertEqual(s["layer"], [cid])

    def test_full_layer_entry_rolled_back(self):
        # 矿层满载仍进入: 满载后进入被拒绝且状态整体回滚(回滚路径一)
        s = main.new_game(layer_capacity=2)
        ids = [main.apply(s, main.spawn_cluster, 3) for _ in range(3)]
        for cid in ids[:2]:
            self.assertTrue(main.apply(s, main.enter_layer, cid))
        before = {k: main.copy.deepcopy(s[k]) for k in main.STATE_KEYS}
        self.assertFalse(main.apply(s, main.enter_layer, ids[2]))
        self.assertEqual({k: s[k] for k in main.STATE_KEYS}, before)
        self.assertEqual(main.layer_status(s), main.LAYER_FULL)

    def test_empty_backpack_returns_none(self):
        # 空背包返回文本: 应为 None 而非 "empty"
        s = main.new_game()
        self.assertIsNone(main.apply(s, main.backpack_status))

    def test_first_arrived_harvested_first(self):
        # 先到晶簇未采集: 采集顺序必须按到达先后
        s = main.new_game()
        a = main.apply(s, main.spawn_cluster, 4)
        b = main.apply(s, main.spawn_cluster, 7)
        main.apply(s, main.enter_layer, a)
        main.apply(s, main.enter_layer, b)
        result = main.apply(s, main.harvest)
        self.assertEqual(result["cluster"], a)
        self.assertEqual(result["crystals"], 4)

    def test_paused_no_growth(self):
        # 暂停仍生长: 暂停时 grow 被拒绝且水晶数不变
        s = main.new_game()
        cid = main.apply(s, main.spawn_cluster, 5)
        main.apply(s, main.enter_layer, cid)
        main.apply(s, main.pause)
        self.assertFalse(main.apply(s, main.grow, 3))
        self.assertEqual(s["clusters"][cid]["crystals"], 5)
        main.apply(s, main.resume)
        self.assertTrue(main.apply(s, main.grow, 3))
        self.assertEqual(s["clusters"][cid]["crystals"], 8)

    def test_view_does_not_delete(self):
        # 查看晶簇误删: 查看后晶簇仍在
        s = main.new_game()
        cid = main.apply(s, main.spawn_cluster, 6)
        info = main.apply(s, main.view_cluster, cid)
        self.assertEqual(info["crystals"], 6)
        self.assertIn(cid, s["clusters"])

    def test_crystal_count_exact(self):
        # 水晶少算: 采集入账必须精确, 不少一颗
        s = main.new_game(backpack_capacity=10)
        cid = main.apply(s, main.spawn_cluster, 5)
        main.apply(s, main.enter_layer, cid)
        main.apply(s, main.harvest)
        self.assertEqual(s["backpack"], 5)

    def test_single_harvest_counted_once(self):
        # 单次采集重复累计: 一次采集只入账一次, 空矿层再采不改变总量
        s = main.new_game()
        cid = main.apply(s, main.spawn_cluster, 5)
        main.apply(s, main.enter_layer, cid)
        main.apply(s, main.harvest)
        self.assertEqual(s["harvested_total"], 5)
        self.assertFalse(main.apply(s, main.harvest))
        self.assertEqual(s["harvested_total"], 5)

    def test_reset_clears_everything(self):
        # 重置不清: reset 后三份状态全部回到初始
        s = main.new_game()
        cid = main.apply(s, main.spawn_cluster, 5)
        main.apply(s, main.enter_layer, cid)
        main.apply(s, main.harvest)
        main.reset(s)
        self.assertEqual({k: s[k] for k in main.STATE_KEYS},
                         {k: main.new_game()[k] for k in main.STATE_KEYS})
        self.assertEqual(s["history"], [])

    def test_load_keeps_id_sequence(self):
        # 读档跳号: 读档后新晶簇编号接着走, 不跳号不撞号
        s = main.new_game()
        main.apply(s, main.spawn_cluster, 3)
        main.apply(s, main.spawn_cluster, 4)
        data = main.save(s)
        s2 = main.new_game()
        self.assertTrue(main.load(s2, data))
        self.assertEqual(main.apply(s2, main.spawn_cluster, 1), 3)

    def test_full_backpack_harvest_rolled_back(self):
        # 背包已满时采集: 整体回滚, 晶簇不被部分转移(回滚路径二)
        s = main.new_game(backpack_capacity=0)
        cid = main.apply(s, main.spawn_cluster, 5)
        main.apply(s, main.enter_layer, cid)
        before = {k: main.copy.deepcopy(s[k]) for k in main.STATE_KEYS}
        self.assertFalse(main.apply(s, main.harvest))
        self.assertEqual({k: s[k] for k in main.STATE_KEYS}, before)
        self.assertIn(cid, s["clusters"])

    def test_explicit_rollback_restores_state(self):
        # 显式回滚: 撤销最近一次已接受命令
        s = main.new_game()
        cid = main.apply(s, main.spawn_cluster, 5)
        main.apply(s, main.enter_layer, cid)
        self.assertTrue(main.rollback(s))
        self.assertEqual(s["layer"], [])
        self.assertIn(cid, s["clusters"])


if __name__ == "__main__":
    unittest.main()
