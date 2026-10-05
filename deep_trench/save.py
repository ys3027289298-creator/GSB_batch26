"""深海海沟（deep_trench）存档与领域逻辑模块。

职责：
- 领域规则：下潜耗氧、样本舱容量、样本去重、采集一次性累计、
  暂停/恢复、重置、样本编号分配。
- 存档持久化：JSON 原子写入、读档校验、损坏存档隔离。

行为说明（详细版见 README.md）：
- 暂停（paused=True）时禁止下潜，恢复（resume）后按当前氧气正常下潜。
- 存档损坏（非法 JSON 或结构校验失败）时，原文件被隔离为
  ``<存档名>.corrupt`` 以便排查，``load_or_new`` 随后返回全新游戏状态。
"""

import json
import os

SAVE_VERSION = 1

# 每下潜 1 米消耗 1 点氧气；氧气不足时拒绝下潜，绝不允许扣成负数。
OXYGEN_PER_METER = 1

DEFAULT_OXYGEN = 100
DEFAULT_CAPACITY = 5


class TrenchError(Exception):
    """深海海沟领域错误基类。"""


class DuplicateSampleError(TrenchError):
    """重复样本：同一编号已登记，拒绝再次登记。"""


class ChamberFullError(TrenchError):
    """样本舱已满：容量用尽时拒绝继续采集。"""


class PausedError(TrenchError):
    """任务暂停中：禁止下潜。"""


class CorruptSaveError(TrenchError):
    """存档损坏：内容不是合法 JSON 或未通过结构校验。"""


def new_game():
    """返回一份全新的游戏状态。"""
    return {
        "version": SAVE_VERSION,
        "oxygen": DEFAULT_OXYGEN,
        "depth": 0,
        "capacity": DEFAULT_CAPACITY,
        "samples": {},        # 编号字符串 -> {"id": int, "name": str}
        "arrivals": {},       # 编号字符串 -> (到达次序, 名称)，先到先登记
        "queue": [],          # 待查看样本编号（查看不删除）
        "collected": {},      # 编号字符串 -> 累计次数（单次采集只累计一次）
        "paused": False,
        "next_id": 1,
    }


# ---------------------------------------------------------------- 通用纯函数
# engine.py 中的 rule_* 是这些纯函数在固定字段上的薄封装。

def transfer(state, src, dst, amount):
    """从 src 转移 amount 到 dst；余额不足时拒绝且不改动任何字段。"""
    if state.get(src, 0) < amount:
        return False
    state[src] -= amount
    state[dst] = state.get(dst, 0) + amount
    return True


def gate(state, flag):
    """开关为真时拒绝操作（如暂停时下潜）。"""
    return not state.get(flag, False)


def register_once(events, key):
    """事件去重登记：首次登记返回 True，重复登记返回 False。"""
    if key in events:
        return False
    events[key] = True
    return True


def empty_reply(items):
    """空集合返回 False（调用方据此给出空提示文本），否则返回集合本身。"""
    return items if items else False


def pick_earliest(events):
    """按到达次序（元组第 0 位）取最早事件的键，即先到先处理。"""
    return min(events.items(), key=lambda item: item[1][0])[0]


def reset_fields(state, fields):
    """重置指定字段；没有任何可重置字段时返回 False。"""
    cleared = False
    for field in fields:
        if field in state:
            del state[field]
            cleared = True
    return cleared


def one_shot(state, flag):
    """一次性开关：首次触发返回 True 并置位，之后一律返回 False。"""
    if state.get(flag):
        return False
    state[flag] = True
    return True


def peek_front(queue):
    """查看队首元素但不移除（查看不等于取出）。"""
    return queue[0]


def remaining_capacity(items, cap):
    """剩余容量 = 容量上限 - 已用数量，不做差一修正。"""
    return cap - len(items)


def alloc_id(state):
    """分配当前编号后再自增，保证编号连续、读档不跳号。"""
    allocated = state["next_id"]
    state["next_id"] = allocated + 1
    return allocated


# ---------------------------------------------------------------- 领域操作

def dive(state, meters):
    """下潜 meters 米。暂停中拒绝；氧气不足时拒绝且不扣氧。"""
    if state.get("paused"):
        raise PausedError("任务已暂停，禁止下潜")
    cost = meters * OXYGEN_PER_METER
    if state["oxygen"] < cost:
        return False
    state["oxygen"] -= cost
    state["depth"] += meters
    return True


def pause(state):
    """暂停任务：暂停期间 dive 一律被拒绝。"""
    state["paused"] = True


def resume(state):
    """恢复任务：解除暂停，之后按当前氧气正常下潜。"""
    state["paused"] = False


def arrive_sample(state, name, seq):
    """样本到达，按到达次序 seq 排队，等待登记。"""
    sample_id = alloc_id(state)
    state["arrivals"][str(sample_id)] = (seq, name)
    return sample_id


