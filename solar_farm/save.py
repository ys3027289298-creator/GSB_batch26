"""太阳能农场保存与调度模块。

修复的持久化边界问题:
  1. 重复面板: 面板编号唯一, 重复接入视为非法输入。
  2. 阵列满仍接入: 接入前检查阵列剩余容量, 满员拒绝且不改状态。
  3. 空阵列返回文本: 空阵列返回空列表, 不再返回 "empty" 之类的文本。
  4. 先到面板未校准: 按到达顺序 (FIFO) 校准, 先到的面板优先。
  5. 锁定仍放电: 农场锁定期间禁止放电。
  6. 查看面板误删: 查看是纯读操作, 不再从阵列中移除面板。
  7. 储能少算: 储能总量统计所有电池的电量之和。
  8. 单次放电重复累计: 每次放电事件只结算一次, 重复结算返回 False。
  9. 重置不清: 重置清空全部运行状态 (含锁定/放电记录/编号计数器)。
 10. 读档跳号: 读档后 next_id 至少为现有最大面板编号 + 1, 不复用不跳号。

失败分类与恢复策略:
  IllegalInputError  非法输入 (重复编号/非法容量/非法电量/坏存档)
                     -> 拒绝本次操作, 状态保持不变, 调用方修正参数后重试。
  CapacityError      容量不足 (阵列满/储能剩余空间不足)
                     -> 本次操作不入账, 先释放空间或扩容后重试同一操作。
  StateLockedError   状态锁定 (农场维护锁定中)
                     -> 本次操作被禁止, 先 unlock_farm 解锁, 再重放该操作。
所有失败都在修改状态之前抛出, 保证失败后状态与操作前一致 (原子性)。
"""

import json
import os


class SolarFarmError(Exception):
    """太阳能农场操作失败的基类。"""


class IllegalInputError(SolarFarmError):
    """非法输入: 修正参数后重试, 当前状态未被改动。"""


class CapacityError(SolarFarmError):
    """容量不足: 释放空间或扩容后重试同一操作。"""


class StateLockedError(SolarFarmError):
    """状态锁定: 解锁后重放该操作。"""


RECOVERY_STRATEGIES = {
    "illegal_input": "reject_and_fix_args",
    "capacity": "free_space_or_expand_then_retry",
    "state_locked": "unlock_then_replay",
}


def recovery_for(exc):
    """根据异常类型返回恢复策略标识。"""
    if isinstance(exc, IllegalInputError):
        return RECOVERY_STRATEGIES["illegal_input"]
    if isinstance(exc, CapacityError):
        return RECOVERY_STRATEGIES["capacity"]
    if isinstance(exc, StateLockedError):
        return RECOVERY_STRATEGIES["state_locked"]
    raise TypeError("未知的农场异常类型: %r" % (exc,))


def new_game():
    """创建一份全新的农场状态。"""
    return {
        "panels": {},        # panel_id -> {"array": name, "calibrated": bool}
        "arrays": {},        # array_name -> {"capacity": int, "panels": [panel_id, ...]}
        "arrival_queue": [], # 未校准面板, 按到达顺序 (FIFO)
        "batteries": {},     # battery_name -> {"capacity": float, "charge": float}
        "next_id": 1,
        "locked": False,
        "discharged_events": set(),  # 已结算的放电事件 (仅内存, 不持久化)
    }


def create_array(state, name, capacity):
    """新建阵列。容量必须是正整数, 名称不得重复。"""
    if not isinstance(capacity, int) or isinstance(capacity, bool) or capacity <= 0:
        raise IllegalInputError("阵列容量必须是正整数: %r" % (capacity,))
    if name in state["arrays"]:
        raise IllegalInputError("阵列已存在: %r" % (name,))
    state["arrays"][name] = {"capacity": capacity, "panels": []}
    return True


