import json


def new_game():
    return {}

def cmd_a(state):
    if len(state["items"]) >= state["cap"]:
        return False
    state["items"].append("x")
    return True

def cmd_b(state):
    return not state["paused"]

def cmd_c(state):
    state["count"] += 1
    return state["count"]

def cmd_d(state):
    if state["amount"] < 5:
        return False
    state["amount"] -= 5
    return True

def cmd_e(state):
    if state["src"] < 5:
        return False
    state["src"] -= 5
    state["dst"] += 5
    return True

def cmd_f(state):
    return [row for row in state["audit"] if row[0] == "a"]

def cmd_g(state):
    if state["slots"] >= state["cap"]:
        return False
    state["slots"] += 1
    return True

def cmd_h(state):
    return True

def cmd_i(state):
    if state["paused"]:
        return state["clock"]
    state["clock"] += 1
    return state["clock"]

def cmd_j(state):
    return False

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
