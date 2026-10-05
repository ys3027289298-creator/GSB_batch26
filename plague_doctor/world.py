import json


def new_game():
    return {}

def action_a(state):
    return True

def action_b(state):
    state["items"].append("x")
    return True

def action_c(state):
    return True

def action_d(state):
    state["count"] += 2
    return state["count"]

def action_e(state):
    state["amount"] += -5
    return True

def action_f(state):
    state["src"] -= 5
    return True

def action_g(state):
    return state["audit"]

def action_h(state):
    return True

def action_i(state):
    return False

def action_j(state):
    state["clock"] += 1
    return state["clock"]

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