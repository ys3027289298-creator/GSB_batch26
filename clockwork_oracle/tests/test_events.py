import unittest

import events


class TestForecastBugs(unittest.TestCase):
    def test_duplicate_forecast_not_repeated(self):
        state = events.new_game()
        first = events.forecast(state, "流星雨")
        second = events.forecast(state, "流星雨")
        self.assertEqual(first, second)
        self.assertEqual(len(events.view_forecasts(state)), 1)

    def test_full_observatory_rejects(self):
        state = events.new_game(capacity=1)
        events.forecast(state, "日食")
        with self.assertRaises(events.ObservatoryFullError):
            events.forecast(state, "月食")
        self.assertEqual(len(events.view_forecasts(state)), 1)

    def test_empty_forecast_returns_none_not_text(self):
        state = events.new_game()
        self.assertIsNone(events.view_next(state))
        self.assertIsNone(events.observe(state))

    def test_first_arrived_observed_first(self):
        state = events.new_game()
        events.forecast(state, "先到")
        events.forecast(state, "后到")
        self.assertEqual(events.observe(state)["event"], "先到")

    def test_locked_state_not_updated(self):
        state = events.new_game()
        events.forecast(state, "风暴")
        events.lock(state)
        with self.assertRaises(events.OracleLockedError):
            events.forecast(state, "地震")
        with self.assertRaises(events.OracleLockedError):
            events.observe(state)
        self.assertEqual(len(events.view_forecasts(state)), 1)
        events.unlock(state)
        self.assertIsNotNone(events.observe(state))

    def test_view_does_not_delete(self):
        state = events.new_game()
        events.forecast(state, "彗星")
        events.view_forecasts(state)
        events.view_next(state)
        self.assertEqual(len(events.view_forecasts(state)), 1)

    def test_clockwork_counts_each_processed(self):
        state = events.new_game()
        events.forecast(state, "一")
        events.forecast(state, "二")
        events.observe(state)
        events.observe(state)
        self.assertEqual(state["clockwork"], 2)

    def test_single_forecast_counted_once(self):
        state = events.new_game()
        events.forecast(state, "唯一")
        self.assertEqual(state["next_id"], 2)
        self.assertEqual(len(events.view_forecasts(state)), 1)

    def test_reset_clears_everything(self):
        state = events.new_game()
        events.forecast(state, "残留")
        events.observe(state)
        events.reset(state)
        self.assertEqual(events.view_forecasts(state), [])
        self.assertEqual(state["clockwork"], 0)
        self.assertEqual(state["next_id"], 1)
        self.assertIsNone(events.view_next(state))

    def test_load_keeps_sequence_no_skip(self):
        state = events.new_game()
        events.forecast(state, "甲")
        events.forecast(state, "乙")
        events.observe(state)
        restored = events.load(events.save(state))
        self.assertEqual(events.forecast(restored, "丙"), 3)


class TestFailureCategories(unittest.TestCase):
    def test_invalid_input_recoverable(self):
        state = events.new_game()
        with self.assertRaises(events.InvalidForecastError) as ctx:
            events.forecast(state, "")
        self.assertIn("重新提交", ctx.exception.recovery)
        self.assertEqual(events.view_forecasts(state), [])

    def test_capacity_failure_recovers_after_observe(self):
        state = events.new_game(capacity=1)
        events.forecast(state, "占位")
        with self.assertRaises(events.ObservatoryFullError):
            events.forecast(state, "新预报")
        events.observe(state)
        self.assertEqual(events.forecast(state, "新预报"), 2)

    def test_locked_failure_recovers_after_unlock(self):
        state = events.new_game()
        events.lock(state)
        with self.assertRaises(events.OracleLockedError):
            events.forecast(state, "锁定中")
        events.unlock(state)
        self.assertEqual(events.forecast(state, "锁定中"), 1)


if __name__ == "__main__":
    unittest.main()