def register_next(state):
    """登记最早到达且尚未登记的样本；重复编号或舱满时拒绝。"""
    if not state["arrivals"]:
        return None
    key = pick_earliest(state["arrivals"])
    _, name = state["arrivals"].pop(key)
    return collect_sample(state, int(key), name)


def collect_sample(state, sample_id, name):
    """采集并登记样本。

    - 重复编号：拒绝（重复样本）。
    - 舱满：拒绝（样本舱满仍采集）。
    - 同一编号只累计一次（单次采集重复累计）。
    """
    key = str(sample_id)
    if key in state["samples"]:
        raise DuplicateSampleError("样本 %s 已登记" % key)
    if len(state["samples"]) >= state["capacity"]:
        raise ChamberFullError("样本舱已满（%d/%d）" % (len(state["samples"]), state["capacity"]))
    state["samples"][key] = {"id": sample_id, "name": name}
    state["collected"][key] = state["collected"].get(key, 0) + 1
    return sample_id


def view_samples(state):
    """查看样本：只读，绝不删除任何样本或队列元素。"""
    return dict(state["samples"])


def format_samples(state):
    """样本清单文本；没有样本时返回空提示文本而不是空串。"""
    if not state["samples"]:
        return "样本舱为空"
    lines = ["样本舱（%d/%d）：" % (len(state["samples"]), state["capacity"])]
    for key in sorted(state["samples"], key=int):
        record = state["samples"][key]
        lines.append("#%d %s" % (record["id"], record["name"]))
    return "\n".join(lines)


def reset(state):
    """重置任务进度：清空全部进度字段，恢复初始值，不留残余。"""
    state.clear()
    state.update(new_game())
    return state


# ---------------------------------------------------------------- 存档持久化

def validate(state):
    """校验读档状态结构；不合法时抛出 CorruptSaveError。"""
    if not isinstance(state, dict):
        raise CorruptSaveError("存档不是状态对象")
    for field in ("oxygen", "depth", "capacity", "next_id"):
        if not isinstance(state.get(field), int):
            raise CorruptSaveError("存档缺少整数字段: %s" % field)
    for field in ("samples", "arrivals", "collected"):
        if not isinstance(state.get(field), dict):
            raise CorruptSaveError("存档缺少字典字段: %s" % field)
    if not isinstance(state.get("queue"), list):
        raise CorruptSaveError("存档缺少列表字段: queue")
    if not isinstance(state.get("paused"), bool):
        raise CorruptSaveError("存档缺少布尔字段: paused")
    return True


def save_game(state, path):
    """原子写入存档：先写临时文件再替换，避免半截文件。"""
    tmp_path = path + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as handle:
        json.dump(state, handle, ensure_ascii=False, indent=2)
    os.replace(tmp_path, path)
    return path


def quarantine(path):
    """把损坏存档隔离为 ``<path>.corrupt``，返回隔离后的路径。"""
    corrupt_path = path + ".corrupt"
    try:
        os.replace(path, corrupt_path)
    except OSError:
        pass
    return corrupt_path


def load_game(path):
    """读取存档。

    - 文件不存在：抛出 FileNotFoundError。
    - 内容损坏或校验失败：隔离原文件后抛出 CorruptSaveError。
    """
    with open(path, "r", encoding="utf-8") as handle:
        try:
            state = json.load(handle)
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            quarantine(path)
            raise CorruptSaveError("存档损坏，已隔离: %s" % path) from exc
    try:
        validate(state)
    except CorruptSaveError:
        quarantine(path)
        raise
    return state


def load_or_new(path):
    """读取存档；文件不存在或已损坏时返回全新游戏状态。"""
    try:
        return load_game(path)
    except (FileNotFoundError, CorruptSaveError):
        return new_game()


def main():
    print("save 命令: dive <米> / pause / resume / arrive <名字> / register /")
    print("           collect <编号> <名字> / samples / reset / save <路径> /")
    print("           load <路径> / quit")
    state = new_game()
    while True:
        try:
            raw = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not raw or raw == "quit":
            break
        parts = raw.split()
        command, args = parts[0], parts[1:]
        try:
            if command == "dive" and len(args) == 1:
                print("ok" if dive(state, int(args[0])) else "氧气不足")
            elif command == "pause":
                pause(state)
                print("已暂停")
            elif command == "resume":
                resume(state)
                print("已恢复")
            elif command == "arrive" and len(args) == 1:
                print("到达样本 #%d" % arrive_sample(state, args[0], len(state["arrivals"])))
            elif command == "register":
                print("登记 #%s" % register_next(state))
            elif command == "collect" and len(args) == 2:
                print("采集 #%d" % collect_sample(state, int(args[0]), args[1]))
            elif command == "samples":
                print(format_samples(state))
            elif command == "reset":
                reset(state)
                print("已重置")
            elif command == "save" and len(args) == 1:
                save_game(state, args[0])
                print("已存档")
            elif command == "load" and len(args) == 1:
                state = load_or_new(args[0])
                print("已读档")
            else:
                print("未知命令")
        except TrenchError as exc:
            print("拒绝: %s" % exc)


if __name__ == "__main__":
    main()
