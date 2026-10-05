"""瘟疫医生的世界状态与动作。

状态不变量（任何成功/失败动作后都必须成立）：
1. 容量：len(items) <= cap，0 <= slots <= cap，满员不得收治。
2. 唯一：同一病例 id 在 queue/items/admitted 中至多一份。
3. FIFO：先到的病例（seq 最小）先被查看/处理。
4. 空查询返回 False 或空容器，绝不返回文本字符串。
5. 门锁：paused/locked 为真时不得进入、收治、走钟。
6. 查看只读：查询类动作不修改 audit/queue/items。
7. 药剂守恒：调剂需余额充足且非负；转移 src->dst 总量不变、两腿都记账。
8. 计数：一次成功收治 count 恰好 +1。
9. 重置：reset 后与 new_game() 的默认状态完全一致。
10. 读档：load 还原存档且 clock 不跳号；暂停态走钟为 no-op。

本模块不持有任何模块级可变状态；每个 new_game() 都构造全新的
嵌套对象，避免多个对局共享 list/dict 而污染全局状态。
"""

import json

DOSE = 5


def new_game():
    return {
        "cases": {},
        "queue": [],
        "items": [],
        "admitted": [],
        "cap": 0,
        "slots": 0,
        "count": 0,
        "amount": 0,
        "src": 0,
        "dst": 0,
        "audit": [],
        "paused": False,
        "locked": False,
        "clock": 0,
        "next_seq": 1,
        "pending": None,
    }


def _door_closed(state):
    return bool(state.get("paused") or state.get("locked"))


def arrive(state, case_id):
    """登记一个到达病例：拒绝重复 id（不变量 2），按序入队（不变量 3）。"""
    if not case_id:
        return False
    cases = state.setdefault("cases", {})
    if case_id in cases:
        return False
    seq = state.get("next_seq", 1)
    cases[case_id] = {"id": case_id, "seq": seq}
    state.setdefault("queue", []).append(case_id)
    state.setdefault("audit", []).append((case_id, seq))
    state["next_seq"] = seq + 1
    return True


def action_a(state):
    """查看 pending（缺省取队首）病例。

    空病例一律返回 False，不返回任何文本（不变量 4）；只读（不变量 6）。
    """
    case_id = state.get("pending")
    if not case_id:
        queue = state.get("queue") or ()
        case_id = queue[0] if queue else None
    if not case_id:
        return False
    case = (state.get("cases") or {}).get(case_id)
    if not case:
        return False
    return dict(case)


def action_b(state):
    """把 pending 病例收入隔离区 items。

    先校验门锁（5）、空病例（4）、重复（2）与容量（1），
    全部通过后才追加；一次收治计数恰好一次（8）。
    """
    if _door_closed(state):
        return False
    case_id = state.get("pending")
    if not case_id:
        return False
    items = state.get("items") or []
    admitted = state.get("admitted") or []
    cap = state.get("cap", 0)
    if case_id in items or case_id in admitted or len(items) >= cap:
        return False
    items.append(case_id)
    admitted.append(case_id)
    state["items"] = items
    state["admitted"] = admitted
    state["slots"] = state.get("slots", 0) + 1
    return action_d(state)


def action_c(state):
    """尝试进入检查门：门锁定/暂停时拒绝（不变量 5）。"""
    if _door_closed(state):
        return False
    return True


def action_d(state):
    """登记一次收治：count 恰好 +1（不变量 8），返回新计数。"""
    state["count"] = state.get("count", 0) + 1
    return state["count"]


def action_e(state, dose=DOSE):
    """从药柜取药：余额不足则拒绝且不改动，库存永不为负（不变量 7）。"""
    amount = state.get("amount", 0)
    if amount < dose:
        return False
    state["amount"] = amount - dose
    return True


def action_f(state, qty=DOSE):
    """把 qty 份药剂从 src 转到 dst：先验余额，src/dst 两腿都记账（7）。"""
    src = state.get("src", 0)
    if src < qty:
        return False
    state["src"] = src - qty
    state["dst"] = state.get("dst", 0) + qty
    return True


def action_g(state):
    """查看最早到达（seq 最小）病人的审计行。

    用新列表返回行副本，绝不在原 audit 上 pop/remove/clear（不变量 3、6）。
    """
    audit = state.get("audit") or []
    if not audit:
        return []
    first_patient = min(audit, key=lambda row: row[1])[0]
    return [tuple(row) for row in audit if row[0] == first_patient]


def action_h(state):
    """以 slots 计数的收治入口：满员/重复/门锁一律拒绝（1、2、5）。"""
    if _door_closed(state):
        return False
    case_id = state.get("pending")
    if not case_id:
        return False
    cap = state.get("cap", 0)
    slots = state.get("slots", 0)
    admitted = state.get("admitted") or []
    items = state.get("items") or []
    if slots >= cap or case_id in admitted or case_id in items:
        return False
    state["slots"] = slots + 1
    admitted.append(case_id)
    items.append(case_id)
    state["admitted"] = admitted
    state["items"] = items
    return action_d(state)


def action_i(state):
    """重置对局：清空传入 state 的全部键并还原默认值（不变量 9）。"""
    state.clear()
    state.update(new_game())
    return True


def action_j(state):
    """走一个钟点：暂停/锁定时为 no-op，返回当前 clock（不变量 5、10）。"""
    if _door_closed(state):
        return state.get("clock", 0)
    state["clock"] = state.get("clock", 0) + 1
    return state["clock"]


def save_game(state):
    """JSON 快照；序列化天然得到深拷贝，不与活动状态共享对象。"""
    return json.dumps(state)


def load_game(state, blob):
    """读档：先清空再整体还原，clock 与存档一致且不自动走钟（不变量 9、10）。"""
    data = json.loads(blob)
    state.clear()
    state.update(new_game())
    state.update(data)
    return state.get("clock", 0)


def process_next(state):
    """按 FIFO 处理队首：收治成功后才出队，失败则保留先到病例（3、6）。"""
    queue = state.get("queue") or []
    if not queue:
        return False
    case_id = queue[0]
    state["pending"] = case_id
    accepted = action_b(state)
    state["pending"] = None
    if accepted:
        queue.pop(0)
        state["queue"] = queue
    return accepted

def main():
    print("world 命令: run/quit")
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
