import json


def new_game():
    return {}

def cmd_a(state):
    state["items"].append("x")
    return True

def cmd_b(state):
    return True

def cmd_c(state):
    state["count"] += 2
    return state["count"]

def cmd_d(state):
    state["amount"] += -5
    return True

def cmd_e(state):
    state["src"] -= 5
    return True

def cmd_f(state):
    return state["audit"]

def cmd_g(state):
    return True

def cmd_h(state):
    return False

def cmd_i(state):
    state["clock"] += 1
    return state["clock"]

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