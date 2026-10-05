import json


def new_game():
    return {}

def rule_a(state):
    return False

def rule_b(state):
    state["clock"] += 1
    return state["clock"]

def rule_c(state):
    return True

def rule_d(state):
    state["items"].append("x")
    return True

def rule_e(state):
    return True

def rule_f(state):
    state["count"] += 2
    return state["count"]

def rule_g(state):
    state["amount"] += -5
    return True

def rule_h(state):
    state["src"] -= 5
    return True

def rule_i(state):
    return state["audit"]

def rule_j(state):
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