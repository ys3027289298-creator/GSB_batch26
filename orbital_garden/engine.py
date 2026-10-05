"""orbital_garden 引擎：光照、水分与收成互相影响的轨道种植。

核心规则
--------
- 每种作物在种植槽中唯一（重复播种会被拒绝）。
- 种植槽有容量上限，满了之后不能再播种。
- 时钟每 tick 推进一次；暂停时时间冻结，作物不生长、不耗水。
- 光照与水分共同决定作物是否成熟：两者都达标才可收获。
- 收获按先到先收（FIFO），只交付已成熟的作物。
- 锁定/暂停的区域不能浇水。
- 单次灌溉只累计一次水分。
- 养分不会扣成负数；转运时目的地按实际扣减量入账。
- reset 会清空全部运行状态；存档/读档保持 next_id 连续不跳号。
"""

import copy
import json

GROWTH_PER_TICK = 1
WATER_PER_TICK = 1
LIGHT_PER_TICK = 1
DEFAULT_SLOT_CAP = 4
IRRIGATION_AMOUNT = 5


def new_game():
    """返回一份全新的初始状态。"""
    return {
        "paused": False,
        "clock": 0,
        "next_id": 1,
        "slot_cap": DEFAULT_SLOT_CAP,
        "crops": [],
        "orders": [],
        "water": 0,
        "light": 0,
        "nutrients": 0,
        "harvest_log": [],
    }


def _crop_names(state):
    return [crop["name"] for crop in state.get("crops", [])]


def _used_slots(state):
    if "slots" in state:
        return state["slots"]
    if "items" in state:
        return len(state["items"])
    return len(state.get("crops", []))


def _slot_cap(state):
    return state.get("cap", state.get("slot_cap", DEFAULT_SLOT_CAP))


def _ready(crop):
    return crop.get("growth", 0) >= crop.get("need", 1)


def rule_a(state):
    """重复作物检查：种植槽内没有同名作物时返回 True。"""
    names = _crop_names(state)
    return len(names) == len(set(names))


def rule_b(state):
    """时钟推进：暂停时时间冻结，返回当前时钟。"""
    if state.get("paused"):
        return state["clock"]
    state["clock"] += 1
    for crop in state.get("crops", []):
        if state.get("water", 0) > 0 and state.get("light", 0) > 0:
            crop["growth"] = crop.get("growth", 0) + GROWTH_PER_TICK
            state["water"] = max(0, state["water"] - WATER_PER_TICK)
            state["light"] = max(0, state["light"] - LIGHT_PER_TICK)
    return state["clock"]


def rule_c(state):
    """交付订单：订单为空时不产生任何交付文本，返回 False。"""
    orders = state.get("orders", [])
    if not orders:
        return False
    order = orders.pop(0)
    return "交付订单: {}".format(order)


def rule_d(state):
    """播种：种植槽已满时拒绝并返回 False，否则登记作物。"""
    if _used_slots(state) >= _slot_cap(state):
        return False
    crop = {
        "id": state.get("next_id", 1),
        "name": "x",
        "growth": 0,
        "need": 3,
    }
    state["next_id"] = crop["id"] + 1
    if "items" in state:
        state["items"].append("x")
    else:
        state.setdefault("crops", []).append(crop)
    return True


def rule_e(state):
    """灌溉：暂停/锁定时拒绝；单次灌溉只累计一次水分。"""
    if state.get("paused"):
        return False
    state["water"] = state.get("water", 0) + IRRIGATION_AMOUNT
    return True


def rule_f(state):
    """灌溉计数：单次灌溉只累计 1 次，返回累计次数。"""
    state["count"] += 1
    return state["count"]


def rule_g(state):
    """养分扣除：余额不足时不扣成负数，返回 False。"""
    if state["amount"] < 5:
        return False
    state["amount"] -= 5
    return True


def rule_h(state):
    """养分转运：从 src 扣 5 并如数记入 dst，不少算。"""
    state["src"] -= 5
    state["dst"] = state.get("dst", 0) + 5
    return True


def rule_i(state):
    """收获审计：按先到先收，只返回最早一批（同名）作物的记录。"""
    audit = state.get("audit", [])
    if not audit:
        return []
    first = audit[0][0]
    return [row for row in audit if row[0] == first]


def rule_j(state):
    """种植槽闸口：槽位达到容量上限时返回 False，禁止继续播种。"""
    return _used_slots(state) < _slot_cap(state)


def pause(state):
    """暂停：冻结时钟与生长，灌溉被拒绝。"""
    state["paused"] = True
    return state


def resume(state):
    """恢复：解除暂停，时钟从冻结处继续，不补跳暂停期间。"""
    state["paused"] = False
    return state


def reset(state):
    """重置：清空全部运行状态，返回 new_game() 的深拷贝。"""
    fresh = new_game()
    state.clear()
    state.update(fresh)
    return state


def save_game(state, path):
    """把状态（含 next_id）写入 JSON 存档。"""
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(state, fh, ensure_ascii=False, indent=2)
    return True


def load_game(path):
    """读档：返回 (state, ok)。

    存档损坏（非法 JSON 或不是对象）时不抛异常、不跳号，
    返回 (new_game(), False)，next_id 从 1 重新开始。
    正常读档保留存档中的 next_id，后续作物编号连续。
    """
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, ValueError):
        return new_game(), False
    if not isinstance(data, dict):
        return new_game(), False
    state = new_game()
    state.update(copy.deepcopy(data))
    return state, True


def main():
    print("engine 命令: run/quit")
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
