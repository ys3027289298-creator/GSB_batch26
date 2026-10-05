"""太阳帆船航程保存模块。

状态模型（state 为纯 dict，仅含 JSON 可序列化字段）：
- routes: 已保存航线名列表（去重）
- sails: 帆面列表，每项 {"name": str, "deployed": bool}
- legs: 待通过航段队列（先进先出）
- energy: 当前光能
- voyages: 已完成航行记录 {voyage_id: legs}
- voyage_count: 累计航行次数（同一 voyage_id 只计一次）
- paused: 是否暂停
- next_id: 下一个存档编号
- log: 航行日志

配套 engine.py 中 rule_a..rule_j 与本模块操作一一对应。
"""

import copy
import json

SAIL_CAPACITY = 4
LEG_ENERGY_COST = 10


def new_game():
    """新航程初始状态。"""
    return {
        "routes": [],
        "sails": [],
        "legs": [],
        "energy": 0,
        "voyages": {},
        "voyage_count": 0,
        "paused": False,
        "next_id": 1,
        "log": [],
    }


def add_route(state, name):
    """保存航线；重复航线返回 False，不重复入库。"""
    if name in state["routes"]:
        return False
    state["routes"].append(name)
    return True


def deploy_sail(state, name):
    """展开帆面；帆面已满（达到容量）时拒绝展开，返回 False。"""
    deployed = [s for s in state["sails"] if s["deployed"]]
    if len(deployed) >= SAIL_CAPACITY:
        return False
    state["sails"].append({"name": name, "deployed": True})
    return True


def first_route(state):
    """取首条航线；空航线返回 None（不返回空文本）。"""
    if not state["routes"]:
        return None
    return state["routes"][0]


def pass_leg(state):
    """通过航段：先到航段先通过（FIFO）；空队列返回 None。"""
    if not state["legs"]:
        return None
    return state["legs"].pop(0)


def sail(state, leg, cost=LEG_ENERGY_COST):
    """航行一个航段。

    - 暂停中拒绝航行，返回 False；
    - 光能不足时回滚：状态完全不变，返回 False；
    - 成功则扣能、移出航段并记日志，返回 True。
    """
    if state["paused"]:
        return False
    if state["energy"] < cost:
        return False
    snapshot = copy.deepcopy(state)
    try:
        state["energy"] -= cost
        if leg in state["legs"]:
            state["legs"].remove(leg)
        state["log"].append(leg)
    except Exception:
        state.clear()
        state.update(snapshot)
        return False
    return True


def view_routes(state):
    """查看航线：只读，返回副本，绝不删除或改动已存航线。"""
    return list(state["routes"])


def add_light(state, *amounts):
    """采集光能：逐段全额累加，不少算。"""
    for amount in amounts:
        state["energy"] += amount
    return state["energy"]


def record_voyage(state, voyage_id, legs=1):
    """登记一次航行；同一 voyage_id 重复登记不重复累计。"""
    if voyage_id in state["voyages"]:
        return False
    state["voyages"][voyage_id] = legs
    state["voyage_count"] += 1
    return True


def reset(state):
    """重置航程：清空全部字段（原地清空，保留同一 state 对象）。"""
    state.clear()
    state.update(new_game())
    return state


def save(state, slot=None):
    """序列化存档；slot 缺省时按 next_id 顺序编号，不跳号。"""
    if slot is None:
        slot = state["next_id"]
        state["next_id"] += 1
    return json.dumps({"slot": slot, "state": state}, ensure_ascii=False, sort_keys=True)


def load(payload):
    """读档：save 的逆操作，保证序列化往返一致。"""
    data = json.loads(payload)
    state = new_game()
    state.update(data["state"])
    return data["slot"], state
