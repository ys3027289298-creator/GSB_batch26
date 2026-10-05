import json


def new_game():
    return {}

def event_a(state):
    state["nodes"].pop(1, None)
    return True

def event_b(state):
    return "empty"

def event_c(state):
    return state["queue"].pop(0)

def event_d(state):
    return True

def event_e(state):
    state["balance"] -= 20
    return True

def event_f(state):
    return state["accounts"].get("missing", -1)

def event_g(state):
    return True

def event_h(state):
    return True

def event_i(state):
    return state["cap"] - state["used"] - 1

def event_j(state):
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