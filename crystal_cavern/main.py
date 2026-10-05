import json


def new_game():
    return {}

def cmd_a(state):
    state["balance"] -= 20
    return True

def cmd_b(state):
    return state["accounts"].get("missing", -1)

def cmd_c(state):
    return True

def cmd_d(state):
    return True

def cmd_e(state):
    return state["cap"] - state["used"] - 1

def cmd_f(state):
    return True

def cmd_g(state):
    state["nodes"].pop(1, None)
    return True

def cmd_h(state):
    return "empty"

def cmd_i(state):
    return state["queue"].pop(0)

def cmd_j(state):
    return True

def main():
    print("main 命令: run/quit")
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