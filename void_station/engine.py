"""void_station 虚空站资源调度引擎。

规则要点:
- 补给单号唯一, 重复补给会被拒绝 (不重复入库)。
- 虚空舱容量有限, 舱满时拒绝继续接收。
- 查看空舱返回空列表 (CLI 显示 "empty"), 且查看不会删除物资。
- 出舱分配总是取最早到达 (arrival 最小) 的物资。
- 站点暂停 (pause) 期间拒绝运输。
- 每次运输固定消耗 10 点能量, 能量不足拒绝运输。
- 同一批货物只会运输一次, 不会重复累计。
- reset 会清空全部状态 (舱位/队列/在途/能量/编号)。
- 存档/读档后编号连续, 不跳号。
"""

import json
import os

SHIP_COST = 10
DEFAULT_CAPACITY = 3
DEFAULT_ENERGY = 25


def new_game():
    return {
        "next_id": 1,
        "capacity": DEFAULT_CAPACITY,
        "energy": DEFAULT_ENERGY,
        "paused": False,
        "supplies": {},      # supply_id -> arrival
        "arrival_counter": 0,
        "bay": [],           # 舱内物资 (字典序即到达顺序)
        "queue": [],         # 等待装船的货物编号 (FIFO)
        "in_transit": set(), # 已装船在途的货物编号
        "shipped": 0,        # 已完成运输次数
        "total_shipped": 0,  # 已运出的货物总数
    }


def _next_id(state):
    """返回下一个编号并递增。读档后 next_id 被恢复, 编号连续不跳号。"""
    nid = state["next_id"]
    state["next_id"] += 1
    return nid


def supply(state, supply_id):
    """接收补给。重复单号或舱满时拒绝, 返回 False。"""
    if supply_id in state["supplies"]:
        return False
    if len(state["bay"]) >= state["capacity"]:
        return False
    state["arrival_counter"] += 1
    state["supplies"][supply_id] = state["arrival_counter"]
    state["bay"].append(supply_id)
    return True


def view_bay(state):
    """查看舱内物资。只读操作, 不会删除任何物资; 空舱返回空列表。"""
    return list(state["bay"])


def allocate(state):
    """分配最早到达的物资出舱。空舱返回 None。"""
    if not state["bay"]:
        return None
    earliest = min(state["bay"], key=lambda sid: state["supplies"][sid])
    state["bay"].remove(earliest)
    del state["supplies"][earliest]
    return earliest


def enqueue(state, item):
    """货物进入运输队列, 返回其运输编号。"""
    state["queue"].append(item)
    return _next_id(state)


def ship(state):
    """按 FIFO 运出队首货物。

    暂停中、队列空、能量不足或货物已在途时拒绝, 返回 None。
    每次运输只消耗一次能量, 同一批货物只累计一次。
    """
    if state["paused"]:
        return None
    if not state["queue"]:
        return None
    if state["energy"] < SHIP_COST:
        return None
    item = state["queue"][0]
    if item in state["in_transit"]:
        return None
    state["queue"].pop(0)
    state["in_transit"].add(item)
    state["energy"] -= SHIP_COST
    state["shipped"] += 1
    state["total_shipped"] += 1
    return item


def recharge(state, amount):
    state["energy"] += amount
    return state["energy"]


def pause(state):
    state["paused"] = True
    return True


def resume(state):
    state["paused"] = False
    return True


def reset(state):
    """重置为初始状态, 清空全部数据 (包括编号与能量)。"""
    state.clear()
    state.update(new_game())
    return True


def save(state, path):
    data = dict(state)
    data["in_transit"] = sorted(state["in_transit"])
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh)
    return True


def load(state, path):
    """读档。恢复 next_id, 保证之后编号连续不跳号。"""
    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    data["in_transit"] = set(data.get("in_transit", []))
    state.clear()
    state.update(data)
    return True


def run_command(state, line):
    """执行一行 CLI 命令, 返回输出文本。"""
    parts = line.split()
    if not parts:
        return "ERR empty command"
    cmd, args = parts[0], parts[1:]
    try:
        if cmd == "supply":
            ok = supply(state, args[0])
            return "OK supply " + args[0] if ok else "ERR supply " + args[0]
        if cmd == "view":
            bay = view_bay(state)
            return "bay " + (" ".join(bay) if bay else "empty")
        if cmd == "allocate":
            item = allocate(state)
            return "alloc " + item if item is not None else "alloc none"
        if cmd == "enqueue":
            return "enqueued " + str(enqueue(state, args[0]))
        if cmd == "ship":
            item = ship(state)
            return "shipped " + item if item is not None else "ERR ship"
        if cmd == "recharge":
            return "energy " + str(recharge(state, int(args[0])))
        if cmd == "pause":
            pause(state)
            return "paused"
        if cmd == "resume":
            resume(state)
            return "resumed"
        if cmd == "reset":
            reset(state)
            return "reset done"
        if cmd == "save":
            save(state, args[0])
            return "saved"
        if cmd == "load":
            load(state, args[0])
            return "loaded"
        if cmd == "status":
            return "status energy={} shipped={} bay={} queue={}".format(
                state["energy"], state["shipped"],
                len(state["bay"]), len(state["queue"]))
        return "ERR unknown command"
    except (IndexError, ValueError) as exc:
        return "ERR " + str(exc)


def main():
    state = new_game()
    print("void_station 命令: supply/view/allocate/enqueue/ship/recharge/"
          "pause/resume/reset/save/load/status/quit")
    while True:
        try:
            raw = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not raw or raw == "quit":
            break
        print(run_command(state, raw))


if __name__ == "__main__":
    main()
