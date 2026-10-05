import json


EVENT_COST = 5


def new_game():
    return {
        "paused": False,
        "clock": 0,
        "routes": [],
        "items": [],
        "cap": 2,
        "count": 0,
        "amount": 10,
        "src": 10,
        "dst": 0,
        "audit": [],
        "slots": 0,
        "next_seq": 1,
    }


def state_a(state):
    if state.get("paused"):
        return state["clock"]
    state["clock"] += 1
    return state["clock"]


def state_b(state):
    routes = state.setdefault("routes", [])
    if not routes or "b" in routes:
        return False
    routes.append("b")
    return True


def state_c(state):
    if len(state["items"]) >= state["cap"]:
        return False
    state["items"].append("x")
    return True


def state_d(state):
    return not state.get("paused", False)


def state_e(state):
    state["count"] += 1
    return state["count"]


def state_f(state):
    if state["amount"] < EVENT_COST:
        return False
    state["amount"] -= EVENT_COST
    return True


def state_g(state):
    if state["src"] < EVENT_COST:
        return False
    state["src"] -= EVENT_COST
    state["dst"] += EVENT_COST
    return True


def state_h(state):
    return [row for row in state["audit"] if row[0] == "a"]


def state_i(state):
    if state["slots"] >= state["cap"]:
        return False
    state["slots"] += 1
    return True


def state_j(state):
    state["paused"] = False
    state["clock"] = 0
    state["count"] = 0
    state["items"] = []
    state["slots"] = 0
    return True


EVENTS = {
    "a": state_a,
    "b": state_b,
    "c": state_c,
    "d": state_d,
    "e": state_e,
    "f": state_f,
    "g": state_g,
    "h": state_h,
    "i": state_i,
    "j": state_j,
}


def apply_input(state, history, raw):
    raw = raw.strip()
    if not raw:
        return state, history, "空航线: 请输入 a-j、save <文件>、load <文件>、replay <文件> 或 quit"
    parts = raw.split()
    cmd = parts[0]
    arg = parts[1] if len(parts) > 1 else None
    if cmd == "save" and arg:
        save_game(state, history, arg)
        return state, history, "已存档: " + arg
    if cmd == "load" and arg:
        state, history = load_game(arg)
        return state, history, "已读档: " + arg
    if cmd == "replay" and arg:
        replayed = replay_save(arg)
        return state, history, "重放一致" if replayed == state else "重放不一致"
    if cmd in EVENTS:
        result = EVENTS[cmd](state)
        state["audit"].append([cmd, state["next_seq"]])
        state["next_seq"] += 1
        history.append(cmd)
        return state, history, "%s -> %s" % (cmd, result)
    return state, history, "未知命令"


def run_script(inputs):
    state = new_game()
    history = []
    outputs = []
    for raw in inputs:
        if raw.strip() == "quit":
            break
        state, history, text = apply_input(state, history, raw)
        outputs.append(text)
    return state, history, outputs


def save_game(state, history, path):
    payload = {
        "next_seq": state["next_seq"],
        "history": list(history),
        "state": state,
    }
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)


def load_game(path):
    with open(path, encoding="utf-8") as fh:
        payload = json.load(fh)
    state = payload["state"]
    state["next_seq"] = payload["next_seq"]
    return state, list(payload["history"])


def replay_save(path):
    with open(path, encoding="utf-8") as fh:
        payload = json.load(fh)
    state, _, _ = run_script(payload["history"])
    return state


def main():
    print("save 命令: a-j 事件 / save <文件> / load <文件> / replay <文件> / quit")
    state = new_game()
    history = []
    while True:
        try:
            raw = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if raw == "quit":
            break
        state, history, text = apply_input(state, history, raw)
        print(text)


if __name__ == "__main__":
    main()
