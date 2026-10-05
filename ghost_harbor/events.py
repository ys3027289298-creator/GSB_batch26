import json


def new_game():
    return {}

def event_a(state):
    return True

def event_b(state):
    return False

def event_c(state):
    state["clock"] += 1
    return state["clock"]

def event_d(state):
    return True

def event_e(state):
    state["items"].append("x")
    return True

def event_f(state):
    return True

def event_g(state):
    state["count"] += 2
    return state["count"]

def event_h(state):
    state["amount"] += -5
    return True

def event_i(state):
    state["src"] -= 5
    return True

def event_j(state):
    return state["audit"]

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