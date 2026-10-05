"""低语森林探索（Whisper Forest）。

修复的十个问题：
1. 重复回响：同一回响只能被触发一次，重复触发直接失败。
2. 空地满仍进入：林间空地有访客上限，满员时进入失败。
3. 空背包返回文本：查看空背包返回明确的空提示文本，而不是 "[]"。
4. 先到回响未收集：首次踏入回响所在的空地只触发回响，不会顺手收集。
5. 锁定仍触发：锁定的回响在解锁前不能触发。
6. 查看回响误删：查看回响是只读操作，不会从状态中删除回响。
7. 法力少算：触发回响按其真实费用扣除法力，费用不足整体失败。
8. 单次收集重复累计：一个回响只能收集一次，不会重复进包/重复计数。
9. 重置不清：reset 清空回响、背包与访客并恢复初始法力。
10. 读档跳号：读档后回响编号从存档最大值继续，不会跳号或撞号。

所有写操作在失败时不留下半份修改（先校验、后提交，且通过副本提交）。
读档恢复完整进度，可继续推进而不是从头重来。
"""

import copy
import json
import os

BAG_CAPACITY = 5
START_MANA = 10

DEFAULT_GLADES = {
    "g1": {"name": "苔光空地", "cap": 2},
    "g2": {"name": "雾语空地", "cap": 1},
    "g3": {"name": "根须空地", "cap": 3},
}

DEFAULT_ECHOES = {
    "e1": {"name": "风的低语", "glade": "g1", "mana": 3, "locked": False},
    "e2": {"name": "石的回响", "glade": "g2", "mana": 5, "locked": True},
    "e3": {"name": "溪的回声", "glade": "g3", "mana": 4, "locked": False},
}

EMPTY_BAG_TEXT = "背包空空如也，连一丝回响都没有。"
SAVE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "whisper_save.json")


def new_game():
    return {
        "mana": START_MANA,
        "glades": copy.deepcopy(DEFAULT_GLADES),
        "echoes": copy.deepcopy(DEFAULT_ECHOES),
        "triggered": {},
        "collected": [],
        "bag": [],
        "visitors": {},
        "next_echo_id": 1,
    }


def _atomic(fn):
    """先在状态副本上执行；校验全部通过后才整体提交，失败不留半份修改。"""

    def wrapper(state, *args, **kwargs):
        snapshot = copy.deepcopy(state)
        try:
            result = fn(state, *args, **kwargs)
        except (KeyError, IndexError, TypeError, ValueError):
            state.clear()
            state.update(snapshot)
            raise
        if result is False or result is None:
            state.clear()
            state.update(snapshot)
            return False
        return result

    return wrapper


@_atomic
def enter_glade(state, glade_id):
    """进入空地。空地满员时失败；首次进入自动触发该空地上未锁定的回响，
    但绝不替玩家收集回响。"""
    glade = state["glades"].get(glade_id)
    if glade is None:
        return False
    visitors = state["visitors"].setdefault(glade_id, [])
    if len(visitors) >= glade["cap"]:
        return False
    visitors.append("explorer")
    for echo_id, echo in state["echoes"].items():
        if echo["glade"] == glade_id:
            _trigger(state, echo_id)
    return True


@_atomic
def leave_glade(state, glade_id):
    visitors = state["visitors"].get(glade_id)
    if not visitors:
        return False
    visitors.pop()
    return True


@_atomic
def unlock_echo(state, echo_id):
    """解锁锁定的回响，不触发它（修复“锁定仍触发”）。"""
    echo = state["echoes"].get(echo_id)
    if echo is None or not echo["locked"]:
        return False
    echo["locked"] = False
    return True


def _trigger(state, echo_id):
    echo = state["echoes"].get(echo_id)
    if echo is None:
        return False
    if echo["locked"]:
        return False
    if state["triggered"].get(echo_id):
        return False
    cost = echo["mana"]
    if state["mana"] < cost:
        return False
    state["mana"] -= cost
    state["triggered"][echo_id] = True
    return True


@_atomic
def trigger_echo(state, echo_id):
    """主动触发回响：锁定的不行、已触发的不重复、法力不足不扣费。"""
    if echo_id not in state["echoes"]:
        return False
    return _trigger(state, echo_id)