def add_battery(state, name, capacity):
    """新增储能电池。容量必须是正数, 名称不得重复。"""
    if not isinstance(capacity, (int, float)) or isinstance(capacity, bool) or capacity <= 0:
        raise IllegalInputError("电池容量必须是正数: %r" % (capacity,))
    if name in state["batteries"]:
        raise IllegalInputError("电池已存在: %r" % (name,))
    state["batteries"][name] = {"capacity": float(capacity), "charge": 0.0}
    return True


def _check_unlocked(state):
    if state["locked"]:
        raise StateLockedError("农场处于锁定状态, 请先解锁")


def connect_panel(state, array_name):
    """接入一块新面板到指定阵列, 返回分配的面板编号。

    修复点: 编号全局唯一 (不重复面板); 阵列满时拒绝接入 (容量不足)。
    """
    _check_unlocked(state)
    array = state["arrays"].get(array_name)
    if array is None:
        raise IllegalInputError("阵列不存在: %r" % (array_name,))
    if len(array["panels"]) >= array["capacity"]:
        raise CapacityError("阵列 %r 已满 (%d/%d)" % (
            array_name, len(array["panels"]), array["capacity"]))
    panel_id = state["next_id"]
    state["next_id"] += 1
    state["panels"][panel_id] = {"array": array_name, "calibrated": False}
    array["panels"].append(panel_id)
    state["arrival_queue"].append(panel_id)
    return panel_id


def calibrate_next(state):
    """校准最早到达且尚未校准的面板 (FIFO), 返回其编号; 无待校准返回 None。"""
    _check_unlocked(state)
    while state["arrival_queue"]:
        panel_id = state["arrival_queue"][0]
        panel = state["panels"].get(panel_id)
        if panel is not None and not panel["calibrated"]:
            panel["calibrated"] = True
            state["arrival_queue"].pop(0)
            return panel_id
        state["arrival_queue"].pop(0)  # 清理失效条目
    return None


def view_panels(state, array_name):
    """查看阵列中的面板编号列表。纯读操作, 不会移除任何面板。

    修复点: 空阵列返回空列表而不是文本; 查看不再误删面板。
    """
    array = state["arrays"].get(array_name)
    if array is None:
        raise IllegalInputError("阵列不存在: %r" % (array_name,))
    return list(array["panels"])


def charge_battery(state, battery_name, amount):
    """向电池充电。电量必须为正, 且不得超过剩余容量 (容量不足则整体拒绝)。"""
    _check_unlocked(state)
    battery = state["batteries"].get(battery_name)
    if battery is None:
        raise IllegalInputError("电池不存在: %r" % (battery_name,))
    if not isinstance(amount, (int, float)) or isinstance(amount, bool) or amount <= 0:
        raise IllegalInputError("充电量必须是正数: %r" % (amount,))
    free = battery["capacity"] - battery["charge"]
    if amount > free:
        raise CapacityError("电池 %r 剩余容量不足: 需要 %s, 仅剩 %s" % (
            battery_name, amount, free))
    battery["charge"] += amount
    return True


def storage_total(state):
    """储能总量: 所有电池电量之和 (修复少算, 不再只算第一块)。"""
    return sum(b["charge"] for b in state["batteries"].values())


def discharge(state, event_id, amount):
    """按事件放电, 返回实际放出的电量。

    修复点: 锁定期间禁止放电; 同一事件只结算一次, 重复调用返回 False。
    """
    _check_unlocked(state)
    if not isinstance(amount, (int, float)) or isinstance(amount, bool) or amount <= 0:
        raise IllegalInputError("放电量必须是正数: %r" % (amount,))
    if event_id in state["discharged_events"]:
        return False  # 已结算过, 不重复累计
    remaining = amount
    for battery in state["batteries"].values():
        if remaining <= 0:
            break
        taken = min(battery["charge"], remaining)
        battery["charge"] -= taken
        remaining -= taken
    delivered = amount - remaining
    state["discharged_events"].add(event_id)
    return delivered


