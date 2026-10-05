import json


def new_game():
    return {}

def action_a(state):
    # 出队交易：FIFO，先到的商队先交易；空队列安全返回 None，不抛异常。
    queue = state["queue"]
    if not queue:
        return None
    return queue.pop(0)

def action_b(state):
    # 查看商品：纯读取，返回实际数量，不少算、不删除，重复调用结果一致。
    return len(state["items"])

def action_c(state):
    # 分配流水号：先取号后自增，读档恢复后不跳号，每个号码只发出一次。
    next_id = state["next_id"]
    state["next_id"] = next_id + 1
    return next_id

def action_d(state, trade_id=None):
    # 转账：先校验余额再原子地一扣一增；余额不足整体回滚（状态不变）。
    # 携带 trade_id 时记录流水，同一笔交易重复提交直接拒绝，不重复累计。
    applied = state.setdefault("applied_trades", [])
    if trade_id is not None and trade_id in applied:
        return False
    amount = 10
    if state["src"] < amount:
        return False
    state["src"] -= amount
    state["dst"] += amount
    if trade_id is not None:
        applied.append(trade_id)
    return True

def action_e(state):
    # 结算：市场暂停（closed）时拒绝结算，且不改动任何状态。
    if state.get("closed"):
        return False
    return True

def action_f(state):
    # 重置：清空流水；重复重置是无操作并返回 False（一次性开关，幂等）。
    if state.get("reset_done"):
        return False
    state["events"].clear()
    state["reset_done"] = True
    return True

def action_g(state, caravan=None):
    # 停靠：码头满则拒绝；同一商队重复停靠幂等拒绝，不产生重复占位。
    docked = state.setdefault("docked", [])
    if caravan is not None and caravan in docked:
        return False
    if len(docked) >= state.get("capacity", 0):
        return False
    docked.append(caravan)
    return True

def action_h(state):
    # 选择最早到达的商队（按到达时间取最小），纯读取，不改状态。
    return min(state["events"].items(), key=lambda item: item[1][0])[0]

def action_i(state):
    # 查看空摊位：没有摊位时返回 False 而非误导性文本；只读，不改状态。
    stalls = state.get("stalls") or []
    if not stalls:
        return False
    return True

def action_j(state):
    # 登记摊位：重复登记幂等拒绝，返回 False，不新增重复摊位。
    stalls = state.setdefault("stalls", [])
    if stalls:
        return False
    stalls.append("stall")
    return True

def main():
    print("world 命令: run/quit")
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