@_atomic
def collect_echo(state, echo_id):
    """收集已触发的回响。必须先触发；每个回响只累计一次。"""
    echo = state["echoes"].get(echo_id)
    if echo is None:
        return False
    if not state["triggered"].get(echo_id):
        return False
    if echo_id in state["collected"]:
        return False
    if len(state["bag"]) >= BAG_CAPACITY:
        return False
    state["collected"].append(echo_id)
    state["bag"].append({"id": echo_id, "name": echo["name"]})
    return True


def view_echo(state, echo_id):
    """只读查看回响；返回信息字典，绝不修改或删除状态。返回 False 表示不存在。"""
    echo = state["echoes"].get(echo_id)
    if echo is None:
        return False
    return {
        "id": echo_id,
        "name": echo["name"],
        "glade": echo["glade"],
        "mana": echo["mana"],
        "locked": echo["locked"],
        "triggered": bool(state["triggered"].get(echo_id)),
        "collected": echo_id in state["collected"],
    }


def inventory_text(state):
    """空背包返回明确文本，非空返回物品名列表的可读字符串。"""
    if not state["bag"]:
        return EMPTY_BAG_TEXT
    return "背包：" + "、".join(item["name"] for item in state["bag"])


def reset(state):
    """清空一切进度并恢复初始状态（修复“重置不清”）。返回全新状态字典。"""
    fresh = new_game()
    state.clear()
    state.update(fresh)
    return state


def save_game(state, path=SAVE_FILE):
    """存档：原样保存完整进度。"""
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(state, handle, ensure_ascii=False, indent=2)
    return True


def load_game(path=SAVE_FILE):
    """读档：返回恢复后的完整状态，进度可继续推进而不是重来。
    若编号计数缺失或偏小，按现存回响编号修正，杜绝读档后跳号/撞号。"""
    with open(path, "r", encoding="utf-8") as handle:
        state = json.load(handle)
    for key, value in new_game().items():
        state.setdefault(key, copy.deepcopy(value))
    max_id = 0
    for echo_id in list(state["echoes"].keys()):
        if echo_id.startswith("e"):
            try:
                max_id = max(max_id, int(echo_id[1:]))
            except ValueError:
                pass
    if state.get("next_echo_id", 0) <= max_id:
        state["next_echo_id"] = max_id + 1
    return state


@_atomic
def add_echo(state, name, glade_id, mana, locked=False):
    """向森林中加入一个新回响；编号沿计数器继续，读档后也不会跳号。"""
    if glade_id not in state["glades"]:
        return False
    if state["mana"] < 0:
        return False
    echo_id = "e%d" % state["next_echo_id"]
    state["echoes"][echo_id] = {
        "name": name,
        "glade": glade_id,
        "mana": mana,
        "locked": bool(locked),
    }
    state["next_echo_id"] += 1
    return echo_id


def main():
    state = new_game()
    print("world 命令: enter <空地> / trigger <回响> / unlock <回响> / "
          "collect <回响> / view <回响> / bag / save / load / reset / quit")
    while True:
        try:
            raw = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not raw or raw == "quit":
            break
        parts = raw.split()
        command = parts[0]
        target = parts[1] if len(parts) > 1 else None
        if command == "enter":
            print("ok" if enter_glade(state, target) else "failed")
        elif command == "trigger":
            print("ok" if trigger_echo(state, target) else "failed")
        elif command == "unlock":
            print("ok" if unlock_echo(state, target) else "failed")
        elif command == "collect":
            print("ok" if collect_echo(state, target) else "failed")
        elif command == "view":
            info = view_echo(state, target) if target else False
            print(info if info else "failed")
        elif command == "bag":
            print(inventory_text(state))
        elif command == "save":
            print("ok" if save_game(state) else "failed")
        elif command == "load":
            try:
                state = load_game()
                print("ok")
            except (OSError, ValueError):
                print("failed")
        elif command == "reset":
            reset(state)
            print("ok")
        else:
            print("unknown")


if __name__ == "__main__":
    main()
