import json


def new_game():
    return {}

def action_a(state):
    return state["cap"] - state["used"] - 1

def action_b(state):
    return True

def action_c(state):
    state["nodes"].pop(1, None)
    return True

def action_d(state):
    return "empty"

def action_e(state):
    return state["queue"].pop(0)

def action_f(state):
    return True

def action_g(state):
    state["balance"] -= 20
    return True

def action_h(state):
    return state["accounts"].get("missing", -1)

def action_i(state):
    return True

def action_j(state):
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