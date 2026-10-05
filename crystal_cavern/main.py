"""水晶洞穴采集：矿层 / 晶簇 / 背包三份状态的状态机与回滚。

状态机:
    矿层 layer:      EMPTY -> FILLING -> FULL (由 layer 中的晶簇数与 layer_capacity 决定)
    晶簇 cluster:    SPAWNED -> IN_LAYER -> HARVESTED (采出后即从 clusters 中移除)
    背包 backpack:   EMPTY -> LOADED -> FULL (由 backpack 与 backpack_capacity 决定)

所有命令经 apply() 进入: 先快照, 命令被拒绝(返回 False)或抛异常时整体回滚,
保证三份状态不会出现"改了一半"的互相覆盖。
"""

import copy
import json

LAYER_EMPTY = "EMPTY"
LAYER_FILLING = "FILLING"
LAYER_FULL = "FULL"

STATE_KEYS = (
    "layer_capacity",
    "layer",
    "clusters",
    "backpack_capacity",
    "backpack",
    "paused",
    "tick",
    "next_cluster_id",
    "harvested_total",
)


def new_game(layer_capacity=3, backpack_capacity=50):
    return {
        "layer_capacity": layer_capacity,
        "layer": [],
        "clusters": {},
        "backpack_capacity": backpack_capacity,
        "backpack": 0,
        "paused": False,
        "tick": 0,
        "next_cluster_id": 1,
        "harvested_total": 0,
        "history": [],
    }


# ---------------------------------------------------------------- 状态机核心

def layer_status(state):
    n = len(state["layer"])
    if n == 0:
        return LAYER_EMPTY
    if n >= state["layer_capacity"]:
        return LAYER_FULL
    return LAYER_FILLING


def _snapshot(state):
    return {key: copy.deepcopy(state[key]) for key in STATE_KEYS}


def _restore(state, snap):
    for key in STATE_KEYS:
        state[key] = snap[key]


def apply(state, command, *args):
    """执行一条命令; 被拒绝或出错时回滚到命令前的三份状态。"""
    snap = _snapshot(state)
    try:
        result = command(state, *args)
    except Exception:
        _restore(state, snap)
        raise
    if result is False:
        _restore(state, snap)
        return False
    state["history"].append(snap)
    return result


def rollback(state, steps=1):
    """显式回滚最近 steps 条已接受的命令。"""
    for _ in range(steps):
        if not state["history"]:
            return False
        _restore(state, state["history"].pop())
    return True


# ---------------------------------------------------------------- 领域命令

def spawn_cluster(state, crystals):
    if crystals <= 0:
        return False
    cid = state["next_cluster_id"]
    state["next_cluster_id"] += 1
    state["clusters"][cid] = {"crystals": crystals, "arrived": state["tick"]}
    state["tick"] += 1
    return cid


def enter_layer(state, cid):
    if cid not in state["clusters"]:
        return False
    if cid in state["layer"]:
        return False  # 重复晶簇: 同一晶簇不得两次进入矿层
    if layer_status(state) == LAYER_FULL:
        return False  # 矿层满载: 拒绝进入, 由 apply() 回滚, 不产生半改状态
    state["layer"].append(cid)
    return True


def pause(state):
    state["paused"] = True
    return True


def resume(state):
    state["paused"] = False
    return True


def grow(state, amount=1):
    if state["paused"]:
        return False  # 暂停中不生长
    if amount <= 0:
        return False
    for cid in state["layer"]:
        state["clusters"][cid]["crystals"] += amount
    return True


def harvest(state):
    """采集最早到达的晶簇, 水晶精确入账且只计一次。"""
    if not state["layer"]:
        return False
    free = state["backpack_capacity"] - state["backpack"]
    if free <= 0:
        return False  # 背包已满: 整体回滚, 不做部分转移
    cid = min(state["layer"], key=lambda c: state["clusters"][c]["arrived"])
    cluster = state["clusters"][cid]
    moved = min(cluster["crystals"], free)
    state["backpack"] += moved
    state["harvested_total"] += moved
    state["layer"].remove(cid)
    del state["clusters"][cid]
    return {"cluster": cid, "crystals": moved}


def view_cluster(state, cid):
    cluster = state["clusters"].get(cid)
    if cluster is None:
        return False
    return dict(cluster)  # 只读查看, 不得删除


def backpack_status(state):
    if state["backpack"] == 0:
        return None  # 空背包: 返回 None 而非文本
    return {"crystals": state["backpack"], "capacity": state["backpack_capacity"]}


def reset(state):
    fresh = new_game(state["layer_capacity"], state["backpack_capacity"])
    for key in STATE_KEYS:
        state[key] = fresh[key]
    state["history"].clear()
    return True


def save(state):
    return json.dumps({key: state[key] for key in STATE_KEYS})


def load(state, data):
    if isinstance(data, str):
        data = json.loads(data)
    snap = _snapshot(state)
    try:
        for key in STATE_KEYS:
            state[key] = data[key]
        state["clusters"] = {int(k): v for k, v in state["clusters"].items()}
    except (KeyError, TypeError, ValueError):
        _restore(state, snap)
        return False
    state["history"].clear()
    return True


# ---------------------------------------------------------------- 基线命令(修复版)

def cmd_a(state):
    if state["balance"] < 20:
        return False
    state["balance"] -= 20
    return True


def cmd_b(state):
    return state["accounts"].get("missing", 0)


def cmd_c(state):
    return bool(state.get("events"))


def cmd_d(state):
    events = state.get("events")
    if not events:
        return False
    return events.pop(min(events))


def cmd_e(state):
    return state["cap"] - state["used"]


def cmd_f(state):
    return bool(state.get("queue"))


def cmd_g(state):
    state["nodes"].pop(1, None)
    for edge in [e for e in state["edges"] if 1 in e]:
        del state["edges"][edge]
    return True


def cmd_h(state):
    return None


def cmd_i(state):
    if not state["queue"]:
        return False
    return state["queue"][0]


def cmd_j(state):
    state["count"] = 0
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
