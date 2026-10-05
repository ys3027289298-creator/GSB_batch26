import os
import tempfile
import unittest

import save


def farm():
    state = save.new_game()
    save.create_array(state, "A", 2)
    save.create_array(state, "B", 1)
    save.add_battery(state, "bat1", 100)
    save.add_battery(state, "bat2", 50)
    return state


class TestSchedulingFixes(unittest.TestCase):
    def test_no_duplicate_panels(self):
        state = farm()
        ids = {save.connect_panel(state, "A") for _ in range(2)}
        ids.add(save.connect_panel(state, "B"))
        self.assertEqual(len(ids), 3)
        self.assertEqual(sorted(ids), [1, 2, 3])

    def test_full_array_rejects_and_keeps_state(self):
        state = farm()
        save.connect_panel(state, "B")
        with self.assertRaises(save.CapacityError):
            save.connect_panel(state, "B")
        self.assertEqual(save.view_panels(state, "B"), [1])
        self.assertEqual(state["next_id"], 2)  # 失败不消耗编号

    def test_empty_array_returns_empty_list_not_text(self):
        state = farm()
        self.assertEqual(save.view_panels(state, "A"), [])

    def test_first_arrived_calibrated_first(self):
        state = farm()
        first = save.connect_panel(state, "A")
        second = save.connect_panel(state, "A")
        self.assertEqual(save.calibrate_next(state), first)
        self.assertEqual(save.calibrate_next(state), second)
        self.assertIsNone(save.calibrate_next(state))

    def test_locked_farm_cannot_discharge(self):
        state = farm()
        save.charge_battery(state, "bat1", 40)
        save.lock_farm(state)
        with self.assertRaises(save.StateLockedError):
            save.discharge(state, "e1", 10)
        self.assertEqual(save.storage_total(state), 40)  # 未放电
        save.unlock_farm(state)
        self.assertEqual(save.discharge(state, "e1", 10), 10)

    def test_view_does_not_remove_panels(self):
        state = farm()
        pid = save.connect_panel(state, "A")
        save.view_panels(state, "A")
        save.view_panels(state, "A")
        self.assertEqual(save.view_panels(state, "A"), [pid])

    def test_storage_total_counts_all_batteries(self):
        state = farm()
        save.charge_battery(state, "bat1", 30)
        save.charge_battery(state, "bat2", 20)
        self.assertEqual(save.storage_total(state), 50)

    def test_discharge_event_settles_only_once(self):
        state = farm()
        save.charge_battery(state, "bat1", 60)
        self.assertEqual(save.discharge(state, "e1", 25), 25)
        self.assertFalse(save.discharge(state, "e1", 25))  # 重复结算被拒绝
        self.assertEqual(save.storage_total(state), 35)
        self.assertEqual(save.discharge(state, "e2", 10), 10)  # 新事件正常

    def test_reset_clears_everything(self):
        state = farm()
        save.connect_panel(state, "A")
        save.charge_battery(state, "bat1", 10)
        save.discharge(state, "e1", 5)
        save.lock_farm(state)
        save.reset(state)
        self.assertEqual(state["panels"], {})
        self.assertEqual(state["arrays"], {})
        self.assertEqual(state["batteries"], {})
        self.assertEqual(state["arrival_queue"], [])
        self.assertEqual(state["next_id"], 1)
        self.assertFalse(state["locked"])
        self.assertEqual(state["discharged_events"], set())

    def test_load_does_not_skip_or_reuse_ids(self):
        state = farm()
        save.connect_panel(state, "A")
        save.connect_panel(state, "A")
        save.connect_panel(state, "B")  # next_id 应为 4
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "farm.json")
            save.save_game(state, path)
            loaded = save.new_game()
            save.load_game(loaded, path)
        self.assertEqual(loaded["next_id"], 4)
        save.create_array(loaded, "C", 1)
        self.assertEqual(save.connect_panel(loaded, "C"), 4)

    def test_load_repairs_low_next_id(self):
        # 旧档 next_id 偏小: 读档后至少为 最大编号 + 1
        state = farm()
        save.connect_panel(state, "A")
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "farm.json")
            save.save_game(state, path)
            with open(path, encoding="utf-8") as fh:
                data = fh.read()
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(data.replace('"next_id": 2', '"next_id": 1'))
            loaded = save.new_game()
            save.load_game(loaded, path)
        self.assertEqual(loaded["next_id"], 2)


