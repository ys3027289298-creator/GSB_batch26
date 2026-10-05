"""天空灯塔导航:引导航船进入航道。

所有操作幂等:先校验后变更,重复调用与失败调用都不破坏状态。
"""

import json

LANES = ("north", "south")
LANE_CAPACITY = 2
FUEL_BASE = 5
FUEL_PER_SHIP = 3


def new_game():
    return {
        "next_ship_no": 1,
        "ships": {},
        "waiting": [],
        "lanes": {lane: [] for lane in LANES},
        "locked": [],
        "lit": [],
        "fuel_used": 0,
        "guided_total": 0,
        "guided_names": [],
    }


def arrive_ship(state, name):
    """航船到达。按名字幂等:重复到达返回已有航船,不重复入队、不消耗编号。"""
    if not name:
        return None
    ship = state["ships"].get(name)
    if ship is not None:
        return ship
    ship = {"no": state["next_ship_no"], "name": name}
    state["next_ship_no"] += 1
    state["ships"][name] = ship
    state["waiting"].append(name)
    return ship


def peek_waiting(state):
    """查看队首航船。只读操作,不出队、不改任何状态。"""
    if not state["waiting"]:
        return None
    return state["ships"][state["waiting"][0]]


def lane_ships(state, lane):
    """查看航道。空航道返回 None,否则返回航船列表副本。"""
    names = state["lanes"].get(lane)
    if not names:
        return None
    return [state["ships"][name] for name in names]


def guide_next(state, lane):
    """引导队首航船进入航道。先校验后变更:任一条件不满足返回 None 且状态不变。"""
    if lane not in state["lanes"]:
        return None
    if lane in state["locked"]:
        return None
    if len(state["lanes"][lane]) >= LANE_CAPACITY:
        return None
    if not state["waiting"]:
        return None
    name = state["waiting"].pop(0)
    state["lanes"][lane].append(name)
    state["fuel_used"] += FUEL_BASE + FUEL_PER_SHIP
    if name not in state["guided_names"]:
        state["guided_names"].append(name)
        state["guided_total"] += 1
    return state["ships"][name]


def lock_lane(state, lane):
    """锁定航道。幂等:已锁定再锁返回 False;锁定时熄灭已亮的灯。"""
    if lane not in state["lanes"] or lane in state["locked"]:
        return False
    state["locked"].append(lane)
    if lane in state["lit"]:
        state["lit"].remove(lane)
    return True


def unlock_lane(state, lane):
    """解锁航道。幂等:未锁定返回 False。"""
    if lane not in state["locked"]:
        return False
    state["locked"].remove(lane)
    return True


def light_lane(state, lane):
    """亮灯。锁定的航道不能亮灯;重复亮灯不重复记录。"""
    if lane not in state["lanes"] or lane in state["locked"]:
        return False
    if lane not in state["lit"]:
        state["lit"].append(lane)
    return True


def reset(state):
    """重置。原地清空并恢复初始状态,重复调用结果相同。"""
    fresh = new_game()
    state.clear()
    state.update(fresh)
    return state


def save(state):
    return json.dumps(state, ensure_ascii=False, sort_keys=True)


def load(state, text):
    """读档。恢复包括 next_ship_no 在内的全部字段,编号不跳号;重复读档结果相同。"""
    data = json.loads(text)
    fresh = new_game()
    fresh.update(data)
    state.clear()
    state.update(fresh)
    return state


def main():
    state = new_game()
    print("天空灯塔命令: arrive <名> / guide <航道> / peek / lane <航道> / "
          "lock <航道> / unlock <航道> / light <航道> / reset / save / load <json> / quit")
    while True:
        try:
            raw = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not raw or raw == "quit":
            break
        cmd, _, arg = raw.partition(" ")
        arg = arg.strip()
        if cmd == "arrive" and arg:
            print(arrive_ship(state, arg))
        elif cmd == "guide" and arg:
            print(guide_next(state, arg))
        elif cmd == "peek":
            print(peek_waiting(state))
        elif cmd == "lane" and arg:
            print(lane_ships(state, arg))
        elif cmd == "lock" and arg:
            print(lock_lane(state, arg))
        elif cmd == "unlock" and arg:
            print(unlock_lane(state, arg))
        elif cmd == "light" and arg:
            print(light_lane(state, arg))
        elif cmd == "reset":
            reset(state)
            print("ok")
        elif cmd == "save":
            print(save(state))
        elif cmd == "load" and arg:
            load(state, arg)
            print("ok")
        else:
            print("未知命令")


if __name__ == "__main__":
    main()
