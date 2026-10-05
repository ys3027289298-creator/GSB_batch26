"""太阳能农场：面板接入、校准调度、储能管理与存档持久化。

失败分类与恢复策略：
- InvalidInputError  非法输入：参数本身不合法，调用被拒绝且状态未被修改，
  修正参数后即可安全重试。
- CapacityError      容量不足：阵列已满或储能不够，先释放容量/扩容/等待
  充电，再重试同一操作。
- StateLockedError   状态锁定：农场处于维护锁定，变更类操作一律拒绝，
  先 unlock() 解锁再操作，锁定期间重试无意义。
"""

import json
import os
import tempfile


class SolarFarmError(Exception):
    """农场操作失败的基类。"""


class InvalidInputError(SolarFarmError):
    """非法输入：状态保持不变，修正参数后重试。"""


class CapacityError(SolarFarmError):
    """容量不足：释放容量或扩容后重试。"""


class StateLockedError(SolarFarmError):
    """状态锁定：解锁前变更类操作均被拒绝。"""


def new_game():
    return {
        "next_id": 1,
        "panels": {},           # pid -> {"id", "array", "calibrated"}
        "arrays": {},           # aid -> {"capacity", "panels": [pid, ...]}
        "pending": [],          # 待校准队列，先进先出
        "storage": 0,
        "storage_cap": 100,
        "locked": False,
        "discharged_events": [],  # 已处理放电事件 id，防止重复累计
    }


def _require_array(state, array_id):
    if array_id not in state["arrays"]:
        raise InvalidInputError(f"未知阵列: {array_id!r}")
    return state["arrays"][array_id]


def add_array(state, array_id, capacity):
    if not isinstance(capacity, int) or capacity <= 0:
        raise InvalidInputError("阵列容量必须为正整数")
    if array_id in state["arrays"]:
        raise InvalidInputError(f"阵列已存在: {array_id!r}")
    state["arrays"][array_id] = {"capacity": capacity, "panels": []}
    return array_id


def add_panel(state, array_id, panel_id=None):
    if panel_id is not None and not (
        isinstance(panel_id, int) and panel_id > 0 and not isinstance(panel_id, bool)
        or isinstance(panel_id, str) and panel_id
    ):
        raise InvalidInputError(f"面板编号非法: {panel_id!r}")
    array = _require_array(state, array_id)
    if panel_id is not None and panel_id in state["panels"]:
        raise InvalidInputError(f"面板重复: {panel_id!r}")
    if len(array["panels"]) >= array["capacity"]:
        raise CapacityError(f"阵列 {array_id!r} 已满，无法接入")
    if panel_id is None:
        panel_id = state["next_id"]
    if isinstance(panel_id, int):
        state["next_id"] = max(state["next_id"], panel_id + 1)
    state["panels"][panel_id] = {"id": panel_id, "array": array_id, "calibrated": False}
    array["panels"].append(panel_id)
    state["pending"].append(panel_id)
    return panel_id


def calibrate_next(state):
    if not state["pending"]:
        return None
    panel_id = state["pending"].pop(0)
    state["panels"][panel_id]["calibrated"] = True
    return panel_id


def view_panel(state, panel_id):
    panel = state["panels"].get(panel_id)
    if panel is None:
        raise InvalidInputError(f"未知面板: {panel_id!r}")
    return dict(panel)


def array_panels(state, array_id):
    array = _require_array(state, array_id)
    return list(array["panels"])


def storage_remaining(state):
    return state["storage_cap"] - state["storage"]


def charge(state, amount):
    if not isinstance(amount, int) or amount <= 0:
        raise InvalidInputError("充电量必须为正整数")
    if amount > storage_remaining(state):
        raise CapacityError("储能已满，无法继续充电")
    state["storage"] += amount
    return state["storage"]


def discharge(state, amount, event_id=None):
    if state["locked"]:
        raise StateLockedError("农场维护锁定中，禁止放电")
    if not isinstance(amount, int) or amount <= 0:
        raise InvalidInputError("放电量必须为正整数")
    if event_id is not None and event_id in state["discharged_events"]:
        return 0
    if amount > state["storage"]:
        raise CapacityError("储能不足，无法放电")
    state["storage"] -= amount
    if event_id is not None:
        state["discharged_events"].append(event_id)
    return amount


def lock(state):
    state["locked"] = True


def unlock(state):
    state["locked"] = False


def reset(state):
    state.clear()
    state.update(new_game())
    return state


_SAVE_KEYS = ("next_id", "panels", "arrays", "pending", "storage",
              "storage_cap", "locked", "discharged_events")


def save_game(state, path):
    data = {key: state[key] for key in _SAVE_KEYS}
    directory = os.path.dirname(os.path.abspath(path))
    fd, tmp = tempfile.mkstemp(dir=directory, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(data, fh, ensure_ascii=False, indent=2)
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise
    return path


def _restore_key(key):
    if isinstance(key, str) and key.isdigit():
        return int(key)
    return key


def load_game(path):
    if not os.path.exists(path):
        raise InvalidInputError(f"存档不存在: {path}")
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        raise InvalidInputError(f"存档损坏，无法读取: {exc}") from exc
    if not isinstance(data, dict):
        raise InvalidInputError("存档格式非法")
    state = new_game()
    for key in _SAVE_KEYS:
        if key in data:
            state[key] = data[key]
    state["panels"] = {_restore_key(k): v for k, v in state["panels"].items()}
    if not isinstance(state["next_id"], int) or state["next_id"] < 1:
        state["next_id"] = 1
    int_ids = [pid for pid in state["panels"] if isinstance(pid, int)]
    if int_ids:
        state["next_id"] = max(state["next_id"], max(int_ids) + 1)
    if not 0 <= state["storage"] <= state["storage_cap"]:
        raise InvalidInputError("存档储能数据越界")
    return state


def main():
    print("save 命令: run/quit")
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
