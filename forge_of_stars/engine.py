"""星之熔炉 (Star Forge)：投入矿石、按配方冶炼、产出星尘的制造引擎。"""

import json
import shlex

FURNACE_CAPACITY = 3

RECIPES = {
    "iron_ingot": {"ore": "iron", "stardust": 10},
    "silver_ingot": {"ore": "silver", "stardust": 30},
}


def new_game():
    return {
        "capacity": FURNACE_CAPACITY,
        "ores": [],
        "ore_ids": [],
        "recipe": None,
        "stardust": 0,
        "forged": 0,
        "products": {},
        "paused": False,
        "saves": {},
        "save_seq": 0,
    }


def _clone(value):
    return json.loads(json.dumps(value))


def add_ore(state, ore_id, kind):
    if ore_id in state["ore_ids"]:
        return False
    if len(state["ores"]) >= state["capacity"]:
        return False
    state["ore_ids"].append(ore_id)
    state["ores"].append({"id": ore_id, "kind": kind})
    return True


def view_ores(state):
    return [(ore["id"], ore["kind"]) for ore in state["ores"]]


def set_recipe(state, name):
    if not name or name == "none":
        state["recipe"] = None
        return True
    if name not in RECIPES:
        return False
    state["recipe"] = name
    return True


def forge(state):
    if state["paused"]:
        return False
    recipe_name = state["recipe"]
    if not recipe_name:
        return None
    recipe = RECIPES[recipe_name]
    ores = state["ores"]
    if not ores or ores[0]["kind"] != recipe["ore"]:
        return False
    ore = ores.pop(0)
    state["ore_ids"].remove(ore["id"])
    state["stardust"] += recipe["stardust"]
    state["forged"] += 1
    state["products"][recipe_name] = state["products"].get(recipe_name, 0) + 1
    return {"ore": ore["id"], "recipe": recipe_name, "stardust": recipe["stardust"]}


def set_paused(state, paused):
    state["paused"] = bool(paused)
    return True


def save_game(state):
    slot = state["save_seq"] + 1
    snapshot = {key: _clone(value) for key, value in state.items() if key != "saves"}
    state["saves"][str(slot)] = snapshot
    state["save_seq"] = slot
    return slot


def load_game(state, slot):
    snapshot = state["saves"].get(str(slot))
    if snapshot is None:
        return False
    saves = state["saves"]
    highest = max((int(key) for key in saves), default=0)
    state.clear()
    state.update(_clone(snapshot))
    state["saves"] = saves
    state["save_seq"] = max(highest, snapshot.get("save_seq", 0))
    return True


def reset_game(state):
    saves = state["saves"]
    save_seq = state["save_seq"]
    state.clear()
    state.update(new_game())
    state["saves"] = saves
    state["save_seq"] = save_seq
    return True


def dispatch(state, command, *args):
    command = command.lower()
    if command == "add":
        return add_ore(state, args[0], args[1])
    if command == "view":
        return view_ores(state)
    if command == "recipe":
        return set_recipe(state, args[0] if args else "")
    if command == "forge":
        return forge(state)
    if command == "pause":
        return set_paused(state, True)
    if command == "resume":
        return set_paused(state, False)
    if command == "stardust":
        return state["stardust"]
    if command == "forged":
        return state["forged"]
    if command == "products":
        return dict(state["products"])
    if command == "save":
        return save_game(state)
    if command == "load":
        return load_game(state, int(args[0]))
    if command == "saves":
        return sorted(int(key) for key in state["saves"])
    if command == "reset":
        return reset_game(state)
    raise ValueError("unknown command: %s" % command)


def main():
    state = new_game()
    print("星之熔炉 命令: add/recipe/forge/view/pause/resume/save/load/reset/quit")
    while True:
        try:
            raw = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not raw or raw == "quit":
            break
        parts = shlex.split(raw)
        if parts[0] == "quit":
            break
        result = dispatch(state, *parts)
        if result is not None:
            print(result)


if __name__ == "__main__":
    main()
