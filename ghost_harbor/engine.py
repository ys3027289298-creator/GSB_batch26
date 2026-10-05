import json


def new_game():
    return {
        "capacity": 3,
        "docked": [],
        "waiting": [],
        "next_id": 1,
        "piloted": 0,
        "paused": False,
    }


def _find(ships, name):
    for ship in ships:
        if ship["name"] == name:
            return ship
    return None


def cmd_arrive(state, name, haunt):
    if _find(state["waiting"], name) or _find(state["docked"], name):
        return "错误: 船只 %s 已在港内" % name
    ship = {"id": state["next_id"], "name": name, "haunt": haunt}
    state["next_id"] += 1
    state["waiting"].append(ship)
    return "船只 %s 到达, 编号 %d, 排队第 %d 位" % (name, ship["id"], len(state["waiting"]))


def cmd_dock(state):
    if state["paused"]:
        return "港口已暂停, 无法引航"
    if not state["waiting"]:
        return "没有等待的船只"
    if len(state["docked"]) >= state["capacity"]:
        return "泊位已满, 无法停靠"
    ship = state["waiting"].pop(0)
    state["docked"].append(ship)
    state["piloted"] += 1
    return "引航完成: %s 停靠 %d 号泊位" % (ship["name"], len(state["docked"]))


def cmd_undock(state, name):
    if state["paused"]:
        return "港口已暂停, 无法离港"
    ship = _find(state["docked"], name)
    if ship is None:
        return "泊位为空: 没有名为 %s 的船只" % name
    state["docked"].remove(ship)
    return "船只 %s 已离港" % name


def cmd_view(state, name):
    ship = _find(state["docked"], name)
    where = "已停靠"
    if ship is None:
        ship = _find(state["waiting"], name)
        where = "排队中"
    if ship is None:
        return "查无此船: %s" % name
    return "船只 %s: 编号 %d, 灵异值 %d, 状态 %s" % (name, ship["id"], ship["haunt"], where)


def cmd_haunt(state):
    total = sum(s["haunt"] for s in state["docked"])
    total += sum(s["haunt"] for s in state["waiting"])
    return "港口灵异值总计: %d" % total


def cmd_status(state):
    return "状态: 暂停=%s 泊位 %d/%d 排队 %d 引航次数 %d 下一编号 %d" % (
        "是" if state["paused"] else "否",
        len(state["docked"]),
        state["capacity"],
        len(state["waiting"]),
        state["piloted"],
        state["next_id"],
    )


def cmd_pause(state):
    state["paused"] = True
    return "港口已暂停"


def cmd_resume(state):
    state["paused"] = False
    return "港口已恢复"


def cmd_reset(state):
    state.clear()
    state.update(new_game())
    return "港口已重置"


def cmd_save(state, path):
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(state, fh, ensure_ascii=False)
    return "已存档到 %s" % path


def cmd_load(state, path):
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, ValueError):
        return "读档失败: %s" % path
    state.clear()
    state.update(new_game())
    state.update(data)
    max_id = max([s["id"] for s in state["docked"] + state["waiting"]], default=0)
    if state["next_id"] <= max_id:
        state["next_id"] = max_id + 1
    return "已读档自 %s" % path


HELP = (
    "命令: arrive <船名> <灵异值> | dock | undock <船名> | view <船名> | "
    "haunt | status | pause | resume | reset | save <路径> | load <路径> | quit"
)


def handle_command(state, raw):
    parts = raw.split()
    cmd = parts[0]
    args = parts[1:]
    if cmd == "arrive" and len(args) == 2:
        try:
            haunt = int(args[1])
        except ValueError:
            return "错误: 灵异值必须是整数"
        return cmd_arrive(state, args[0], haunt)
    if cmd == "dock" and not args:
        return cmd_dock(state)
    if cmd == "undock" and len(args) == 1:
        return cmd_undock(state, args[0])
    if cmd == "view" and len(args) == 1:
        return cmd_view(state, args[0])
    if cmd == "haunt" and not args:
        return cmd_haunt(state)
    if cmd == "status" and not args:
        return cmd_status(state)
    if cmd == "pause" and not args:
        return cmd_pause(state)
    if cmd == "resume" and not args:
        return cmd_resume(state)
    if cmd == "reset" and not args:
        return cmd_reset(state)
    if cmd == "save" and len(args) == 1:
        return cmd_save(state, args[0])
    if cmd == "load" and len(args) == 1:
        return cmd_load(state, args[0])
    if cmd == "help":
        return HELP
    return "未知命令: %s" % raw


def main():
    print("幽灵港调度引擎, " + HELP)
    state = new_game()
    while True:
        try:
            raw = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not raw or raw == "quit":
            break
        print(handle_command(state, raw))


if __name__ == "__main__":
    main()
