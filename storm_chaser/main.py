"""Storm chaser event stream.

事件分三类失败，恢复策略见 RECOVERY_STRATEGIES：

1. InvalidInput   非法输入：风暴为空 / id 非法 / 重复上报。事件被丢弃，状态
                   原样不变；调用方修正载荷后重新发送即可（重复事件天然幂等，
                   忽略即安全）。
2. CapacityFull   容量不足：追踪队已满或能源不足。不做任何改动；调用方应退避
                   排队，等名额释放（风暴被观测/撤出，used 回落）或能源补给后
                   重试。
3. StateLocked    状态锁定：全局暂停或正在存档/读档，追踪类操作一律拒绝；调用方
                   应先恢复（resume）或等待读档完成，再原样重放该事件。
"""

import json

OBSERVATION_COST = 20


class StormError(Exception):
    """所有风暴事件失败的基类。"""


class InvalidInput(StormError):
    """非法输入：空风暴、非法 id、重复上报。恢复：丢弃并修正后重发。"""


class CapacityFull(StormError):
    """容量不足：追踪队满或能源不足。恢复：退避，待名额/能源恢复后重试。"""


class StateLocked(StormError):
    """状态锁定：暂停或存读档中。恢复：解除暂停/等待读档完成后重放。"""


RECOVERY_STRATEGIES = {
    InvalidInput: "discard the malformed event, keep state untouched, resend a corrected payload",
    CapacityFull: "back off and queue the request; retry after a slot frees or energy is recharged",
    StateLocked: "resume the stream or finish save/load, then replay the original event unchanged",
}


def new_game():
    return {
        "storms": {},        # id -> 风暴载荷（登记去重）
        "queue": [],         # 待观测风暴 id，FIFO
        "events": {},        # id -> True，待确认的观测事件（确认后即消费）
        "observed": {},      # id -> 观测次数
        "nodes": {},         # 正在追踪的风暴
        "edges": {},         # 追踪链路 (a, b) -> 权重
        "paused": set(),     # 已暂停（撤出追踪）的风暴 id
        "locked": False,     # 全局暂停/存读档锁
        "balance": 0,        # 当前能源
        "accounts": {},      # 能源账户
        "cap": 0,            # 追踪队容量
        "used": 0,           # 已占用名额
        "count": 0,          # 本季观测计数
        "next_id": 1,        # 下一个风暴编号（存档保持连续，避免读档跳号）
    }


def _require_unlocked(state):
    if state.get("locked"):
        raise StateLocked("stream is paused or saving/loading")


def _storm_id(storm):
    if storm is None:
        raise InvalidInput("storm payload is empty")
    if isinstance(storm, dict):
        storm_id = storm.get("id")
    else:
        storm_id = storm
    if not isinstance(storm_id, int) or isinstance(storm_id, bool) or storm_id <= 0:
        raise InvalidInput("storm id must be a positive integer")
    return storm_id


def report_storm(state, storm=None):
    """接收风暴上报：空载荷/重复/队满分别落入三类失败。"""
    _require_unlocked(state)
    storm_id = _storm_id(storm)
    if storm_id in state.get("storms", {}):
        raise InvalidInput("storm %d already tracked" % storm_id)
    if state.get("used", 0) >= state.get("cap", 0):
        raise CapacityFull("tracking team is full")
    state.setdefault("storms", {})[storm_id] = storm
    state.setdefault("queue", []).append(storm_id)
    state.setdefault("nodes", {})[storm_id] = True
    state["used"] = state.get("used", 0) + 1
    return True


def pause_storm(state, storm_id):
    """暂停追踪：撤出节点并级联删除所有相关链路，避免“暂停仍追踪”。"""
    _require_unlocked(state)
    state.get("nodes", {}).pop(storm_id, None)
    edges = state.get("edges", {})
    for edge in [edge for edge in edges if storm_id in edge]:
        del edges[edge]
    state.setdefault("paused", set()).add(storm_id)
    if storm_id in state.get("queue", []):
        state["queue"].remove(storm_id)
    return True


def current_storm(state):
    """返回队首风暴 id；没有风暴时返回 None，而不是文本。"""
    queue = state.get("queue", [])
    return queue[0] if queue else None


def view_storm(state):
    """查看队首但不移除（查看不得误删）。"""
    return current_storm(state)


def observe_next(state):
    """观测最早到的风暴（FIFO 出队并只计一次）；队空返回 False。"""
    _require_unlocked(state)
    queue = state.get("queue", [])
    if not queue:
        return False
    storm_id = queue.pop(0)
    _record_observation(state, storm_id)
    return storm_id


def _record_observation(state, storm_id):
    # 消费待确认事件：同一事件只可能被累计一次，重复上报直接忽略。
    state.get("events", {}).pop(storm_id, None)
    observed = state.setdefault("observed", {})
    observed[storm_id] = observed.get(storm_id, 0) + 1
    state["count"] = state.get("count", 0) + 1


