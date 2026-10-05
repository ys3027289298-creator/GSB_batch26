# Orbital Garden 轨道花园

光照、水分、养分与收成互相影响的轨道种植引擎。规则函数见 `engine.py`，
测试命令不变：`python -m unittest discover -s tests`。

## 暂停 / 恢复行为

- `pause(state)` 置 `paused=True` 后：
  - `rule_b` 时钟停止走动，返回值保持为暂停时刻的 `clock`；
  - `rule_e` 浇水被拒绝并返回 `False`，锁定区域不会被灌溉。
- `resume(state)` 解除暂停后，时钟从暂停时的 `clock` 原值继续，
  不会补跳暂停期间的 tick，也不会额外累计灌溉次数。
- 暂停期间状态可正常存档；读档后 `paused` 标志按存档恢复。

## 损坏存档行为

- `load_game(path)` 遇到文件不存在、JSON 损坏或缺少 `next_id` 等
  关键字段时，抛出 `ValueError`，不修改调用方任何现有状态。
- 加载失败不会消耗或跳过作物编号：`next_id` 只在成功读档时
  按存档记录恢复，编号连续、不回退（修复“读档跳号”）。
- 调用方捕获 `ValueError` 后可继续用当前状态游戏，或改用
  `new_game()` / `reset_game(state)` 重开；`reset_game` 会先彻底
  清空旧状态再写入初始值（修复“重置不清”）。
