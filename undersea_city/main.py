"""海底城市调度：区段舱室、物资运输、氧气与暂停/存档。

状态不变量：
1. 区段名唯一：任意两个区段的 name 不同。
2. 容量守恒：每个区段 0 <= occupants <= capacity。
3. 只读路径无副作用：view 等查询命令不修改 state。
4. 物资守恒且 FIFO：队列按到达顺序分配；
   已交付总量 + 在途总量 == 到达总量。
5. 暂停即停：paused 为 True 时 dispatch 不改变任何状态。
6. 氧气可核算：oxygen == BASE_OXYGEN - 所有区段 occupants 之和 * 2。
7. 调度计数：dispatch_count 每执行一轮有效调度恰好 +1。
8. 重置等价：reset 后 state 与 new_game() 完全一致（原地清空）。
9. 编号单调：next_id 严格大于所有现存区段 id，存档/读档后不重用不跳号。
10. 空值语义：查询不存在的区段返回 None，不返回误导性文本。
"""

import json
import copy

BASE_OXYGEN = 100
OXYGEN_PER_PERSON = 2

# 模块级“调度历史”，供统计功能使用。
_HISTORY = []


def new_game():
    return {
        "sections": {},      # id -> {"name", "capacity", "occupants"}
        "queue": [],         # 待分配物资 [sid, amount]，按到达顺序
        "delivered": {},     # sid -> 已分配批次列表
        "oxygen": BASE_OXYGEN,
        "paused": False,
        "dispatch_count": 0,
        "next_id": 1,
    }


def _find(state, name):
    for sid, sec in state["sections"].items():
        if sec["name"] == name:
            return sid, sec
    return None, None


def cmd_add(state, name, capacity):
    _, existing = _find(state, name)
    if existing is not None:
        return None
    sid = state["next_id"]
    state["next_id"] += 1
    state["sections"][sid] = {"name": name, "capacity": capacity, "occupants": 0}
    return sid


def cmd_enter(state, name, n):
    _, sec = _find(state, name)
    if sec is None:
        return False
    if sec["occupants"] + n > sec["capacity"]:
        return False
    sec["occupants"] += n
    return True


def cmd_view(state, name):
    sid, sec = _find(state, name)
    if sec is None:
        return None
    return {"id": sid, **sec}


def cmd_deliver(state, name, amount):
    sid, sec = _find(state, name)
    if sec is None:
        return False
    state["queue"].append([sid, amount])
    return True


def cmd_dispatch(state):
    if state["paused"]:
        return 0
    moved = 0
    while state["queue"]:
        sid, amount = state["queue"].pop(0)
        state["delivered"].setdefault(sid, []).append(amount)
        moved += amount
    if moved:
        state["dispatch_count"] += 1
    _HISTORY.append(copy.deepcopy(state))
    return moved


def cmd_pause(state):
    state["paused"] = True


def cmd_resume(state):
    state["paused"] = False


def cmd_oxygen(state):
    used = 0
    for sec in state["sections"].values():
        used += sec["occupants"] * OXYGEN_PER_PERSON
    state["oxygen"] = BASE_OXYGEN - used
    return state["oxygen"]


def cmd_reset(state):
    state.clear()
    state.update(new_game())
    return True


def cmd_save(state, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(state, f)


def cmd_load(state, path):
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    state.clear()
    state.update(data)
    state["sections"] = {int(k): v for k, v in state["sections"].items()}
    state["delivered"] = {int(k): v for k, v in state["delivered"].items()}


def main():
    state = new_game()
    print("海底城市调度: add/enter/view/deliver/dispatch/pause/resume/"
          "oxygen/reset/save/load/quit")
    while True:
        try:
            raw = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not raw or raw == "quit":
            break
        parts = raw.split()
        cmd, args = parts[0], parts[1:]
        try:
            if cmd == "add":
                print(cmd_add(state, args[0], int(args[1])))
            elif cmd == "enter":
                print(cmd_enter(state, args[0], int(args[1])))
            elif cmd == "view":
                print(cmd_view(state, args[0]))
            elif cmd == "deliver":
                print(cmd_deliver(state, args[0], int(args[1])))
            elif cmd == "dispatch":
                print(cmd_dispatch(state))
            elif cmd == "pause":
                cmd_pause(state)
                print("ok")
            elif cmd == "resume":
                cmd_resume(state)
                print("ok")
            elif cmd == "oxygen":
                print(cmd_oxygen(state))
            elif cmd == "reset":
                cmd_reset(state)
                print("ok")
            elif cmd == "save":
                cmd_save(state, args[0])
                print("ok")
            elif cmd == "load":
                cmd_load(state, args[0])
                print("ok")
            else:
                print("未知命令")
        except (IndexError, ValueError):
            print("参数错误")


if __name__ == "__main__":
    main()
