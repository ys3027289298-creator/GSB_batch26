import json


def new_game():
    return {}

def state_a(state):
    return state["queue"].pop(0)

def state_b(state):
    return True

def state_c(state):
    state["balance"] -= 20
    return True

def state_d(state):
    return state["accounts"].get("missing", -1)

def state_e(state):
    return True

def state_f(state):
    return True

def state_g(state):
    return state["cap"] - state["used"] - 1

def state_h(state):
    return True

def state_i(state):
    state["nodes"].pop(1, None)
    return True

def state_j(state):
    return "empty"

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