class TestFailureKindsAndRecovery(unittest.TestCase):
    def test_illegal_input_rejected_state_untouched(self):
        state = farm()
        with self.assertRaises(save.IllegalInputError):
            save.create_array(state, "bad", 0)
        with self.assertRaises(save.IllegalInputError):
            save.create_array(state, "A", 5)  # 重名
        with self.assertRaises(save.IllegalInputError):
            save.connect_panel(state, "nope")
        with self.assertRaises(save.IllegalInputError):
            save.charge_battery(state, "bat1", -3)
        self.assertEqual(set(state["arrays"]), {"A", "B"})
        self.assertEqual(save.storage_total(state), 0)
        # 恢复策略: 修正参数后重试即成功
        self.assertEqual(save.recovery_for(save.IllegalInputError()), "reject_and_fix_args")
        save.create_array(state, "A2", 5)
        self.assertIn("A2", state["arrays"])

    def test_capacity_error_retry_after_freeing_space(self):
        state = farm()
        save.charge_battery(state, "bat2", 50)
        with self.assertRaises(save.CapacityError):
            save.charge_battery(state, "bat2", 1)
        self.assertEqual(state["batteries"]["bat2"]["charge"], 50)  # 未部分入账
        self.assertEqual(
            save.recovery_for(save.CapacityError()),
            "free_space_or_expand_then_retry",
        )
        save.discharge(state, "drain", 20)  # 释放空间后重试同一操作
        save.charge_battery(state, "bat2", 15)
        self.assertEqual(state["batteries"]["bat2"]["charge"], 45)

    def test_state_locked_replay_after_unlock(self):
        state = farm()
        save.lock_farm(state)
        for op in (
            lambda: save.connect_panel(state, "A"),
            lambda: save.calibrate_next(state),
            lambda: save.charge_battery(state, "bat1", 5),
            lambda: save.discharge(state, "e1", 5),
        ):
            with self.assertRaises(save.StateLockedError):
                op()
        self.assertEqual(
            save.recovery_for(save.StateLockedError()),
            "unlock_then_replay",
        )
        save.unlock_farm(state)
        pid = save.connect_panel(state, "A")  # 解锁后重放成功
        self.assertEqual(save.calibrate_next(state), pid)

    def test_failure_is_atomic(self):
        state = farm()
        before = save._serialize(state)
        for op in (
            lambda: save.connect_panel(state, "missing"),
            lambda: save.charge_battery(state, "bat1", 10**9),
            lambda: save.discharge(state, "e1", -1),
        ):
            with self.assertRaises(save.SolarFarmError):
                op()
        self.assertEqual(save._serialize(state), before)


class TestPersistenceBoundary(unittest.TestCase):
    def test_roundtrip_preserves_state(self):
        state = farm()
        pid = save.connect_panel(state, "A")
        save.calibrate_next(state)
        save.charge_battery(state, "bat1", 12.5)
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "farm.json")
            save.save_game(state, path)
            loaded = save.new_game()
            save.load_game(loaded, path)
        self.assertEqual(loaded["panels"][pid]["calibrated"], True)
        self.assertEqual(loaded["batteries"]["bat1"]["charge"], 12.5)
        self.assertEqual(save.view_panels(loaded, "A"), [pid])
        self.assertEqual(loaded["discharged_events"], set())  # 运行时状态不入档

    def test_corrupt_save_raises_and_keeps_current_state(self):
        state = farm()
        save.connect_panel(state, "A")
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "bad.json")
            with open(path, "w", encoding="utf-8") as fh:
                fh.write("{not json")
            with self.assertRaises(save.IllegalInputError):
                save.load_game(state, path)
            with open(path, "w", encoding="utf-8") as fh:
                fh.write('{"panels": []}')
            with self.assertRaises(save.IllegalInputError):
                save.load_game(state, path)
        self.assertEqual(len(state["panels"]), 1)  # 当前状态未被污染


if __name__ == "__main__":
    unittest.main()
