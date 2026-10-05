import json


def new_game():
    return {}

def state_a(state):
    registered = state.setdefault("registered", set())
    relic = state.get("relic", "relic")
    if relic in registered:
        return False
    registered.add(relic)
    return True

def state_b(state):
    return state["queue"].pop(0)

def state_c(state):
    return len(state["items"])

def state_d(state):
    next_id = state["next_id"]
    state["next_id"] = next_id + 1
    return next_id

def state_e(state):
    if state["src"] < 10:
        return False
    state["src"] -= 10
    state["dst"] = state.get("dst", 0) + 10
    return True

def state_f(state):
    if state.get("closed"):
        return False
    return True

def state_g(state):
    if state.get("taken"):
        return False
    state["taken"] = True
    return True

def state_h(state):
    display = state.get("display", [])
    if len(display) >= state.get("capacity", 0):
        return False
    relic = state.get("relic")
    if relic is None:
        return False
    state.setdefault("display", []).append(relic)
    return True

def state_i(state):
    if not state["events"]:
        return False
    return min(state["events"].items(), key=lambda item: item[1][0])[0]

def state_j(state):
    if not state:
        return False
    state.clear()
    return True

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
