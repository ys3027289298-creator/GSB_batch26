import unittest

import engine


class TestEngine(unittest.TestCase):
    def setUp(self):
        self.state = engine.new_game()

    def test_no_duplicate_stall(self):
        # 现象1: 重复摊位 —— 重复登记返回同一摊位
        first = engine.register_stall(self.state, "s1", "alice")
        first["goods"]["gem"] = 3
        again = engine.register_stall(self.state, "s1", "bob")
        self.assertIs(first, again)
        self.assertEqual(len(self.state["stalls"]), 1)
        self.assertEqual(again["goods"], {"gem": 3})

    def test_dock_capacity(self):
        # 现象2: 码头满仍停靠 —— 满员后进入队列而非超额停靠
        for name in ["c1", "c2", "c3"]:
            self.assertEqual(engine.arrive_caravan(self.state, name)["status"], "docked")
        late = engine.arrive_caravan(self.state, "c4")
        self.assertEqual(late["status"], "queued")
        self.assertEqual(len(self.state["dock"]), 3)
        # 重复抵达为 no-op
        self.assertEqual(engine.arrive_caravan(self.state, "c4")["status"], "queued")
        self.assertEqual(self.state["queue"], ["c4"])

    def test_empty_stall_view(self):
        # 现象3: 空摊位返回文本 —— 统一返回空 dict
        engine.register_stall(self.state, "s1")
        self.assertEqual(engine.view_goods(self.state, "s1"), {})
        self.assertEqual(engine.view_goods(self.state, "ghost"), {})

    def test_fifo_promotion(self):
        # 现象4: 先到商队未交易 —— 离港后按到达顺序补位
        for name in ["c1", "c2", "c3", "c4", "c5"]:
            engine.arrive_caravan(self.state, name)
        engine.depart_caravan(self.state, "c2")
        self.assertEqual(self.state["dock"], ["c1", "c3", "c4"])
        self.assertEqual(self.state["queue"], ["c5"])

    def test_no_settle_while_paused(self):
        # 现象5: 暂停仍结算 —— 暂停时结算与交易均为 no-op
        engine.register_stall(self.state, "s1")
        engine.stock_goods(self.state, "s1", "gem", 5)
        engine.trade(self.state, "s1", "gem", 2, 10, trade_id="t1")
        engine.pause(self.state)
        self.assertEqual(engine.settle(self.state), 0)
        self.assertEqual(self.state["coins"], 0)
        engine.resume(self.state)
        self.assertEqual(engine.settle(self.state), 20)
        self.assertEqual(self.state["coins"], 20)

    def test_view_does_not_delete(self):
        # 现象6: 查看商品误删 —— 查看是纯读
        engine.register_stall(self.state, "s1")
        engine.stock_goods(self.state, "s1", "gem", 5)
        goods = engine.view_goods(self.state, "s1")
        goods["gem"] = 0
        self.assertEqual(engine.view_goods(self.state, "s1"), {"gem": 5})

    def test_coins_amount(self):
        # 现象7: 影币少算 —— 按 数量*单价 全额入账
        engine.register_stall(self.state, "s1")
        engine.stock_goods(self.state, "s1", "gem", 10)
        engine.trade(self.state, "s1", "gem", 3, 7, trade_id="t1")
        engine.trade(self.state, "s1", "gem", 4, 7, trade_id="t2")
        engine.settle(self.state)
        self.assertEqual(self.state["coins"], 3 * 7 + 4 * 7)

    def test_trade_idempotent(self):
        # 现象8: 单次交易重复累计 —— 同 trade_id 重放不重复扣货记账
        engine.register_stall(self.state, "s1")
        engine.stock_goods(self.state, "s1", "gem", 5)
        r1 = engine.trade(self.state, "s1", "gem", 2, 10, trade_id="t1")
        r2 = engine.trade(self.state, "s1", "gem", 2, 10, trade_id="t1")
        self.assertIs(r1, r2)
        self.assertEqual(engine.view_goods(self.state, "s1"), {"gem": 3})
        self.assertEqual(len(self.state["ledger"]), 1)
        engine.settle(self.state)
        engine.settle(self.state)
        self.assertEqual(self.state["coins"], 20)

    def test_reset_clears_ledger(self):
        # 现象9: 重置不清流水 —— 重置后流水、交易、影币全部清空
        engine.register_stall(self.state, "s1")
        engine.stock_goods(self.state, "s1", "gem", 5)
        engine.trade(self.state, "s1", "gem", 2, 10, trade_id="t1")
        engine.settle(self.state)
        engine.reset(self.state)
        self.assertEqual(self.state["ledger"], [])
        self.assertEqual(self.state["trades"], {})
        self.assertEqual(self.state["coins"], 0)
        self.assertEqual(self.state, engine.new_game())

    def test_load_keeps_id_sequence(self):
        # 现象10: 读档跳号 —— next_id 随存档恢复
        engine.arrive_caravan(self.state)
        engine.arrive_caravan(self.state)
        data = engine.save(self.state)
        engine.reset(self.state)
        engine.load(self.state, data)
        result = engine.arrive_caravan(self.state)
        self.assertEqual(result["id"], "caravan-3")
        # 重复读档结果一致
        engine.load(self.state, data)
        self.assertEqual(self.state, engine.load(engine.new_game(), data))

    def test_failed_trade_rolls_back(self):
        # 现象11: 失败交易回滚 —— 任何失败路径都不留部分写入
        engine.register_stall(self.state, "s1")
        engine.stock_goods(self.state, "s1", "gem", 2)
        before = (dict(engine.view_goods(self.state, "s1")),
                  len(self.state["ledger"]), self.state["coins"])
        # 库存不足
        r = engine.trade(self.state, "s1", "gem", 9, 10, trade_id="bad1")
        self.assertFalse(r["ok"])
        # 摊位不存在
        self.assertFalse(engine.trade(self.state, "ghost", "gem", 1, 1, trade_id="bad2")["ok"])
        # 参数非法
        self.assertFalse(engine.trade(self.state, "s1", "gem", 0, 10, trade_id="bad3")["ok"])
        # 暂停中
        engine.pause(self.state)
        self.assertFalse(engine.trade(self.state, "s1", "gem", 1, 1, trade_id="bad4")["ok"])
        engine.resume(self.state)
        after = (engine.view_goods(self.state, "s1"),
                 len(self.state["ledger"]), self.state["coins"])
        self.assertEqual(before, after)
        # 失败的 trade_id 不占用幂等键, 修正参数后可重试成功
        ok = engine.trade(self.state, "s1", "gem", 2, 10, trade_id="bad1")
        self.assertTrue(ok["ok"])
        self.assertEqual(engine.view_goods(self.state, "s1"), {})


if __name__ == "__main__":
    unittest.main()
