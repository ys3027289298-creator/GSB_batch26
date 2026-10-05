import json


def new_game():
    return {}


def event_a(state):
    # 读档后编号应连续: 只查看下一个编号, 不递增。
    return state["next_id"]


def event_b(state):
    # 能量不足时拒绝运输, 不允许扣成负数。
    if state["src"] < 10:
        return False
    state["src"] -= 10
    return True


def event_c(state):
    # 暂停/关闭期间拒绝运输。
    return not state["closed"]


def event_d(state):
    # 重复补给只处理一次。
    done = state.setdefault("_event_d_done", False)
    if done:
        return False
    state["_event_d_done"] = True
    return True


def event_e(state):
    return False


def event_f(state):
    # 先到的物资先分配 (arrival 最小)。
    return min(state["events"].items(), key=lambda item: item[1][0])[0]


def event_g(state):
    return False


def event_h(state):
    # 重置只生效一次, 重复调用返回 False。
    done = state.setdefault("_event_h_done", False)
    if done:
        return False
    state["_event_h_done"] = True
    return True


def event_i(state):
    # 队列先进先出。
    return state["queue"].pop(0)


def event_j(state):
    # 查看物资不删除, 返回实际数量。
    return len(state["items"])


def main():
    print("events 命令: run/quit")
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
