import json


def new_game():
    return {}

def state_a(state):
    registered = state.setdefault("registered", set())
    if "relic" in registered:
        return False
    registered.add("relic")
    return True

def state_b(state):
    return state["queue"].pop(0)

def state_c(state):
    return len(state["items"])

def state_d(state):
    next_id = state["next_id"]
    state["next_id"] += 1
    return next_id

def state_e(state):
    if state["src"] < 10:
        return False
    state["src"] -= 10
    state["dst"] += 10
    return True

def state_f(state):
    return not state["closed"]

def state_g(state):
    if state.get("counted"):
        return False
    state["counted"] = True
    return True

def state_h(state):
    return bool(state.get("items"))

def state_i(state):
    return min(state["events"].items(), key=lambda item: item[1][0] + item[1][1])[0]

def state_j(state):
    return bool(state)

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