def record_observation(state, storm_id=1):
    """确认一次观测：消费 pending 事件，防止单次观测被重复累计。"""
    _require_unlocked(state)
    events = state.get("events", {})
    if storm_id not in events:
        return False
    _record_observation(state, storm_id)
    return True


def spend_energy(state, cost=OBSERVATION_COST):
    """扣除能源：余额不足属容量不足，拒绝且一分不扣（杜绝能源少算/透支）。"""
    _require_unlocked(state)
    if state.get("balance", 0) < cost:
        raise CapacityFull("not enough energy")
    state["balance"] -= cost
    return True


def account_balance(state, key="missing"):
    """读取（含读档后缺失的）账户计数：缺失即 0，不能用 -1 哨兵污染计数。"""
    return state.get("accounts", {}).get(key, 0)


def free_slots(state):
    """追踪队剩余名额：cap - used（旧实现多减 1 导致满员判断错误）。"""
    return state.get("cap", 0) - state.get("used", 0)


def reset_season(state):
    """重置：清空一切派生的运行时状态；容量/账户配置与编号序列保留。"""
    state["queue"] = []
    state["events"] = {}
    state["observed"] = {}
    state["nodes"] = {}
    state["edges"] = {}
    state["paused"] = set()
    state["used"] = 0
    state["count"] = 0
    state["locked"] = False
    return True


def save_game(state, path):
    serializable = dict(state)
    serializable["paused"] = list(state.get("paused", set()))
    serializable["edges"] = {
        "%d:%d" % edge: weight for edge, weight in state.get("edges", {}).items()
    }
    with open(path, "w") as handle:
        json.dump(serializable, handle)
    return True


def load_game(path):
    with open(path) as handle:
        raw = json.load(handle)
    raw["paused"] = set(raw.get("paused", []))
    raw["edges"] = {
        tuple(map(int, key.split(":"))): weight
        for key, weight in raw.get("edges", {}).items()
    }
    # 编号直接沿用存档的 next_id（缺档则按已登记最大号续号），避免读档跳号。
    registered = [0] + [sid for sid in raw.get("storms", {}) if isinstance(sid, int)]
    raw["next_id"] = raw.get("next_id") or (max(registered) + 1)
    return raw


# 兼容既有命令名（cmd_a..cmd_j 为事件流入口）。命令层把三类失败统一折叠为
# False/None，分类异常仍可通过 dispatch 捕获并按 RECOVERY_STRATEGIES 恢复。
_COMMANDS = {
    "a": report_storm,
    "b": pause_storm,
    "c": current_storm,
    "d": view_storm,
    "e": reset_season,
    "f": spend_energy,
    "g": account_balance,
    "h": observe_next,
    "i": record_observation,
    "j": free_slots,
}

_DEFAULTS = {"b": (1,), "f": (20,), "g": ("missing",), "i": (1,)}


def dispatch(state, name, *args):
    """分类派发：抛出 InvalidInput / CapacityFull / StateLocked 之一。"""
    return _COMMANDS[name](state, *args)


def _wrap(name):
    handler = _COMMANDS[name]

    def command(state, *args):
        args = args or _DEFAULTS.get(name, ())
        try:
            return handler(state, *args)
        except (InvalidInput, CapacityFull, StateLocked):
            return False if name != "c" else None

    command.__name__ = "cmd_" + name
    return command


cmd_a = _wrap("a")
cmd_b = _wrap("b")
cmd_c = _wrap("c")
cmd_d = _wrap("d")
cmd_e = _wrap("e")
cmd_f = _wrap("f")
cmd_g = _wrap("g")
cmd_h = _wrap("h")
cmd_i = _wrap("i")
cmd_j = _wrap("j")


def main():
    print("main 命令: report/view/observe/reset/save/load/quit")
    state = new_game()
    while True:
        try:
            raw = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not raw or raw == "quit":
            break
        parts = raw.split()
        try:
            if parts[0] == "report":
                dispatch(state, "a", {"id": int(parts[1])})
            elif parts[0] == "view":
                print(dispatch(state, "d"))
            elif parts[0] == "observe":
                print(dispatch(state, "h"))
            elif parts[0] == "reset":
                dispatch(state, "e")
            elif parts[0] == "save":
                save_game(state, parts[1])
            elif parts[0] == "load":
                state = load_game(parts[1])
            else:
                print("unknown command")
                continue
            print("ok")
        except StormError as exc:
            strategy = RECOVERY_STRATEGIES[type(exc)]
            print("%s: %s | recovery: %s" % (type(exc).__name__, exc, strategy))


if __name__ == "__main__":
    main()
