"""暗影市场交易核心。

设计原则:每个操作幂等。重复调用返回首次结果而不重复改变状态;
失败调用在验证阶段即返回,不产生任何部分写入(交易级回滚)。
"""

import copy
import json

DOCK_CAPACITY = 3


def new_game():
    return {
        "stalls": {},        # stall_id -> {"owner": str, "goods": {item: qty}}
        "dock": [],          # 已停靠商队 id, 长度受 dock_capacity 限制
        "dock_capacity": DOCK_CAPACITY,
        "queue": [],         # 等待停靠的商队, 先进先出
        "paused": False,
        "coins": 0,          # 已结算影币
        "trades": {},        # trade_id -> 交易回执(幂等键)
        "ledger": [],        # 流水: {"trade_id", "amount", "settled"}
        "next_id": 1,        # 自增 id, 随存档持久化
    }


def _alloc_id(state, prefix):
    value = "%s-%d" % (prefix, state["next_id"])
    state["next_id"] += 1
    return value


def register_stall(state, stall_id, owner=""):
    """登记摊位。同一 stall_id 重复登记返回已有摊位, 不产生重复摊位。"""
    stall = state["stalls"].get(stall_id)
    if stall is None:
        stall = {"owner": owner, "goods": {}}
        state["stalls"][stall_id] = stall
    return stall


def arrive_caravan(state, caravan_id=None):
    """商队抵达。已在码头或队列中时重复调用为 no-op;
    码头满时进入等待队列, 不会超额停靠。"""
    if caravan_id is None:
        caravan_id = _alloc_id(state, "caravan")
    if caravan_id in state["dock"]:
        return {"id": caravan_id, "status": "docked"}
    if caravan_id in state["queue"]:
        return {"id": caravan_id, "status": "queued"}
    if len(state["dock"]) < state["dock_capacity"]:
        state["dock"].append(caravan_id)
        return {"id": caravan_id, "status": "docked"}
    state["queue"].append(caravan_id)
    return {"id": caravan_id, "status": "queued"}


def depart_caravan(state, caravan_id):
    """商队离港。离港后按到达顺序从队列补位(先到先交易);
    对不在码头的商队调用为 no-op。"""
    if caravan_id not in state["dock"]:
        return False
    state["dock"].remove(caravan_id)
    while state["queue"] and len(state["dock"]) < state["dock_capacity"]:
        state["dock"].append(state["queue"].pop(0))
    return True


def view_goods(state, stall_id):
    """查看商品。纯读操作, 返回副本, 不修改任何状态;
    空摊位返回空 dict 而非文本。"""
    stall = state["stalls"].get(stall_id)
    if stall is None:
        return {}
    return dict(stall["goods"])


def stock_goods(state, stall_id, item, qty):
    """上架商品。qty 必须为正且摊位存在, 否则失败且状态不变。"""
    if qty <= 0:
        return False
    stall = state["stalls"].get(stall_id)
    if stall is None:
        return False
    stall["goods"][item] = stall["goods"].get(item, 0) + qty
    return True


def trade(state, stall_id, item, qty, price, trade_id=None):
    """交易。以 trade_id 为幂等键: 同一 trade_id 重复调用直接返回
    首次回执, 不重复扣货、不重复记账。暂停中拒绝交易。
    先验证全部前置条件再写入; 写入过程若异常则整体回滚,
    失败调用保证状态与调用前一致。"""
    if trade_id is None:
        trade_id = _alloc_id(state, "trade")
    receipt = state["trades"].get(trade_id)
    if receipt is not None:
        return receipt
    if state["paused"]:
        return {"ok": False, "reason": "paused", "trade_id": trade_id}
    stall = state["stalls"].get(stall_id)
    if stall is None:
        return {"ok": False, "reason": "no_stall", "trade_id": trade_id}
    if qty <= 0 or price < 0:
        return {"ok": False, "reason": "bad_args", "trade_id": trade_id}
    if stall["goods"].get(item, 0) < qty:
        return {"ok": False, "reason": "out_of_stock", "trade_id": trade_id}

    snapshot = (copy.deepcopy(stall["goods"]), len(state["ledger"]))
    try:
        stall["goods"][item] -= qty
        if stall["goods"][item] == 0:
            del stall["goods"][item]
        amount = qty * price
        state["ledger"].append(
            {"trade_id": trade_id, "amount": amount, "settled": False}
        )
    except Exception:
        stall["goods"] = snapshot[0]
        del state["ledger"][snapshot[1]:]
        raise
    receipt = {"ok": True, "trade_id": trade_id, "amount": amount}
    state["trades"][trade_id] = receipt
    return receipt


def settle(state):
    """结算。暂停中为 no-op; 把未结算流水计入影币并标记已结算,
    重复调用时无未结算流水, 不会重复累计。"""
    if state["paused"]:
        return 0
    total = 0
    for entry in state["ledger"]:
        if not entry["settled"]:
            total += entry["amount"]
            entry["settled"] = True
    state["coins"] += total
    return total


def pause(state):
    state["paused"] = True


def resume(state):
    state["paused"] = False


def reset(state):
    """重置。清空摊位、码头、队列、流水与交易记录, 影币归零,
    id 计数归位。重复重置结果相同。"""
    state.clear()
    state.update(new_game())
    return state


def save(state):
    """存档。完整序列化含 next_id 在内的全部状态。"""
    return json.dumps(state, ensure_ascii=False, sort_keys=True)


def load(state, data):
    """读档。整体替换状态并恢复 next_id, 之后分配的 id 不跳号;
    同一存档重复读入结果一致。"""
    loaded = json.loads(data)
    state.clear()
    state.update(loaded)
    return state


def main():
    print("engine 命令: run/quit")
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
