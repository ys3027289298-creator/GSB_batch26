# deep_trench 深海海沟

深海下潜与样本采集的存档模块。纯规则在 `engine.py`（`rule_a`~`rule_j` 薄封装），
领域逻辑与存档持久化在 `save.py`。

## 十个问题的修复

| 问题 | 规则/函数 | 修复后行为 |
| --- | --- | --- |
| 重复样本 | `rule_c` / `collect_sample` | 同一编号已登记则拒绝（`DuplicateSampleError`），不产生第二条记录 |
| 样本舱满仍采集 | `rule_i` / `collect_sample` | 剩余容量 = 容量上限 - 已用数量；装满后拒绝采集（`ChamberFullError`） |
| 空样本返回文本 | `rule_d` / `format_samples` | 空舱返回提示文本「样本舱为空」，而非空串；`rule_d` 在空集合时返回 `False` |
| 先到样本未登记 | `rule_e` / `register_next` | 按到达次序取最早（`min`），先到的样本先登记 |
| 暂停仍下潜 | `rule_b` / `dive` | `paused=True` 时下潜抛 `PausedError`，不扣氧、不增加深度 |
| 查看样本误删 | `rule_h` / `view_samples` | 只查看队首（`queue[0]`），不调用 `pop`，可反复查看 |
| 氧气少算 | `rule_a` / `dive` | 余额不足时整笔拒绝，氧气不被扣成负数；每次下潜按 `米数 × 1` 精确扣减 |
| 单次采集重复累计 | `rule_g` / 采集计数 | 同一编号只累计一次，重复采集不会让计数增长 |
| 重置不清 | `rule_f` / `reset` | 清空全部进度字段并恢复初始值，旧样本、深度、暂停标记均不残留 |
| 读档跳号 | `rule_j` / `alloc_id` | 先返回当前编号再自增，编号连续；读档后接着档内编号分配 |

## 暂停与恢复行为说明

- `pause(state)` 把 `paused` 置为 `True`，此后 `dive` 一律抛 `PausedError`；
  被拒绝的下潜**不消耗氧气、不改变深度**。
- `resume(state)` 把 `paused` 置为 `False`，恢复后按当前剩余氧气正常下潜；
  暂停与恢复本身都不耗氧，暂停期间也不会自动恢复氧气。
- 暂停状态是存档的一部分：暂停中存档、读档后任务仍处于暂停状态，
  必须显式 `resume` 才能继续下潜。
- 采集、登记、查看样本、重置等操作不受暂停限制（暂停只禁止下潜）。

## 损坏存档后的行为说明

存档读写经过 `save_game` / `load_game` / `load_or_new` 三个入口：

1. `save_game` 采用「写临时文件 + 原子替换」，正常写入不会产生半截存档。
2. `load_game` 发现以下任一情况时判定存档损坏：
   - 文件内容不是合法 JSON（或不是 UTF-8 文本）；
   - JSON 结构校验失败（缺少 `oxygen`/`depth`/`capacity`/`next_id` 等
     必需字段或类型不符）。
3. 存档损坏后：
   - 原文件被**隔离**为同目录下的 `<存档名>.corrupt`，不会被静默覆盖，
     便于事后排查或手工救援；
   - `load_game` 抛出 `CorruptSaveError`，由调用方决定如何提示；
   - `load_or_new` 捕获该异常后返回一份全新游戏状态（与文件不存在时一致），
     程序可直接继续；下次 `save_game` 会生成一份干净的新存档。
4. 隔离失败（如跨文件系统、权限问题）不影响 `CorruptSaveError` 的抛出
   与新开局流程。
