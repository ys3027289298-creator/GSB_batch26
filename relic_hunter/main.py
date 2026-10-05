"""遗迹猎人探索逻辑（修复版）。

状态保存在一个可被 json 直接序列化往返的 dict 中；每个会改状态的命令
先做全部前置检查，再通过快照/回滚保证失败时状态不变。
"""

import json

MAX_BAG = 3
EXPLORE_COST = 1

RELIC_NAMES = ["石斧", "陶符", "铜镜", "玉珏", "骨笛", "金冠"]


def new_game(seed=0):
    return {
        "seed": seed,
        "stamina": 10,
        "explorations": 0,
        "paused": False,
        "next_id": 1,
        # relic_id -> {"id", "name"}；字符串键以保证 JSON 往返
        "registry": {},
        "bag": [],
    }


def _copy(state):
    return json.loads(json.dumps(state))


def _relic_name(seed_offset):
    return RELIC_NAMES[seed_offset % len(RELIC_NAMES)]


def explore(state):
    """消耗体力探索一次，发现一件新遗物（不自动入包）。

    暂停中或体力不足时整体失败，任何计数都不变化。
    """
    if state.get("paused"):
        return False, "已暂停，无法探索"
    if state.get("stamina", 0) < EXPLORE_COST:
        return False, "体力不足"

    snapshot = _copy(state)
    try:
        state["stamina"] -= EXPLORE_COST
        state["explorations"] += 1
        rid = state["next_id"]
        state["next_id"] += 1
        state["registry"][str(rid)] = {"id": rid, "name": _relic_name(rid - 1)}
        state["last_found"] = rid
    except Exception:
        state.clear()
        state.update(snapshot)
        raise
    return True, "发现遗物 %d 号：%s" % (rid, state["registry"][str(rid)]["name"])


def pickup(state, rid):
    """把已登记遗物装入背包：重复、未登记、背包满均失败且不改动状态。"""
    rid = int(rid)
    if str(rid) not in state.get("registry", {}):
        return False, "该遗物不存在"
    if rid in state.get("bag", []):
        return False, "遗物已在背包中"
    if len(state.get("bag", [])) >= MAX_BAG:
        return False, "背包已满"

    snapshot = _copy(state)
    try:
        state["bag"].append(rid)
    except Exception:
        state.clear()
        state.update(snapshot)
        raise
    return True, "拾取 %d 号遗物" % rid


def inspect(state, rid):
    """查看遗物（纯读操作，绝不删除背包内容）。"""
    rid = int(rid)
    relic = state.get("registry", {}).get(str(rid))
    if relic is None:
        return False, "该遗物不存在"
    carried = rid in state.get("bag", [])
    where = "背包中" if carried else "未携带"
    return True, "%d 号遗物 %s（%s）" % (rid, relic["name"], where)


def view_bag(state):
    """空背包返回 None（不返回占位文本），不修改任何状态。"""
    bag = list(state.get("bag", []))
    if not bag:
        return None
    return bag


def free_slots(state):
    return MAX_BAG - len(state.get("bag", []))


def status(state):
    return (
        "体力 %d，探索 %d 次，背包 %d/%d，%s"
        % (
            state["stamina"],
            state["explorations"],
            len(state["bag"]),
            MAX_BAG,
            "暂停中" if state["paused"] else "进行中",
        )
    )


def set_paused(state, paused):
    state["paused"] = bool(paused)
    return True, ("已暂停" if paused else "已继续")


def reset(state):
    """原地清空到新游戏状态（旧对象上的计数、背包、登记全部归零）。"""
    state.clear()
    state.update(new_game())
    return True, "已重置"


def to_save(state):
    """序列化：完整状态写盘，读回后编号严格连续。"""
    return json.dumps(_copy(state), ensure_ascii=False)


def from_save(state, text):
    data = json.loads(text)
    restored = new_game()
    restored.update(data)
    state.clear()
    state.update(restored)
    return True, "读档完成"


def dispatch(state, line):
    parts = line.split()
    cmd = parts[0]
    args = parts[1:]
    if cmd == "explore":
        return explore(state)
    if cmd == "pickup" and len(args) == 1:
        return pickup(state, args[0])
    if cmd == "inspect" and len(args) == 1:
        return inspect(state, args[0])
    if cmd == "bag":
        return view_bag(state)
    if cmd == "status":
        return True, status(state)
    if cmd == "pause":
        return set_paused(state, True)
    if cmd == "resume":
        return set_paused(state, False)
    if cmd == "reset":
        return reset(state)
    if cmd == "save" and len(args) == 1:
        with open(args[0], "w", encoding="utf-8") as fh:
            fh.write(to_save(state))
        return True, "已保存"
    if cmd == "load" and len(args) == 1:
        with open(args[0], encoding="utf-8") as fh:
            return from_save(state, fh.read())
    return False, "未知命令"


def main():
    state = new_game()
    print("遗迹猎人 命令: explore/pickup ID/inspect ID/bag/status/"
          "pause/resume/reset/save F/load F/quit")
    while True:
        try:
            raw = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not raw or raw == "quit":
            break
        result = dispatch(state, raw)
        if result is None:
            print("(空)")
        elif isinstance(result, list):
            print("背包: " + ", ".join(str(rid) for rid in result))
        else:
            ok, msg = result
            print(("OK " if ok else "FAIL ") + str(msg))


if __name__ == "__main__":
    main()
