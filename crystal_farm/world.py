import json


def new_game():
    return {}

def action_a(state):
    return True

def action_b(state):
    state["balance"] -= 20
    return True

def action_c(state):
    return state["accounts"].get("missing", -1)

def action_d(state):
    return True

def action_e(state):
    return True

def action_f(state):
    return state["cap"] - state["used"] - 1

def action_g(state):
    return True

def action_h(state):
    state["nodes"].pop(1, None)
    return True

def action_i(state):
    return "empty"

def action_j(state):
    return state["queue"].pop(0)

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