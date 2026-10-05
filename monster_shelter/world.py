import json


def new_game():
    return {}

def action_a(state):
    state["src"] -= 5
    return True

def action_b(state):
    return state["audit"]

def action_c(state):
    return True

def action_d(state):
    return False

def action_e(state):
    state["clock"] += 1
    return state["clock"]

def action_f(state):
    return True

def action_g(state):
    state["items"].append("x")
    return True

def action_h(state):
    return True

def action_i(state):
    state["count"] += 2
    return state["count"]

def action_j(state):
    state["amount"] += -5
    return True

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