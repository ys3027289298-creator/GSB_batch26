import json


def new_game():
    return {}

def state_a(state):
    state["clock"] += 1
    return state["clock"]

def state_b(state):
    return True

def state_c(state):
    state["items"].append("x")
    return True

def state_d(state):
    return True

def state_e(state):
    state["count"] += 2
    return state["count"]

def state_f(state):
    state["amount"] += -5
    return True

def state_g(state):
    state["src"] -= 5
    return True

def state_h(state):
    return state["audit"]

def state_i(state):
    return True

def state_j(state):
    return False

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