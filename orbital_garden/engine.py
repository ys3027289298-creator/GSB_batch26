"""轨道花园引擎：光照、水分、养分与收成互相影响。

已修复的问题：
 1. 重复作物          —— rule_a / plant 拒绝同名作物重复入槽
 2. 种植槽满仍播种    —— rule_d / rule_j 在槽位满时拒绝播种
 3. 空订单返回文本    —— rule_c 在没有订单时返回 False，不再返回文本
 4. 先到作物未收获    —— harvest 按先进先出收获最早种下的作物
 5. 锁定区域仍浇水    —— rule_e 在暂停(锁定)时拒绝浇水
 6. 查看作物误删      —— rule_i 返回过滤后的副本，不改动原记录
 7. 养分少算          —— rule_h 转移养分时 dst 同步入账
 8. 单次灌溉重复累计  —— rule_f 一次灌溉只累计一次
 9. 重置不清          —— reset_game 先彻底清空再写入初始状态
10. 读档跳号          —— load_game 恢复 next_id，编号连续不回退

暂停/恢复与损坏存档的行为说明见同目录 README.md。
"""

import json

SAVE_VERSION = 1
WATER_PER_IRRIGATION = 5
NUTRIENT_PER_TRANSFER = 5


def new_game():
    """返回一份完全干净的初始状态。"""
    return {
        "clock": 0,
        "paused": False,
        "items": [],
        "slots": 0,
        "cap": 2,
        "count": 0,
        "amount": 0,
        "src": 0,
        "dst": 0,
        "audit": [],
        "orders": [],
        "next_id": 1,
    }


def rule_a(state, name="x"):
    """播种新作物；同名作物已在槽中时拒绝（重复作物修复）。"""
    if name in state["items"]:
        return False
    state["items"].append(name)
    return True


def rule_b(state):
    """推进时钟；暂停时保持不动并返回当前时钟。"""
    if state.get("paused"):
        return state["clock"]
    state["clock"] += 1
    return state["clock"]


def rule_c(state):
    """返回队首订单文本；没有订单时返回 False（空订单不返回文本）。"""
    orders = state.get("orders") or []
    if not orders:
        return False
    return orders[0]


def rule_d(state, name="x"):
    """播种；种植槽已满时拒绝（槽满仍播种修复）。"""
    if len(state["items"]) >= state["cap"]:
        return False
    state["items"].append(name)
    return True


def rule_e(state):
    """给区域浇水；区域锁定(暂停)时拒绝（锁定仍浇水修复）。"""
    if state.get("paused"):
        return False
    return True


def rule_f(state):
    """累计一次灌溉；单次灌溉只计一次（重复累计修复）。"""
    state["count"] += 1
    return state["count"]


def rule_g(state):
    """消耗水分进行灌溉；水分不足时失败且不扣减。"""
    if state["amount"] < WATER_PER_IRRIGATION:
        return False
    state["amount"] -= WATER_PER_IRRIGATION
    return True


def rule_h(state):
    """把养分从 src 转到 dst，dst 必须同步入账（养分少算修复）。"""
    state["src"] -= NUTRIENT_PER_TRANSFER
    state["dst"] += NUTRIENT_PER_TRANSFER
    return True


def rule_i(state, kind="a"):
    """查看某类记录，返回过滤后的副本，不改动原列表（查看误删修复）。"""
    return [row for row in state["audit"] if row[0] == kind]


def rule_j(state):
    """占用一个种植槽；槽位已满时拒绝。"""
    if state["slots"] >= state["cap"]:
        return False
    state["slots"] += 1
    return True


def plant(state, name):
    """播种：重复作物或槽位满时返回 None，否则返回分配的作物编号。"""
    if name in state["items"]:
        return None
    if len(state["items"]) >= state["cap"]:
        return None
    state["items"].append(name)
    state["slots"] += 1
    crop_id = state["next_id"]
    state["next_id"] += 1
    return crop_id


def harvest(state):
    """收获最早种下的作物（先到先收）；没有作物时返回 None。"""
    if not state["items"]:
        return None
    state["slots"] = max(0, state["slots"] - 1)
    return state["items"].pop(0)


def pause(state):
    state["paused"] = True


def resume(state):
    state["paused"] = False


def reset_game(state):
    """重置：先彻底清空旧状态，再写入初始值（重置不清修复）。"""
    state.clear()
    state.update(new_game())
    return state


def save_game(state, path):
    payload = dict(state)
    payload["save_version"] = SAVE_VERSION
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)


def load_game(path):
    """读档。

    存档损坏或格式不符时抛出 ValueError，不产生任何副作用；
    正常读档时 next_id 按存档记录恢复，编号连续、不回退（读档跳号修复）。
    """
    try:
        with open(path, encoding="utf-8") as fh:
            payload = json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"存档损坏或不可读: {path}") from exc
    if not isinstance(payload, dict) or "next_id" not in payload:
        raise ValueError(f"存档格式不符: {path}")
    state = new_game()
    state.update(payload)
    state["next_id"] = max(1, int(state["next_id"]))
    return state


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
