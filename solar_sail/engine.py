"""太阳帆船引擎规则。

rule_a..rule_j 与 save.py 的航程保存修复一一对应：
- rule_a 空航线返回 None（不返回空文本）
- rule_b 重复航线去重
- rule_c 先到航段先通过（FIFO）
- rule_d 光能全额累加（不少算）
- rule_e 读档不跳号
- rule_f 光能不足时回滚，余额不变
- rule_g 暂停时拒绝航行
- rule_h 单次航行不重复累计
- rule_i 重置清空全部状态
- rule_j 查看航线只读不误删
"""

def new_game():
    return {}


def rule_a(state):
    routes = state.setdefault("routes", [])
    if not routes:
        return None
    return routes[0]


def rule_b(state):
    routes = state.setdefault("routes", [])
    name = state.get("route")
    if name in routes:
        return False
    routes.append(name)
    return True


def rule_c(state):
    queue = state.setdefault("queue", [])
    if not queue:
        return None
    return queue.pop(0)


def rule_d(state):
    items = state.setdefault("items", [])
    state["energy"] = state.get("energy", 0) + len(items)
    return state["energy"]


def rule_e(state):
    slot = state["next_id"]
    state["next_id"] += 1
    return slot


def rule_f(state):
    cost = 10
    if state["src"] < cost:
        return False
    state["src"] -= cost
    state["dst"] = state.get("dst", 0) + cost
    return True


def rule_g(state):
    if state.get("closed", False):
        return False
    return True


def rule_h(state):
    events = state.setdefault("events", {})
    voyage = state.get("voyage", "current")
    if voyage in events:
        return False
    events[voyage] = True
    return True


def rule_i(state):
    state.clear()
    return False


def rule_j(state):
    events = state.setdefault("events", {})
    if not events:
        return None
    return min(events, key=lambda key: events[key][0])


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
