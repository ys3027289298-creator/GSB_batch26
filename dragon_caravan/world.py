"""龙商队交易状态机。

关键不变量：
- 同一种货物只保留一条记录（数量合并），同一事件重复提交不会重复入账。
- 驮兽容量不足时拒绝装载，不写入任何半截状态。
- 空货单返回 None（而不是给调用方一段文本）。
- 抵达货物按 FIFO 卸载，先到先卸。
- 暂停期间拒绝一切交易动作。
- 查看货物是只读操作，不修改队列。
- 金币按 qty * unit_price 精确结算，缺账户按 0 计。
- 单次交易只累计一次计数。
- reset_round 清零本轮计数；存档/读档保留 phase 与 next_id，读档后继续推进而非重来。
"""

import json

SAVE_VERSION = 1

PHASE_RUNNING = "running"
PHASE_PAUSED = "paused"
PHASE_CLOSED = "closed"

_PHASE_TRANSITIONS = {
    PHASE_RUNNING: {PHASE_PAUSED, PHASE_CLOSED},
    PHASE_PAUSED: {PHASE_RUNNING, PHASE_CLOSED},
    PHASE_CLOSED: set(),
}


class CaravanError(Exception):
    """业务规则被拒绝；抛出前状态不会发生任何修改。"""


def new_game():
    return {
        "version": SAVE_VERSION,
        "phase": PHASE_RUNNING,
        "gold": 0,
        "beast_cap": 0,
        "used": 0,
        "cargo": {},
        "arrivals": [],
        "round_count": 0,
        "processed_events": {},
        "next_id": 1,
        "accounts": {},
    }


def _set_phase(state, target):
    current = state["phase"]
    if target not in _PHASE_TRANSITIONS[current]:
        raise CaravanError(f"illegal phase transition: {current} -> {target}")
    state["phase"] = target


def _require_running(state):
    if state["phase"] == PHASE_PAUSED:
        raise CaravanError("caravan is paused")
    if state["phase"] != PHASE_RUNNING:
        raise CaravanError(f"caravan is {state['phase']}")


def pause(state):
    _set_phase(state, PHASE_PAUSED)
    return True


def resume(state):
    _set_phase(state, PHASE_RUNNING)
    return True


def close(state):
    _set_phase(state, PHASE_CLOSED)
    return True


def remaining_capacity(state):
    return state["beast_cap"] - state["used"]


def _next_id(state):
    cargo_id = state["next_id"]
    state["next_id"] += 1
    return cargo_id


def submit_cargo(state, item, qty, event_id):
    """登记货物。同一 event_id 重复提交幂等返回；同种货物数量合并为一条。"""
    _require_running(state)
    if not isinstance(item, str) or not item:
        raise CaravanError("bad item")
    if qty <= 0:
        raise CaravanError("bad qty")
    existing = state["processed_events"].get(event_id)
    if existing is not None:
        return existing
    cargo_id = _next_id(state)
    state["cargo"][item] = state["cargo"].get(item, 0) + qty
    state["processed_events"][event_id] = cargo_id
    return cargo_id


def load_beasts(state, weight):
    """往驮兽上装货；容量不足时整体拒绝，used 不变。"""
    _require_running(state)
    if weight <= 0:
        raise CaravanError("bad weight")
    if state["used"] + weight > state["beast_cap"]:
        raise CaravanError("beasts are full")
    state["used"] += weight
    return remaining_capacity(state)


def view_cargo(state):
    """只读查看货单；空货单返回 None，绝不返回误导性文本。"""
    cargo = state["cargo"]
    if not cargo:
        return None
    return dict(cargo)


def receive_arrival(state, item, qty):
    """货物抵达，进入 FIFO 队列尾部。"""
    _require_running(state)
    if qty <= 0:
        raise CaravanError("bad qty")
    arrival = {"id": _next_id(state), "item": item, "qty": qty}
    state["arrivals"].append(arrival)
    return arrival["id"]


def peek_arrival(state):
    """查看最先抵达的货物，不出队。"""
    arrivals = state["arrivals"]
    if not arrivals:
        return None
    return dict(arrivals[0])


def unload_next(state):
    """卸载最先抵达的货物（FIFO）。"""
    _require_running(state)
    if not state["arrivals"]:
        return None
    return state["arrivals"].pop(0)


def account_balance(state, name):
    return state["accounts"].get(name, 0)


def deposit(state, name, amount):
    if amount < 0:
        raise CaravanError("bad amount")
    state["accounts"][name] = account_balance(state, name) + amount
    return state["accounts"][name]


def settle_trade(state, item, qty, unit_price):
    """完成一笔交易：先做全部校验，再一次性落账，计数只加一次。"""
    _require_running(state)
    if qty <= 0 or unit_price < 0:
        raise CaravanError("bad trade")
    total = qty * unit_price
    held = state["cargo"].get(item, 0)
    if held < qty:
        raise CaravanError("not enough cargo")
    if state["gold"] < total:
        raise CaravanError("not enough gold")
    remaining = held - qty
    if remaining:
        state["cargo"][item] = remaining
    else:
        del state["cargo"][item]
    state["gold"] -= total
    state["round_count"] += 1
    return total


def reset_round(state):
    """清空本轮交易累计；驮兽实载与货物不在本轮重置范围内。"""
    state["round_count"] = 0
    return True


def save_game(state):
    """序列化；phase 与 next_id 一并保存，读档后接着走。"""
    return json.dumps(state, ensure_ascii=False, sort_keys=True)


def load_game(payload):
    data = json.loads(payload)
    state = new_game()
    state.update(data)
    return state


def main():
    print("world 命令: run/quit")
    state = new_game()
    while True:
        try:
            raw = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not raw or raw == "quit":
            break
        if raw == "run":
            print(save_game(state))
        else:
            print("unknown command")


if __name__ == "__main__":
    main()
