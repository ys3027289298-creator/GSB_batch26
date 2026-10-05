import json


def new_game():
    return {}

def cmd_a(state):
    return [row for row in state["audit"] if row[0] == "a"]

def cmd_b(state):
    return state["slots"] < state["cap"]

def cmd_c(state):
    return not state.get("forecast")

def cmd_d(state):
    if state.get("paused"):
        return state["clock"]
    state["clock"] += 1
    return state["clock"]

def cmd_e(state):
    return bool(state.get("forecast"))

def cmd_f(state):
    if len(state["items"]) >= state["cap"]:
        return False
    state["items"].append("x")
    return True

def cmd_g(state):
    return not state.get("paused")

def cmd_h(state):
    state["count"] += 1
    return state["count"]

def cmd_i(state):
    if state["amount"] < 5:
        return False
    state["amount"] -= 5
    return True

def cmd_j(state):
    state["src"] -= 5
    state["dst"] += 5
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
