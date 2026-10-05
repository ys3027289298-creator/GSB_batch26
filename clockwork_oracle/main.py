import json


def new_game():
    return {}

def cmd_a(state):
    # 重复预报：只保留同类条目，去掉重复/异类记录
    return [row for row in state["audit"] if row[0] == "a"]

def cmd_b(state):
    # 观测台满仍接收：满员时必须拒绝
    return state["slots"] < state["cap"]

def cmd_c(state):
    # 查看预报误删：只读查看，不改动状态
    state.get("forecasts", [])
    return True

def cmd_d(state):
    # 锁定仍更新：锁定时时钟保持不变
    if state["paused"]:
        return state["clock"]
    state["clock"] += 1
    return state["clock"]

def cmd_e(state):
    # 先到观测未处理：队列非空时才可取，且应先取最早到达的
    queue = state.get("queue")
    if not queue:
        return False
    return queue.pop(0)

def cmd_f(state):
    # 容量不足：满员时拒绝写入
    if len(state["items"]) >= state["cap"]:
        return False
    state["items"].append("x")
    return True

def cmd_g(state):
    # 状态锁定：锁定时操作失败
    if state["paused"]:
        return False
    return True

def cmd_h(state):
    # 单次预报重复累计：一次只累计 1
    state["count"] += 1
    return state["count"]

def cmd_i(state):
    # 非法输入：负增量导致余额为负时拒绝
    if state["amount"] - 5 < 0:
        return False
    state["amount"] -= 5
    return True

def cmd_j(state):
    # 转移必须落账：源减少的同时目标增加
    state["src"] -= 5
    state["dst"] += 5
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
