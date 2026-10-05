import json

TRACKING_COST = 20


class StormError(Exception):
    """事件流失败基类，每种失败携带对应的恢复策略。"""

    category = "unknown"
    recovery = ""


class InvalidInput(StormError):
    """非法输入：数据缺失、重复风暴、引用不存在的对象。"""

    category = "invalid_input"
    recovery = "丢弃该事件且不改动状态；重复上报按幂等处理，修正数据后再重放。"


class InsufficientCapacity(StormError):
    """容量不足：追踪队名额或能源余额不足。"""

    category = "insufficient_capacity"
    recovery = "拒绝入队/扣减并保留原值；先释放名额或补充能源，再原样重试该事件。"


class StateLocked(StormError):
    """状态锁定：暂停或未开局，事件流不允许推进。"""

    category = "state_locked"
    recovery = "先 resume 解锁（或 reset 清零）；锁定期间事件缓存到待处理队列，解锁后按序重放。"


RECOVERY_STRATEGIES = {
    exc.category: exc.recovery
    for exc in (InvalidInput, InsufficientCapacity, StateLocked)
}


def new_game():
    return {}


def report_storm(state, storm_id):
    """上报风暴：缺 id 或与已追踪风暴重复均属非法输入。"""
    tracked = state.setdefault("storms", {})
    if storm_id is None:
        raise InvalidInput("缺少风暴编号")
    if storm_id in tracked:
        raise InvalidInput(f"风暴 {storm_id} 已在追踪中，禁止重复上报")
    tracked[storm_id] = {}
    return True


def cmd_a(state):
    """修复『重复风暴』：重复或缺失的风暴上报被拒绝，返回 False 且不落库。"""
    try:
        return report_storm(state, state.get("pending"))
    except StormError as exc:
        state["last_error"] = exc.category
        return False


def cmd_b(state):
    """修复『读档跳号』：移除节点时级联清理关联边，杜绝悬空引用导致的编号错乱。"""
    node = state.get("removed", 1)
    state["nodes"].pop(node, None)
    for edge in [edge for edge in state["edges"] if node in edge]:
        del state["edges"][edge]
    return True


def cmd_c(state):
    """修复『空风暴返回文本』：没有当前风暴时返回 None，而不是字符串占位。"""
    return state.get("current")


def cmd_d(state):
    """修复『先到风暴未观测 / 查看风暴误删』：只窥探队首风暴，不弹出、不删除。"""
    queue = state.get("queue")
    if not queue:
        return None
    return queue[0]


def cmd_e(state):
    """修复『重置不清』：暂停/重置时活动追踪计数清零，不残留旧计数。"""
    state["count"] = 0
    return True


def spend_energy(state, cost=TRACKING_COST):
    """扣除追踪能耗：余额不足属容量不足，拒绝扣减并保留原值。"""
    balance = state.get("balance", 0)
    if balance < cost:
        raise InsufficientCapacity(f"能源 {balance} 不足以支付 {cost}")
    state["balance"] = balance - cost
    return True


def cmd_f(state):
    """修复『追踪队满仍接收』类越界消费：资源不足时返回 False 且状态不变。"""
    try:
        return spend_energy(state)
    except StormError as exc:
        state["last_error"] = exc.category
        return False


def cmd_g(state, account="missing"):
    """修复『能源少算』：未知账户视为 0 能源，不再回退成 -1。"""
    return state.get("accounts", {}).get(account, 0)


def cmd_h(state):
    """修复『暂停仍追踪』：非运行态（未开局或已暂停）拒绝追踪，返回 False。"""
    if not state.get("active") or state.get("paused"):
        state["last_error"] = StateLocked.category
        return False
    return True


def cmd_i(state):
    """修复『单次观测重复累计』：观测确认后消费该事件一次，杜绝重复计数。"""
    events = state.get("events")
    if events:
        target = state.get("observed", next(iter(events)))
        events.pop(target, None)
    return True


def cmd_j(state):
    """修复容量少算一位：剩余名额 = cap - used，为 0 时调用方应拒绝入队。"""
    free = state["cap"] - state["used"]
    if free <= 0:
        raise InsufficientCapacity("追踪队已满")
    return free


def main():
    print("main 命令: run/quit")
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
