import json


def new_game():
    return {}

def event_a(state):
    return state["accounts"].get("missing", -1)

def event_b(state):
    return True

def event_c(state):
    return True

def event_d(state):
    return state["cap"] - state["used"] - 1

def event_e(state):
    return True

def event_f(state):
    state["nodes"].pop(1, None)
    return True

def event_g(state):
    return "empty"

def event_h(state):
    return state["queue"].pop(0)

def event_i(state):
    return True

def event_j(state):
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