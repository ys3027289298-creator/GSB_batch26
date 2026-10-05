"""深海海沟探测任务 —— 存档模块。

潜水器下潜到海沟、采集样本、管理氧气，支持暂停/恢复与 JSON 存档。

状态字典关键字段：
    depth     当前深度（米）
    src       主氧罐余量
    dst       累计消耗氧气（src + dst 恒等于初始氧气，不会少算）
    items     样本舱（已采集样本，dict 列表）
    capacity  样本舱容量
    queue     待登记样本编号队列（先进先出，先到先登记）
    events    已登记样本 {编号: (到达序号, 深度)}
    next_id   下一个样本编号（先取号后自增，读档不跳号）
    paused    暂停标志（暂停期间禁止下潜与采集）

已修复的十个问题：
    1. 重复样本         rule_c：样本登记幂等，同一编号重复登记被拒绝。
    2. 样本舱满仍采集   rule_f / collect_sample：舱满时采集直接拒绝。
    3. 空样本返回文本   rule_d / view_sample：空舱返回 None，不再返回占位文本。
    4. 先到样本未登记   rule_h / rule_e：队列先进先出，按到达序号取最早样本。
    5. 暂停仍下潜       rule_b / dive：暂停或舱门关闭时下潜被拒绝。
    6. 查看样本误删     rule_e / view_sample：查看为只读操作，不移除样本。
    7. 氧气少算         rule_a：余量不足拒绝扣减，消耗准确记入 dst，不出现负氧。
    8. 单次采集重复累计 rule_g：采集计数幂等，同一编号只累计一次。
    9. 重置不清         reset_mission：清空全部字段并恢复初始值，含 next_id。
   10. 读档跳号         rule_j / load_game：先取号后自增，存档完整恢复 next_id。

暂停/恢复行为：
    pause_mission 后，dive 与 collect_sample 立即被拒绝（返回 False/None），
    深度、氧气、样本舱、登记队列全部冻结；resume_mission 后从冻结点继续，
    编号与氧气无缝衔接。暂停与恢复均幂等：重复调用返回 False 且不改状态。
    暂停标志随 save_game 持久化，读档后仍处于暂停，须 resume 才能继续。

损坏存档行为：
    load_game 遇到文件缺失、JSON 损坏、字段缺失或类型非法时，不抛异常、
    不删除也不覆盖原存档文件，而是返回一个全新的初始状态，并置
    state["save_recovered"] = True，调用方可据此提示“存档损坏，已重新开局”。
"""

import json

START_OXYGEN = 100
SAMPLE_CAPACITY = 5
DIVE_OXYGEN_COST = 10
DIVE_DEPTH_STEP = 100
DEFAULT_SAVE_PATH = "trench_save.json"

__all__ = [
    "new_game", "main",
    "rule_a", "rule_b", "rule_c", "rule_d", "rule_e",
    "rule_f", "rule_g", "rule_h", "rule_i", "rule_j",
    "dive", "collect_sample", "view_sample",
    "pause_mission", "resume_mission", "reset_mission",
    "save_game", "load_game",
]


def new_game():
    return {
        "depth": 0,
        "src": START_OXYGEN,
        "dst": 0,
        "items": [],
        "capacity": SAMPLE_CAPACITY,
        "queue": [],
        "events": {},
        "seq": 0,
        "next_id": 1,
        "collected": 0,
        "counted": [],
        "paused": False,
        "closed": False,
    }


def rule_a(state):
    """氧气结算：从主氧罐 src 扣 10 单位并记入 dst；余量不足拒绝扣减。"""
    if state["src"] < DIVE_OXYGEN_COST:
        return False
    state["src"] -= DIVE_OXYGEN_COST
    state["dst"] += DIVE_OXYGEN_COST
    return True


def rule_b(state):
    """是否允许行动：暂停或舱门关闭时拒绝。"""
    return not state.get("paused", False) and not state.get("closed", False)


def rule_c(state):
    """登记当前待登记样本：同一编号重复登记被拒绝（幂等）。"""
    sid = state["next_id"]
    if sid in state["events"]:
        return False
    state["seq"] = state.get("seq", 0) + 1
    state["events"][sid] = (state["seq"], state.get("depth", 0))
    return True


def rule_d(state):
    """查看最新样本：空舱返回 None，不返回占位文本；只读，不删除。"""
    if not state.get("items"):
        return None
    return state["items"][-1]


def rule_e(state):
    """查看最早到达的已登记样本编号：按到达序号最小选取，只读不删除。"""
    return min(state["events"].items(), key=lambda item: item[1][0])[0]


def rule_f(state):
    """样本舱是否已满：满舱时采集必须被拒绝。"""
    return len(state.get("items", [])) >= state.get("capacity", SAMPLE_CAPACITY)


