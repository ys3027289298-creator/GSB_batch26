"""幽灵港调度:船只到港排队、引航入泊位、出港、查看与存档。"""

import json

BERTH_COUNT = 3
EMPTY_BERTH_TEXT = "空泊位"


def new_game():
    return {
        "ships": {},                 # id -> {"id", "name", "haunting"}
        "queue": [],                 # 等待引航的船只 id,先到先引航
        "berths": [None] * BERTH_COUNT,
        "next_id": 1,
        "piloted": 0,                # 累计引航次数
        "paused": False,
    }


def _find_ship_by_name(state, name):
    for ship in state["ships"].values():
        if ship["name"] == name:
            return ship
    return None


def arrive(state, name, haunting=1):
    if state["paused"]:
        return "暂停中 禁止进出"
    if _find_ship_by_name(state, name) is not None:
        return "拒绝 重复船只 {}".format(name)
    ship = {"id": state["next_id"], "name": name, "haunting": haunting}
    state["ships"][ship["id"]] = ship
    state["queue"].append(ship["id"])
    state["next_id"] += 1
    return "进港 {} #{}".format(name, ship["id"])


def pilot(state):
    """引航:把最早到达的等待船只带进第一个空泊位。"""
    if state["paused"]:
        return "暂停中 禁止进出"
    if not state["queue"]:
        return "没有等待的船只"
    if None not in state["berths"]:
        return "泊位已满 无法停靠"
    ship_id = state["queue"].pop(0)
    berth_index = state["berths"].index(None)
    state["berths"][berth_index] = ship_id
    state["piloted"] += 1
    return "引航 {} 入泊位{}".format(state["ships"][ship_id]["name"], berth_index)


def depart(state, name):
    if state["paused"]:
        return "暂停中 禁止进出"
    ship = _find_ship_by_name(state, name)
    if ship is None or ship["id"] not in state["berths"]:
        return "船只不在泊位 {}".format(name)
    state["berths"][state["berths"].index(ship["id"])] = None
    del state["ships"][ship["id"]]
    return "出港 {}".format(name)


def berth_status(state, index):
    if index < 0 or index >= len(state["berths"]):
        return "无此泊位"
    ship_id = state["berths"][index]
    if ship_id is None:
        return EMPTY_BERTH_TEXT
    return state["ships"][ship_id]["name"]


def view(state, name):
    """只查看,不改动任何状态。"""
    ship = _find_ship_by_name(state, name)
    if ship is None:
        return "查无此船 {}".format(name)
    return "船只 {} #{} 灵异值{}".format(ship["name"], ship["id"], ship["haunting"])


def total_haunting(state):
    """灵异值:等待队列与泊位中的船只全部计入。"""
    return sum(ship["haunting"] for ship in state["ships"].values())


def status(state):
    used = sum(1 for ship_id in state["berths"] if ship_id is not None)
    return "状态 等待{} 泊位{}/{} 引航{} 灵异{} 下一编号#{} 暂停{}".format(
        len(state["queue"]), used, len(state["berths"]), state["piloted"],
        total_haunting(state), state["next_id"],
        "开" if state["paused"] else "关",
    )


def reset(state):
    fresh = new_game()
    state.clear()
    state.update(fresh)
    return "已重置"


def save(state, path):
    data = {
        "ships": {str(ship_id): ship for ship_id, ship in state["ships"].items()},
        "queue": list(state["queue"]),
        "berths": list(state["berths"]),
        "next_id": state["next_id"],
        "piloted": state["piloted"],
        "paused": state["paused"],
    }
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False)
    return "已存档 {}".format(path)


def load(state, path):
    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    state.clear()
    state.update({
        "ships": {int(ship_id): ship for ship_id, ship in data["ships"].items()},
        "queue": list(data["queue"]),
        "berths": list(data["berths"]),
        "next_id": data["next_id"],
        "piloted": data["piloted"],
        "paused": data["paused"],
    })
    return "已读档 {}".format(path)


def main():
    state = new_game()
    print("幽灵港调度 命令: arrive/pilot/depart/berth/view/haunting/pause/resume/reset/save/load/status/quit")
    while True:
        try:
            raw = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not raw:
            continue
        parts = raw.split()
        cmd, args = parts[0], parts[1:]
        if cmd == "quit":
            break
        elif cmd == "arrive" and len(args) >= 1:
            haunting = int(args[1]) if len(args) > 1 else 1
            print(arrive(state, args[0], haunting))
        elif cmd == "pilot":
            print(pilot(state))
        elif cmd == "depart" and len(args) == 1:
            print(depart(state, args[0]))
        elif cmd == "berth" and len(args) == 1:
            print("泊位{} {}".format(args[0], berth_status(state, int(args[0]))))
        elif cmd == "view" and len(args) == 1:
            print(view(state, args[0]))
        elif cmd == "haunting":
            print("灵异值 {}".format(total_haunting(state)))
        elif cmd == "pause":
            state["paused"] = True
            print("已暂停")
        elif cmd == "resume":
            state["paused"] = False
            print("已恢复")
        elif cmd == "reset":
            print(reset(state))
        elif cmd == "save" and len(args) == 1:
            print(save(state, args[0]))
        elif cmd == "load" and len(args) == 1:
            print(load(state, args[0]))
        elif cmd == "status":
            print(status(state))
        else:
            print("未知命令 {}".format(raw))


if __name__ == "__main__":
    main()
