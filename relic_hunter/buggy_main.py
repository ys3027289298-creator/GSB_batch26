"""遗迹猎人探索逻辑（缺陷基线，仅用于复现，勿在生产使用）。

刻意保留 10 个缺陷，与 replay.py 的固定输入一一对应：
 1 重复遗物        pickup 不查重，同一遗物可重复入包
 2 背包满仍拾取    pickup 不检查容量
 3 空背包返回文本  view_bag 空包返回 "empty" 而非 None
 4 先到遗物未登记  explore 只登记偶数号，奇数号先到遗物丢失
 5 暂停仍触发      explore 忽略 paused 标志
 6 查看遗物误删    inspect 顺手把遗物从背包移除
 7 体力少算        体力 1 点时仍允许探索，扣成负数
 8 单次探索重复累计 explorations 一次加 2
 9 重置不清        reset 只返回成功，状态原样保留
10 读档跳号        存档丢 next_id 且登记按背包截断，读档后编号重复
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
        "registry": {},
        "bag": [],
    }


def _relic_name(seed_offset):
    return RELIC_NAMES[seed_offset % len(RELIC_NAMES)]


def explore(state):
    # 缺陷 5：不检查 paused
    # 缺陷 7：要求体力 >= 2，体力 1 点时仍放行并扣成负数
    if state.get("stamina", 0) < 2 * EXPLORE_COST:
        return False, "体力不足"
    state["stamina"] -= EXPLORE_COST
    # 缺陷 8：单次探索计数加 2
    state["explorations"] += 2
    rid = state["next_id"]
    state["next_id"] += 1
    # 缺陷 4：只登记偶数号，先到的奇数号遗物不进入 registry
    if rid % 2 == 0:
        state["registry"][str(rid)] = {"id": rid, "name": _relic_name(rid - 1)}
    state["last_found"] = rid
    return True, "发现遗物 %d 号" % rid


def pickup(state, rid):
    # 缺陷 1：不检查是否已在背包
    # 缺陷 2：不检查背包容量
    rid = int(rid)
    state["bag"].append(rid)
    return True, "拾取 %d 号遗物" % rid


def inspect(state, rid):
    # 缺陷 6：查看时把遗物从背包里删掉
    rid = int(rid)
    relic = state.get("registry", {}).get(str(rid))
    if relic is None:
        return False, "该遗物不存在"
    if rid in state.get("bag", []):
        state["bag"].remove(rid)
    return True, "%d 号遗物 %s" % (rid, relic["name"])


def view_bag(state):
    # 缺陷 3：空背包返回占位文本
    bag = list(state.get("bag", []))
    if not bag:
        return "empty"
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
    # 缺陷 9：声称重置成功，实际状态原样保留
    return True, "已重置"


def to_save(state):
    # 缺陷 10：丢 next_id，且登记只保留背包内遗物
    data = {
        "stamina": state["stamina"],
        "explorations": state["explorations"],
        "paused": state["paused"],
        "bag": list(state["bag"]),
        "registry": {
            key: value
            for key, value in state["registry"].items()
            if value["id"] in state["bag"]
        },
    }
    return json.dumps(data, ensure_ascii=False)


def from_save(state, text):
    data = json.loads(text)
    state.clear()
    state.update(data)
    # 缺陷 10：按背包长度猜编号，读档后新遗物与旧编号冲突（跳号/重号）
    state["next_id"] = len(state.get("bag", [])) + 1
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
    print("遗迹猎人(缺陷版) 命令: explore/pickup ID/inspect ID/bag/status/"
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
        elif not (isinstance(result, tuple) and len(result) == 2):
            print(result)
        else:
            ok, msg = result
            print(("OK " if ok else "FAIL ") + str(msg))


if __name__ == "__main__":
    main()