def lock_farm(state):
    """锁定农场 (维护模式): 锁定期间禁止接入/校准/充放电。"""
    state["locked"] = True
    return True


def unlock_farm(state):
    """解锁农场, 之后可重放被锁定拒绝的操作。"""
    state["locked"] = False
    return True


def reset(state):
    """原地重置农场: 清空全部运行状态, 编号从 1 重新计数 (修复重置不清)。"""
    state.clear()
    state.update(new_game())
    return True


# ---- 持久化边界 ----

_PERSISTED_SCALARS = ("next_id", "locked")


def _serialize(state):
    """只持久化可序列化的纯数据; 放电结算记录属于运行时状态, 不入档。"""
    return {
        "version": 1,
        "panels": {str(pid): dict(p) for pid, p in state["panels"].items()},
        "arrays": {name: {"capacity": a["capacity"], "panels": list(a["panels"])}
                   for name, a in state["arrays"].items()},
        "arrival_queue": list(state["arrival_queue"]),
        "batteries": {name: dict(b) for name, b in state["batteries"].items()},
        "next_id": state["next_id"],
        "locked": state["locked"],
    }


def _validate_payload(data):
    """校验读档数据, 坏档视为非法输入, 不污染当前状态。"""
    if not isinstance(data, dict):
        raise IllegalInputError("存档必须是对象")
    for key in ("panels", "arrays", "arrival_queue", "batteries"):
        if not isinstance(data.get(key), (dict, list)):
            raise IllegalInputError("存档缺少字段: %s" % key)
    if not isinstance(data["panels"], dict) or not isinstance(data["arrays"], dict):
        raise IllegalInputError("存档 panels/arrays 必须是对象")
    if not isinstance(data["arrival_queue"], list) or not isinstance(data["batteries"], dict):
        raise IllegalInputError("存档 arrival_queue/batteries 类型错误")
    next_id = data.get("next_id")
    if not isinstance(next_id, int) or isinstance(next_id, bool) or next_id < 1:
        raise IllegalInputError("存档 next_id 非法: %r" % (next_id,))


def save_game(state, path):
    """原子写档: 先写临时文件再替换, 避免写一半留下坏档。"""
    payload = _serialize(state)
    tmp_path = path + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)
    os.replace(tmp_path, path)
    return True


def load_game(state, path):
    """读档到现有状态。坏档抛 IllegalInputError 且当前状态不变。

    修复读档跳号: next_id 取 存档值 与 现有最大面板编号 + 1 的较大者,
    保证之后接入的面板编号既不复用也不跳号。
    """
    with open(path, "r", encoding="utf-8") as fh:
        try:
            data = json.load(fh)
        except json.JSONDecodeError as exc:
            raise IllegalInputError("存档不是合法 JSON: %s" % exc) from exc
    _validate_payload(data)

    panels = {int(pid): {"array": p["array"], "calibrated": bool(p["calibrated"])}
              for pid, p in data["panels"].items()}
    arrays = {name: {"capacity": int(a["capacity"]), "panels": [int(x) for x in a["panels"]]}
              for name, a in data["arrays"].items()}
    batteries = {name: {"capacity": float(b["capacity"]), "charge": float(b["charge"])}
                 for name, b in data["batteries"].items()}

    max_panel_id = max(panels.keys(), default=0)
    next_id = max(int(data["next_id"]), max_panel_id + 1)

    state.clear()
    state.update({
        "panels": panels,
        "arrays": arrays,
        "arrival_queue": [int(x) for x in data["arrival_queue"]],
        "batteries": batteries,
        "next_id": next_id,
        "locked": bool(data.get("locked", False)),
        "discharged_events": set(),
    })
    return True


def main():
    print("save 命令: run/quit")
    state = new_game()
    while True:
        try:
            raw = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not raw or raw == "quit":
            break
        if raw == "run":
            print("panels=%d storage=%s" % (len(state["panels"]), storage_total(state)))
        else:
            print("ok")


if __name__ == "__main__":
    main()
