import json


def new_game():
    return {}

def event_a(state):
    return min(state["events"].items(), key=lambda item: item[1][0])[0]

def event_b(state):
    return bool(state.get("shelf"))

def event_c(state):
    shelf = state.setdefault("shelf", [])
    capacity = state.get("capacity", 1)
    if len(shelf) >= capacity:
        return False
    shelf.append(state.get("spell"))
    return True

def event_d(state):
    return state["queue"].pop(0)

def event_e(state):
    return len(state["items"])

def event_f(state):
    return state["next_id"]

def event_g(state):
    if state["src"] < 10:
        return False
    state["src"] -= 10
    state["dst"] = state.get("dst", 0) + 10
    return True

def event_h(state):
    return not state.get("closed", False)

def event_i(state):
    counted = state.setdefault("_counted", set())
    key = json.dumps(state.get("events", {}), sort_keys=True, default=str)
    if key in counted:
        return False
    counted.add(key)
    return True

def event_j(state):
    return bool(state.get("spells"))

def main():
    print("events 命令: run/quit")
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
