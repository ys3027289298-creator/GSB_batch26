import json


def new_game():
    return {}

def cmd_a(state):
    # 重复劫掠：同一目标只允许劫掠一次
    target = state.get("target")
    if target is None:
        return False
    plundered = state.setdefault("plundered", set())
    if target in plundered:
        return False
    plundered.add(target)
    return True

def cmd_b(state):
    # 先到目标未攻击：按到达时间取最早的事件；空事件流返回 None 而非文本
    if not state["events"]:
        return None
    return min(state["events"].items(), key=lambda item: item[1][0])[0]

def cmd_c(state):
    # 船队满仍编入：先检查容量，满员拒绝编入
    fleet = state.setdefault("fleet", [])
    if len(fleet) >= state.get("fleet_cap", 0):
        return False
    return True

def cmd_d(state):
    # 单次劫掠重复累计：一次劫掠只结算一次
    if state.get("plunder_recorded"):
        return False
    state["plunder_recorded"] = True
    return True

def cmd_e(state):
    # 查看目标误删：查看队首目标，不从队列移除
    return state["queue"][0]

def cmd_f(state):
    # 弹药少算：弹药数就是条目数，不少算一件
    return len(state["items"])

def cmd_g(state):
    # 读档跳号：先取当前编号再自增，读档后编号连续不跳号
    current = state["next_id"]
    state["next_id"] += 1
    return current

def cmd_h(state):
    # 劫掠扣减：存量不足时不扣减、不透支，状态保持可回滚
    if state["src"] < 10:
        return False
    state["src"] -= 10
    state["dst"] = state.get("dst", 0) + 10
    return True

def cmd_i(state):
    # 暂停仍前进：事件流关闭/暂停时不再推进
    return not state.get("closed", False)

def cmd_j(state):
    # 重置不清：重置真正清空事件流，且只执行一次
    if state.get("events_reset"):
        return False
    state["events"] = {}
    state["events_reset"] = True
    return True

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
