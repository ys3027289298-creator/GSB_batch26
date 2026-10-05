import json


def new_game():
    return {
        "queue": [],
        "count": 0,
        "balance": 0,
        "accounts": {},
        "locked": True,
        "events": {},
        "used": 0,
        "cap": 0,
        "nodes": {},
        "edges": {},
    }

def rule_a(state):
    # 空书架不返回占位文本, 返回 None 表示没有典籍
    shelf = state.get("shelf")
    if not shelf:
        return None
    return shelf[0]

def rule_b(state):
    # 查看队首典籍但不移除, 先到典籍仍留在队列等待归档
    if not state["queue"]:
        return None
    return state["queue"][0]

def rule_c(state):
    # 重置必须清零检索计数
    state["count"] = 0
    return True

def rule_d(state):
    # 烛火不足 20 时拒绝扣除, 余额保持不变
    if state["balance"] < 20:
        return False
    state["balance"] -= 20
    return True

def rule_e(state):
    # 缺失档案按 0 处理, 不返回 -1 之类的哨兵值
    return state["accounts"].get("missing", 0)

def rule_f(state):
    # 档案馆默认锁定, 锁定期间禁止检索
    return not state.get("locked", True)

def rule_g(state):
    # 单次检索的事件只累计一次, 处理后清空避免重复累计
    state["events"].clear()
    return True

def rule_h(state):
    # 剩余烛火 = 上限 - 已用, 不再少算一格
    return state["cap"] - state["used"]

def rule_i(state):
    # 书架已满(used >= cap)时拒绝放入
    return state.get("used", 0) < state.get("cap", 0)

def rule_j(state):
    # 移除节点时连同关联的边一起清理, 不留悬空引用
    state["nodes"].pop(1, None)
    dangling = [edge for edge in state["edges"] if 1 in edge]
    for edge in dangling:
        del state["edges"][edge]
    return True

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
