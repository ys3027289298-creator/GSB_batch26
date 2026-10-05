import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import save


class TestOxygen(unittest.TestCase):
    def test_dive_consumes_exact_cost(self):
        state = save.new_game()
        self.assertTrue(save.dive(state, 30))
        self.assertEqual(state["oxygen"], 70)
        self.assertEqual(state["depth"], 30)

    def test_dive_rejected_when_oxygen_short(self):
        # 氧气少算：不足时拒绝下潜，氧气与深度都保持不变
        state = save.new_game()
        state["oxygen"] = 5
        self.assertFalse(save.dive(state, 10))
        self.assertEqual(state["oxygen"], 5)
        self.assertEqual(state["depth"], 0)


class TestPauseResume(unittest.TestCase):
    def test_pause_blocks_dive(self):
        # 暂停仍下潜：暂停期间下潜被拒绝
        state = save.new_game()
        save.pause(state)
        with self.assertRaises(save.PausedError):
            save.dive(state, 1)
        self.assertEqual(state["depth"], 0)
        self.assertEqual(state["oxygen"], save.DEFAULT_OXYGEN)

    def test_resume_restores_diving(self):
        # 恢复后按当前氧气正常下潜，暂停本身不耗氧
        state = save.new_game()
        save.pause(state)
        save.resume(state)
        self.assertTrue(save.dive(state, 10))
        self.assertEqual(state["oxygen"], 90)
        self.assertEqual(state["depth"], 10)

    def test_pause_survives_save_load(self):
        # 暂停状态随存档持久化，读档后仍然禁止下潜
        state = save.new_game()
        save.pause(state)
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "slot.json")
            save.save_game(state, path)
            loaded = save.load_game(path)
        self.assertTrue(loaded["paused"])
        with self.assertRaises(save.PausedError):
            save.dive(loaded, 1)


class TestSamples(unittest.TestCase):
    def test_duplicate_sample_rejected(self):
        # 重复样本：同一编号登记两次，第二次被拒绝
        state = save.new_game()
        save.collect_sample(state, 1, "管虫")
        with self.assertRaises(save.DuplicateSampleError):
            save.collect_sample(state, 1, "管虫")
        self.assertEqual(len(state["samples"]), 1)

    def test_chamber_full_rejects_collect(self):
        # 样本舱满仍采集：装满后继续采集被拒绝
        state = save.new_game()
        state["capacity"] = 2
        save.collect_sample(state, 1, "a")
        save.collect_sample(state, 2, "b")
        with self.assertRaises(save.ChamberFullError):
            save.collect_sample(state, 3, "c")
        self.assertEqual(len(state["samples"]), 2)

    def test_empty_samples_returns_text(self):
        # 空样本返回文本：空舱给出提示文本而非空串
        state = save.new_game()
        text = save.format_samples(state)
        self.assertIsInstance(text, str)
        self.assertTrue(text.strip())

    def test_earliest_arrival_registered_first(self):
        # 先到样本未登记：先到达的样本先被登记
        state = save.new_game()
        late = save.arrive_sample(state, "晚到", seq=2)
        early = save.arrive_sample(state, "先到", seq=1)
        self.assertEqual(save.register_next(state), early)
        self.assertEqual(save.register_next(state), late)
        self.assertIsNone(save.register_next(state))

    def test_view_does_not_delete(self):
        # 查看样本误删：查看是纯读操作
        state = save.new_game()
        save.collect_sample(state, 1, "a")
        state["queue"] = [1, 2]
        save.view_samples(state)
        save.view_samples(state)
        self.assertEqual(len(state["samples"]), 1)
        self.assertEqual(state["queue"], [1, 2])

    def test_collect_counted_once(self):
        # 单次采集重复累计：同一编号只累计一次
        state = save.new_game()
        save.collect_sample(state, 1, "a")
        with self.assertRaises(save.DuplicateSampleError):
            save.collect_sample(state, 1, "a")
        self.assertEqual(state["collected"]["1"], 1)

    def test_reset_clears_everything(self):
        # 重置不清：重置后所有进度字段恢复初始值
        state = save.new_game()
        save.dive(state, 10)
        save.collect_sample(state, 1, "a")
        save.pause(state)
        save.reset(state)
        self.assertEqual(state, save.new_game())


class TestIds(unittest.TestCase):
    def test_ids_are_continuous(self):
        # 读档跳号：编号先分配后自增，连续不跳号
        state = save.new_game()
        self.assertEqual(save.alloc_id(state), 1)
        self.assertEqual(save.alloc_id(state), 2)

    def test_ids_continuous_after_load(self):
        state = save.new_game()
        save.arrive_sample(state, "a", seq=1)
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "slot.json")
            save.save_game(state, path)
            loaded = save.load_game(path)
        self.assertEqual(save.alloc_id(loaded), 2)


class TestPersistence(unittest.TestCase):
    def test_roundtrip(self):
        state = save.new_game()
        save.dive(state, 10)
        save.collect_sample(state, 1, "a")
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "slot.json")
            save.save_game(state, path)
            self.assertEqual(save.load_game(path), state)

    def test_missing_file_load_or_new(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "missing.json")
            self.assertEqual(save.load_or_new(path), save.new_game())

    def test_corrupt_json_quarantined(self):
        # 损坏存档：非法 JSON 被隔离为 .corrupt，load_or_new 返回新游戏
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "slot.json")
            with open(path, "w", encoding="utf-8") as handle:
                handle.write("{not json")
            with self.assertRaises(save.CorruptSaveError):
                save.load_game(path)
            self.assertFalse(os.path.exists(path))
            self.assertTrue(os.path.exists(path + ".corrupt"))
            self.assertEqual(save.load_or_new(path), save.new_game())

    def test_invalid_structure_quarantined(self):
        # 损坏存档：结构校验失败同样被隔离
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "slot.json")
            with open(path, "w", encoding="utf-8") as handle:
                json.dump({"oxygen": "很多很多"}, handle)
            with self.assertRaises(save.CorruptSaveError):
                save.load_game(path)
            self.assertTrue(os.path.exists(path + ".corrupt"))
            self.assertEqual(save.load_or_new(path), save.new_game())


if __name__ == "__main__":
    unittest.main()
