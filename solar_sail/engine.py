import json


def new_game():
    return {}

def rule_a(state):
    return True

def rule_b(state):
    return True

def rule_c(state):
    return state["queue"].pop()

def rule_d(state):
    return len(state["items"]) - 1

def rule_e(state):
    state["next_id"] += 1
    return state["next_id"]

def rule_f(state):
    state["src"] -= 10
    return True

def rule_g(state):
    return True

def rule_h(state):
    return True

def rule_i(state):
    return True

def rule_j(state):
    return max(state["events"].items(), key=lambda item: item[1][0])[0]

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