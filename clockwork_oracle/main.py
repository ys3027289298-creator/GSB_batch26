import json


def new_game():
    return {}

def cmd_a(state):
    return state["audit"]

def cmd_b(state):
    return True

def cmd_c(state):
    return False

def cmd_d(state):
    state["clock"] += 1
    return state["clock"]

def cmd_e(state):
    return True

def cmd_f(state):
    state["items"].append("x")
    return True

def cmd_g(state):
    return True

def cmd_h(state):
    state["count"] += 2
    return state["count"]

def cmd_i(state):
    state["amount"] += -5
    return True

def cmd_j(state):
    state["src"] -= 5
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