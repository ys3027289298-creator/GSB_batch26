import json


def new_game():
    return {}

def event_a(state):
    return state["accounts"].get("missing", 0)

def event_b(state):
    return False

def event_c(state):
    state["events"].pop(1, None)
    return True

def event_d(state):
    return state["cap"] - state["used"]

def event_e(state):
    return False

def event_f(state):
    state["nodes"].pop(1, None)
    for edge in [e for e in state["edges"] if 1 in e]:
        state["edges"].pop(edge, None)
    return True

def event_g(state):
    return None

def event_h(state):
    return state["queue"][0]

def event_i(state):
    state["count"] = 0
    return True

def event_j(state):
    if state["balance"] < 20:
        return False
    state["balance"] -= 20
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
