"""发条先知预报事件模块。

发条先知接收事件预报，存入观测台槽位，按到达先后依次观测处理，
并以发条计数记录已完成的预报。支持锁定、重置与存档/读档。

三类失败及恢复策略：
- 非法输入 (InvalidForecastError)：预报内容为空或类型不合法。
  恢复：状态未被修改，修正输入后重试即可。
- 容量不足 (ObservatoryFullError)：观测台槽位已满。
  恢复：先调用 observe() 处理最旧的预报腾出槽位，或提高 capacity 后重试。
- 状态锁定 (OracleLockedError)：先知处于锁定状态，拒绝一切写操作。
  恢复：调用 unlock() 解锁后重试；锁定期间查看类操作仍可用。
"""

import json

DEFAULT_CAPACITY = 8


class ForecastError(Exception):
    """预报操作失败基类，recovery 字段给出恢复策略。"""

    def __init__(self, message, recovery):
        super().__init__(message)
        self.recovery = recovery


class InvalidForecastError(ForecastError):
    """非法输入：预报内容为空或不是字符串。"""

    def __init__(self, event):
        super().__init__(
            "非法预报内容: %r" % (event,),
            "修正预报内容（非空字符串）后重新提交；当前状态未被修改。",
        )


class ObservatoryFullError(ForecastError):
    """容量不足：观测台槽位已满。"""

    def __init__(self, capacity):
        super().__init__(
            "观测台已满（容量 %d）" % capacity,
            "先调用 observe() 处理最旧的预报腾出槽位，或提高 capacity 后重试。",
        )


class OracleLockedError(ForecastError):
    """状态锁定：锁定期间拒绝写操作。"""

    def __init__(self):
        super().__init__(
            "发条先知已锁定",
            "调用 unlock() 解锁后重试；锁定期间 view_* 等只读操作仍可用。",
        )


def new_game(capacity=DEFAULT_CAPACITY):
    return {
        "forecasts": [],   # 观测台中的预报，按到达先后排列
        "processed": [],   # 已观测处理的预报
        "capacity": capacity,
        "clockwork": 0,    # 发条计数：已完成的预报数
        "next_id": 1,      # 下一个预报编号
        "locked": False,
    }


def _require_unlocked(state):
    if state["locked"]:
        raise OracleLockedError()


def forecast(state, event):
    """提交一条预报。成功返回预报编号。

    - 重复预报：同一事件已在观测台中则直接返回原编号，不重复占位。
    - 容量不足：观测台满时抛出 ObservatoryFullError。
    - 状态锁定：锁定时抛出 OracleLockedError。
    - 非法输入：内容为空或非字符串时抛出 InvalidForecastError。
    """
    _require_unlocked(state)
    if not isinstance(event, str) or not event.strip():
        raise InvalidForecastError(event)
    for entry in state["forecasts"]:
        if entry["event"] == event:
            return entry["id"]
    if len(state["forecasts"]) >= state["capacity"]:
        raise ObservatoryFullError(state["capacity"])
    entry = {"id": state["next_id"], "event": event}
    state["next_id"] += 1  # 单次预报只累计一次编号
    state["forecasts"].append(entry)
    return entry["id"]


def view_forecasts(state):
    """查看观测台中的预报（只读，不会删除）。"""
    return list(state["forecasts"])


def view_next(state):
    """查看下一条待观测预报；空预报时返回 None，不返回占位文本。"""
    if not state["forecasts"]:
        return None
    return state["forecasts"][0]


def observe(state):
    """观测处理最先到达的预报（FIFO），返回该预报；空预报返回 None。"""
    _require_unlocked(state)
    if not state["forecasts"]:
        return None
    entry = state["forecasts"].pop(0)
    state["processed"].append(entry)
    state["clockwork"] += 1  # 每处理一条预报，发条累计一次
    return entry


def lock(state):
    state["locked"] = True


def unlock(state):
    state["locked"] = False


def reset(state):
    """重置：清空全部预报、处理记录、发条计数与编号。"""
    state["forecasts"].clear()
    state["processed"].clear()
    state["clockwork"] = 0
    state["next_id"] = 1
    state["locked"] = False


def save(state):
    """存档：完整保存队列、计数与编号，保证读档后编号连续。"""
    return json.dumps(
        {
            "forecasts": state["forecasts"],
            "processed": state["processed"],
            "capacity": state["capacity"],
            "clockwork": state["clockwork"],
            "next_id": state["next_id"],
            "locked": state["locked"],
        }
    )


def load(data):
    """读档：恢复存档中的 next_id，新预报编号接着走、不跳号。"""
    payload = json.loads(data)
    state = new_game(capacity=payload["capacity"])
    state["forecasts"] = list(payload["forecasts"])
    state["processed"] = list(payload["processed"])
    state["clockwork"] = payload["clockwork"]
    state["next_id"] = payload["next_id"]
    state["locked"] = payload["locked"]
    return state


def main():
    print("events 命令: forecast <事件> / observe / view / next / lock / unlock / reset / quit")
    state = new_game()
    handlers = {
        "observe": lambda arg: observe(state),
        "view": lambda arg: view_forecasts(state),
        "next": lambda arg: view_next(state),
        "lock": lambda arg: lock(state) or "locked",
        "unlock": lambda arg: unlock(state) or "unlocked",
        "reset": lambda arg: reset(state) or "reset",
    }
    while True:
        try:
            raw = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not raw or raw == "quit":
            break
        verb, _, arg = raw.partition(" ")
        try:
            if verb == "forecast":
                print(forecast(state, arg))
            elif verb in handlers:
                print(handlers[verb](arg))
            else:
                print("未知命令")
        except ForecastError as exc:
            print("失败: %s；恢复策略: %s" % (exc, exc.recovery))


if __name__ == "__main__":
    main()
