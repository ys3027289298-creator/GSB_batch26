"""星之熔炉 (Forge of Stars) 制造引擎。

修复的问题:
1. 重复矿石   - 同种矿石重复投入会被拒绝
2. 熔炉满仍投入 - 熔炉达到容量上限后拒绝继续投入
3. 空配方返回文本 - 查不到的配方返回 None, 而不是 "empty" 之类的文本
4. 先到矿石未冶炼 - 冶炼严格按 FIFO, 先投入的矿石先被冶炼
5. 暂停仍锻造 - 暂停状态下 smelt 不做任何事
6. 查看矿石误删 - view 只读取不弹出队列
7. 星尘少算   - 星尘按配方全额计入
8. 单次锻造重复累计 - 每次冶炼锻造计数只加一次
9. 重置不清   - reset 彻底清空全部状态
10. 读档跳号  - 读档后存档序号不回退、不跳号
"""

import copy

RECIPES = {
    "铁矿": ("铁锭", 10),
    "铜矿": ("铜锭", 8),
    "星砂": ("星晶", 25),
}

CAPACITY = 3


def new_game():
    return {
        "furnace": [],      # 熔炉内矿石队列 (FIFO)
        "capacity": CAPACITY,
        "paused": False,
        "stardust": 0,      # 星尘
        "forged": 0,        # 锻造次数
        "products": [],     # 已产出的锭/晶
        "save_seq": 0,      # 存档序号 (单调递增, 不随读档回退)
        "saves": {},        # 序号 -> 快照
    }


def add_ore(state, ore):
    """投入矿石。重复或熔炉满时拒绝。"""
    if ore in state["furnace"]:
        return "duplicate"
    if len(state["furnace"]) >= state["capacity"]:
        return "full"
    state["furnace"].append(ore)
    return "ok"


def get_recipe(ore):
    """查询配方。没有配方时返回 None, 不返回占位文本。"""
    return RECIPES.get(ore)


def smelt(state):
    """冶炼最早投入的矿石 (FIFO)。暂停或空炉时不动作。"""
    if state["paused"]:
        return "paused"
    if not state["furnace"]:
        return "empty"
    ore = state["furnace"].pop(0)
    recipe = get_recipe(ore)
    if recipe is None:
        return "no-recipe"
    product, dust = recipe
    state["products"].append(product)
    state["stardust"] += dust   # 星尘全额计入
    state["forged"] += 1        # 单次锻造只累计一次
    return product


def view_ores(state):
    """查看炉内矿石, 返回副本, 不移除任何矿石。"""
    return list(state["furnace"])


def pause(state):
    state["paused"] = True
    return True


def resume(state):
    state["paused"] = False
    return True


def reset(state):
    """彻底重置: 清空炉内矿石、星尘、计数、产物与存档。"""
    state.clear()
    state.update(new_game())
    return True


def _snapshot(state):
    return {
        "furnace": copy.deepcopy(state["furnace"]),
        "capacity": state["capacity"],
        "paused": state["paused"],
        "stardust": state["stardust"],
        "forged": state["forged"],
        "products": copy.deepcopy(state["products"]),
    }


def save(state):
    """存档, 返回新序号。序号单调递增。"""
    state["save_seq"] += 1
    slot = state["save_seq"]
    state["saves"][slot] = _snapshot(state)
    return slot


def load(state, slot):
    """读档。恢复进度但保留存档序号与存档表, 不会跳号。"""
    snap = state["saves"].get(slot)
    if snap is None:
        return False
    restored = copy.deepcopy(snap)
    restored["save_seq"] = state["save_seq"]
    restored["saves"] = state["saves"]
    state.clear()
    state.update(restored)
    return True


def handle_command(state, raw):
    """处理一条命令, 返回一行输出文本。"""
    parts = raw.split()
    cmd = parts[0]
    arg = parts[1] if len(parts) > 1 else None

    if cmd == "add" and arg:
        return add_ore(state, arg)
    if cmd == "recipe" and arg:
        recipe = get_recipe(arg)
        if recipe is None:
            return "none"
        return "%s/%d" % recipe
    if cmd == "smelt":
        return str(smelt(state))
    if cmd == "view":
        ores = view_ores(state)
        return ",".join(ores) if ores else "empty"
    if cmd == "pause":
        pause(state)
        return "ok"
    if cmd == "resume":
        resume(state)
        return "ok"
    if cmd == "reset":
        reset(state)
        return "ok"
    if cmd == "save":
        return str(save(state))
    if cmd == "load" and arg:
        return "ok" if load(state, int(arg)) else "missing"
    if cmd == "status":
        return "stardust=%d forged=%d" % (state["stardust"], state["forged"])
    return "unknown"


def main():
    print("engine 命令: add/recipe/smelt/view/pause/resume/reset/save/load/status/quit")
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
