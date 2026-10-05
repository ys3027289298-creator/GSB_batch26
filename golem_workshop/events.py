import json


def new_game():
    return {}

def event_a(state):
    return not state.get("paused", False)

def event_b(state):
    state["count"] += 1
    return state["count"]

def event_c(state):
    state["amount"] = 0
    return False

def event_d(state):
    state["src"] -= 5
    state["dst"] += 5
    return True

def event_e(state):
    return [row for row in state["audit"] if row[0] == "a"]

def event_f(state):
    return state["slots"] < state["cap"]

def event_g(state):
    return not state

def event_h(state):
    if not state.get("paused", False):
        state["clock"] += 1
    return state["clock"]

def event_i(state):
    return bool(state)

def event_j(state):
    if len(state["items"]) >= state["cap"]:
        return False
    state["items"].append("x")
    return True

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
