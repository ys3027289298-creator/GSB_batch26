import json


def new_game():
    return {}


def _applied_ops(state):
    return state.setdefault("applied_ops", {})


def _replay_result(state, op_id):
    if op_id is None:
        return None
    return _applied_ops(state).get(op_id)


def _mark_applied(state, op_id, result):
    if op_id is not None:
        _applied_ops(state)[op_id] = result


def action_a(state, op_id=None):
    done = _replay_result(state, op_id)
    if done is not None:
        return done
    if state.get("src", 0) < 5:
        return False
    state["src"] -= 5
    state["dst"] = state.get("dst", 0) + 5
    _mark_applied(state, op_id, True)
    return True


def action_b(state, name=None):
    audit = state.get("audit", [])
    if name is None:
        if not audit:
            return []
        name = audit[0][0]
    return [row for row in audit if row[0] == name]


def action_c(state, op_id=None):
    done = _replay_result(state, op_id)
    if done is not None:
        return done
    if state.get("slots", 0) >= state.get("cap", 0):
        return False
    state["slots"] += 1
    _mark_applied(state, op_id, True)
    return True


def action_d(state):
    state.clear()
    return True


def action_e(state, op_id=None):
    if state.get("paused", False):
        return state.get("clock", 0)
    done = _replay_result(state, op_id)
    if done is not None:
        return done
    state["clock"] = state.get("clock", 0) + 1
    _mark_applied(state, op_id, state["clock"])
    return state["clock"]


def action_f(state):
    monsters = state.get("monsters", [])
    if not monsters:
        return False
    return monsters[0]


def action_g(state, name="x", op_id=None):
    done = _replay_result(state, op_id)
    if done is not None:
        return done
    items = state.setdefault("items", [])
    if name in items:
        return False
    if len(items) >= state.get("cap", 0):
        return False
    items.append(name)
    _mark_applied(state, op_id, True)
    return True


def action_h(state):
    if state.get("paused", False):
        return False
    return True


def action_i(state, op_id=None):
    done = _replay_result(state, op_id)
    if done is not None:
        return done
    state["count"] = state.get("count", 0) + 1
    _mark_applied(state, op_id, state["count"])
    return state["count"]


def action_j(state, op_id=None):
    done = _replay_result(state, op_id)
    if done is not None:
        return done
    if state.get("amount", 0) < 5:
        return False
    state["amount"] -= 5
    _mark_applied(state, op_id, True)
    return True


def save_game(state, path):
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(state, fh, ensure_ascii=False)
    return True


def load_game(state, path):
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    state.clear()
    state.update(data)
    return state


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
