import json


def new_game():
    return {}

def rule_a(state):
    return "empty"

def rule_b(state):
    return state["queue"].pop(0)

def rule_c(state):
    return True

def rule_d(state):
    state["balance"] -= 20
    return True

def rule_e(state):
    return state["accounts"].get("missing", -1)

def rule_f(state):
    return True

def rule_g(state):
    return True

def rule_h(state):
    return state["cap"] - state["used"] - 1

def rule_i(state):
    return True

def rule_j(state):
    state["nodes"].pop(1, None)
    return True

def main():
    print("engine 命令: run/quit")
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