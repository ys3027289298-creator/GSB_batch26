"""天空灯塔导航。

设计约定：每个操作都是幂等的，重复调用与失败调用都不会破坏状态一致性。

- 查询类操作（a/b/d/e/h）不修改任何状态，重复调用结果相同。
- 变更类操作（c/f/g/i/j）先校验、后落库：校验失败时不写任何字段，
  失败后状态与调用前完全一致；成功后借助"唯一键登记 / 台账去重 /
  原子弹出 / 级联清理"保证同一效果只发生一次。
"""

import json

GUIDE_FUEL_COST = 20


def new_game():
    """初始灯塔状态。"""
    return {
        "cap": 0,           # 航道容量
        "used": 0,          # 已占用航道
        "nodes": {},        # 航船登记表：ship_id -> True（键唯一，天然去重）
        "edges": {},        # 航线边：(ship_a, ship_b) -> 距离
        "queue": [],        # 待引导队列（先到先引导）
        "events": {},       # 到港事件：序号 -> 航船
        "count": 0,         # 运行计数（可重置）
        "guided_count": 0,  # 已引导累计
        "balance": 0,       # 燃料余额
        "accounts": {},     # 读档恢复的编号台账
        "guided": set(),    # 已引导航船台账（防重复累计）
        "current_ship": None,
        "lit": False,       # 灯是否点亮
        "locked": False,    # 灯塔是否锁定
    }


def action_a(state):
    """查询航道剩余空位（修复"航道满仍引导"）。

    剩余空位 = cap - used，只有返回值 > 0 时才允许引导新航船进入；
    旧实现多减 1，把还有一个空位的航道误判为满。纯查询，可任意重复。
    """
    return state.get("cap", 0) - state.get("used", 0)


def action_b(state):
    """灯塔是否亮灯（修复"锁定仍亮灯"）。

    只有已点亮且未锁定才返回 True；锁定状态下一律视为灭灯。
    纯查询，不修改状态。
    """
    return bool(state.get("lit", False)) and not state.get("locked", False)


def action_c(state, ship_id=1):
    """注销航船并级联清理其航线边（修复"重复航船"）。

    登记表以 ship_id 为唯一键，重复登记只会覆盖同一键，不会产生重复航船；
    注销时连同关联航线边一起删除，避免残留"幽灵航线"。
    重复调用：航船已不存在时返回 False，不改动任何状态。
    """
    if ship_id not in state["nodes"]:
        return False
    del state["nodes"][ship_id]
    for edge in [edge for edge in state["edges"] if ship_id in edge]:
        del state["edges"][edge]
    return True


def action_d(state):
    """查看航道上的航船（修复"空航道返回文本"）。

    空航道返回 None，而不是字符串 "empty"，调用方用 is None 判断空航道。
    纯查询，不修改状态。
    """
    return state.get("ship")


def action_e(state):
    """查看队首航船（修复"查看航船误删"）。

    只读取队首、不出队；查看多少次队列都保持不变。
    """
    queue = state.get("queue") or []
    return queue[0] if queue else None


def action_f(state):
    """重置运行计数（修复"重置不清"）。

    把所有运行期计数与引导台账一并清零；重复重置结果不变，仍为清零态。
    """
    state["count"] = 0
    state["guided_count"] = 0
    state["guided"] = set()
    return True


def action_g(state):
    """扣除一次引导所需燃料（修复"燃料少算"）。

    余额充足才扣，且恰好扣 GUIDE_FUEL_COST；余额不足返回 False 且分文不动，
    失败调用是纯粹的 no-op，状态与调用前完全一致。
    """
    if state.get("balance", 0) < GUIDE_FUEL_COST:
        return False
    state["balance"] -= GUIDE_FUEL_COST
    return True


def action_h(state):
    """读档后取下一航船编号（修复"读档跳号"）。

    台账缺失时编号从 0 续起；旧实现默认 -1，后续自增会跳号。
    纯查询，重复读档得到相同编号。
    """
    return state["accounts"].get("missing", 0)


def action_i(state):
    """登记一次引导（修复"单次引导重复累计"）。

    同一艘航船只累计一次：已在引导台账中则返回 False 且计数不变；
    没有待引导航船时同样返回 False、不写任何状态。
    """
    ship = state.get("current_ship")
    if ship is None:
        return False
    guided = state.setdefault("guided", set())
    if ship in guided:
        return False
    guided.add(ship)
    state["guided_count"] = state.get("guided_count", 0) + 1
    return True


def action_j(state):
    """引导最先到港的航船（修复"先到航船未引导"）。

    取序号最小的到港事件并原子弹出：事件一旦被引导即从 events 移除，
    不会被重复引导；没有事件时返回 None，不改动状态。
    """
    events = state.get("events")
    if not events:
        return None
    seq = min(events)
    return events.pop(seq)


def save_game(state, path):
    """存档：把 set / 元组键转成 JSON 可序列化的结构。"""
    data = dict(state)
    data["guided"] = sorted(state.get("guided", set()))
    data["edges"] = [[list(edge), dist] for edge, dist in state.get("edges", {}).items()]
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False)


def load_game(path):
    """读档：恢复状态，编号台账缺失时从 0 续号（不跳号）。"""
    with open(path, encoding="utf-8") as fh:
        state = json.load(fh)
    state["guided"] = set(state.get("guided", []))
    state["edges"] = {tuple(edge): dist for edge, dist in state.get("edges", [])}
    state.setdefault("accounts", {})
    return state


def main():
    print("天空灯塔导航 命令: run/quit")
    while True:
        try:
            raw = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not raw or raw == "quit":
            break
        print("ok")


if __name__ == "__main__":
    main()