def rule_g(state):
    """累计一次采集计数：同一编号只累计一次（幂等）。"""
    sid = state["next_id"]
    counted = state.setdefault("counted", [])
    if sid in counted:
        return False
    counted.append(sid)
    state["collected"] = state.get("collected", 0) + 1
    return True


def rule_h(state):
    """从待登记队列取出最早到达的样本编号（先进先出）。"""
    return state["queue"].pop(0)


def rule_i(state):
    """当前样本数量：只读统计，不删除、不漏算。"""
    return len(state["items"])


def rule_j(state):
    """分配样本编号：先取号、后自增，读档后从 next_id 继续，不跳号。"""
    current = state["next_id"]
    state["next_id"] += 1
    return current


def dive(state):
    """下潜 100 米：暂停/关闭或氧气不足时被拒绝，状态保持不变。"""
    if not rule_b(state):
        return False
    if not rule_a(state):
        return False
    state["depth"] += DIVE_DEPTH_STEP
    return True


def collect_sample(state, name="sample"):
    """采集一个样本：暂停或舱满时拒绝；登记、计数、取号均幂等不重复。"""
    if not rule_b(state):
        return None
    if rule_f(state):
        return None
    rule_g(state)
    rule_c(state)
    sid = rule_j(state)
    sample = {"id": sid, "name": name, "depth": state["depth"]}
    state["items"].append(sample)
    state["queue"].append(sid)
    return sid


def view_sample(state, sid=None):
    """查看样本（只读，不删除）；空舱或编号不存在时返回 None。"""
    if not state["items"]:
        return None
    if sid is None:
        return state["items"][-1]
    for sample in state["items"]:
        if sample["id"] == sid:
            return sample
    return None


def pause_mission(state):
    """暂停任务：冻结下潜与采集；重复暂停返回 False 且状态不变。"""
    if state.get("paused"):
        return False
    state["paused"] = True
    return True


def resume_mission(state):
    """恢复任务：从暂停点继续；未暂停时调用返回 False 且状态不变。"""
    if not state.get("paused"):
        return False
    state["paused"] = False
    return True


def reset_mission(state):
    """重置任务：清空全部任务数据并恢复初始值（含 next_id、计数与队列）。"""
    state.clear()
    state.update(new_game())
    return state


def save_game(state, path=DEFAULT_SAVE_PATH):
    """存档：完整写入 JSON（含 next_id），读档后编号连续不跳号。"""
    data = dict(state)
    data["version"] = 1
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2)
    return path


def _is_valid_save(data):
    if not isinstance(data, dict):
        return False
    checks = [
        ("depth", int), ("src", int), ("dst", int),
        ("items", list), ("capacity", int), ("queue", list),
        ("events", dict), ("seq", int), ("next_id", int),
        ("collected", int), ("counted", list),
        ("paused", bool), ("closed", bool),
    ]
    for key, typ in checks:
        if key not in data or not isinstance(data[key], typ):
            return False
    return data["next_id"] >= 1


def load_game(path=DEFAULT_SAVE_PATH):
    """读档：恢复完整状态；存档缺失或损坏时返回初始状态并标记 save_recovered。"""
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, ValueError):
        data = None
    if not _is_valid_save(data):
        state = new_game()
        state["save_recovered"] = True
        return state
    data.pop("version", None)
    state = new_game()
    state.update(data)
    state["events"] = {int(k): tuple(v) for k, v in data["events"].items()}
    return state


def main():
    print("深海海沟任务 save 模块")
    print("命令: dive/collect/samples/view/pause/resume/save/load/reset/quit")
    state = new_game()
    while True:
        try:
            raw = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not raw or raw == "quit":
            break
        if raw == "dive":
            if dive(state):
                print(f"下潜至 {state['depth']} 米，氧气余量 {state['src']}")
            else:
                print("下潜被拒绝（暂停中或氧气不足）")
        elif raw == "collect":
            sid = collect_sample(state)
            print(f"已采集样本 #{sid}" if sid is not None else "采集被拒绝（暂停中或样本舱已满）")
        elif raw == "samples":
            print(f"样本舱 {rule_i(state)}/{state['capacity']}: {state['items']}")
        elif raw == "view":
            print(view_sample(state))
        elif raw == "pause":
            print("已暂停" if pause_mission(state) else "已处于暂停状态")
        elif raw == "resume":
            print("已恢复" if resume_mission(state) else "任务未在暂停")
        elif raw == "save":
            print("已存档:", save_game(state))
        elif raw == "load":
            state = load_game()
            print("读档完成" + ("（存档损坏，已重新开局）" if state.get("save_recovered") else ""))
        elif raw == "reset":
            reset_mission(state)
            print("已重置")
        else:
            print("未知命令")


if __name__ == "__main__":
    main()
