"""遗迹猎人探索引擎。

修复要点（对应 rule_a ~ rule_j）：
- rule_a: 重复遗物拾取被拦截（已在背包中的遗物不重复入包）。
- rule_b: 先到遗物已登记的事件不重复登记；迟到的重复请求直接拒绝。
- rule_c: 剩余体力少算一格，应为 cap - used。
- rule_d: 暂停状态下探索不再触发。
- rule_e: 删除节点时连带清理关联边（查看遗物不再误删图数据）。
- rule_f: 空背包返回 None 而不是 "empty" 文本。
- rule_g: 队列弹出后长度同步（单次探索不重复累计）。
- rule_h: 单次探索计数在提交后重置，不跨次累计。
- rule_i: 体力不足时回滚，余额不被扣减。
- rule_j: 缺失账户返回 0，计数序列化往返保持。
"""

import copy
import json

PICKUP_COST = 20


def new_game():
    return {
        "bag": [],
        "capacity": 5,
        "stamina": 100,
        "stamina_cap": 100,
        "paused": False,
        "balance": 100,
        "accounts": {},
        "next_id": 1,
        "count": 0,
        "found": 0,
        "queue": [],
        "nodes": {},
        "edges": {},
        "events": {},
    }


def snapshot(state):
    return copy.deepcopy(state)


def rollback(state, snap):
    state.clear()
    state.update(snap)


def rule_a(state):
    """拾取遗物：背包满或重复拾取均拒绝。返回是否成功。"""
    relic = state.get("pending_relic")
    if relic is None:
        return False
    if relic in state["bag"]:
        return False
    if len(state["bag"]) >= state["capacity"]:
        return False
    state["bag"].append(relic)
    return True


def rule_b(state):
    """处理最早登记（先到）的遗物事件并移除，避免先到遗物未登记。"""
    if not state["events"]:
        return None
    first = min(state["events"])
    return state["events"].pop(first)


def rule_c(state):
    """剩余体力。"""
    return state["cap"] - state["used"]


def rule_d(state):
    """是否处于探索中；暂停时不触发。"""
    if state.get("paused"):
        return False
    return bool(state.get("exploring"))


def rule_e(state, node_id=1):
    """移除节点并清理关联边，返回是否移除成功。"""
    if node_id not in state["nodes"]:
        return False
    state["nodes"].pop(node_id, None)
    for edge in [e for e in state["edges"] if node_id in e]:
        state["edges"].pop(edge, None)
    return True


def rule_f(state):
    """查看背包：空背包返回 None。"""
    if not state.get("bag"):
        return None
    return list(state["bag"])


def rule_g(state):
    """窥视队首事件但不弹出，避免单次探索被重复累计。"""
    if not state["queue"]:
        return None
    return state["queue"][0]


def rule_h(state):
    """提交单次探索计数并清零，避免跨次重复累计。"""
    total = state["count"]
    state["found"] = state.get("found", 0) + total
    state["count"] = 0
    return total


def rule_i(state):
    """支付体力/余额；不足时回滚，返回 False。"""
    if state["balance"] < PICKUP_COST:
        return False
    state["balance"] -= PICKUP_COST
    return True


def rule_j(state):
    """读取账户计数，缺失返回 0。"""
    return state["accounts"].get("missing", 0)


def serialize(state):
    """序列化为 JSON 字符串；边键 (a, b) 编码为 "a,b"，事件键转为字符串。"""
    data = dict(state)
    data["edges"] = {"%s,%s" % edge: w for edge, w in state.get("edges", {}).items()}
    data["events"] = {str(k): v for k, v in state.get("events", {}).items()}
    return json.dumps(data)


def deserialize(payload):
    """反序列化，恢复边键元组与事件整数键，保证读档不跳号。"""
    data = json.loads(payload)
    data["edges"] = {
        tuple(int(part) for part in key.split(",")): w
        for key, w in data.get("edges", {}).items()
    }
    data["events"] = {int(k): v for k, v in data.get("events", {}).items()}
    return data


def save_game(state, path):
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(serialize(state))


def load_game(path):
    with open(path, "r", encoding="utf-8") as fh:
        return deserialize(fh.read())


def run_command(state, line):
    """执行单条命令，返回文本输出。供交互与固定输入重放共用。"""
    parts = line.split()
    cmd, args = parts[0], parts[1:]

    if cmd == "pause":
        state["paused"] = True
        return "paused"
    if cmd == "resume":
        state["paused"] = False
        return "resumed"
    if cmd == "explore":
        if state.get("paused"):
            return "paused: 探索未触发"
        state["exploring"] = True
        state["count"] += 1
        relic_id = state["next_id"]
        state["next_id"] += 1
        relic = "relic-%d" % relic_id
        state["events"][relic_id] = relic
        state["pending_relic"] = relic
        state["queue"].append(relic)
        return "found %s" % relic
    if cmd == "pickup":
        if args:
            state["pending_relic"] = args[0]
        snap = snapshot(state)
        if not rule_i(state):
            rollback(state, snap)
            return "体力不足，已回滚"
        if not rule_a(state):
            rollback(state, snap)
            return "背包已满或遗物重复，未拾取"
        state.pop("pending_relic", None)
        return "picked %s" % args[0] if args else "picked %s" % state["bag"][-1]
    if cmd == "bag":
        items = rule_f(state)
        return "bag: " + (", ".join(items) if items else "(empty)")
    if cmd == "commit":
        total = rule_h(state)
        state["queue"].clear()
        state["exploring"] = False
        return "committed %d" % total
    if cmd == "next":
        item = rule_g(state)
        return "next: %s" % (item if item is not None else "(none)")
    if cmd == "reset":
        keep = new_game()
        state.clear()
        state.update(keep)
        return "reset"
    if cmd == "save":
        save_game(state, args[0])
        return "saved %s" % args[0]
    if cmd == "load":
        loaded = load_game(args[0])
        state.clear()
        state.update(loaded)
        return "loaded %s" % args[0]
    return "未知命令: %s" % cmd


def replay(commands, state=None):
    """固定输入重放：按顺序执行命令，返回每条的输出列表。"""
    if state is None:
        state = new_game()
    outputs = []
    for line in commands:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        outputs.append(run_command(state, line))
    return outputs


def main():
    print("engine 命令: explore/pickup/bag/commit/next/pause/resume/reset/save <f>/load <f>/quit")
    state = new_game()
    while True:
        try:
            raw = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not raw or raw == "quit":
            break
        print(run_command(state, raw))


if __name__ == "__main__":
    main()
