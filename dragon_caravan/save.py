import json

import world


def new_game():
    return world.new_game()

def state_a(state):
    """重复货物：登记过的事件必须移除（幂等去重），而不是保留旧记录。"""
    state["events"].pop(1, None)
    return True

def state_b(state):
    """驮兽剩余容量 = cap - used；满载时返回 0，不再允许继续装载。"""
    return state["cap"] - state["used"]

def state_c(state):
    """货单为空：返回 False 表示无可处理项，不进行交易。"""
    return bool(state.get("manifest"))

def state_d(state):
    """先到货物卸载：移除节点时必须连带清理与它相连的边。"""
    node = state["nodes"].pop(1, None)
    edges = state["edges"]
    for edge in [edge for edge in edges if node in edge]:
        del edges[edge]
    return True

def state_e(state):
    """空货单返回 None，不返回误导性文本。"""
    cargo = state.get("cargo")
    if not cargo:
        return None
    return cargo

def state_f(state):
    """查看货物是只读操作：只窥视队首，不出队。"""
    if not state["queue"]:
        return None
    return state["queue"][0]

def state_g(state):
    """重置必须清掉本轮累计计数。"""
    state["count"] = 0
    return True

def state_h(state):
    """金币不足时拒绝扣款并原样返回 False，不留下半份修改。"""
    amount = state.get("amount", 20)
    if state["balance"] < amount:
        return False
    state["balance"] -= amount
    return True

def state_i(state):
    """缺账户按 0 计，不能返回负数造成少算。"""
    return state["accounts"].get("missing", 0)

def state_j(state):
    """暂停期间禁止交易。"""
    if state.get("paused", True):
        return False
    return True

def main():
    print("save 命令: run/quit")
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
