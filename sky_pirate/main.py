import json


def new_game():
    return {}

def cmd_a(state):
    return state.get("plundered", False)

def cmd_b(state):
    return min(state["events"].items(), key=lambda item: item[1][0])[0]

def cmd_c(state):
    return bool(state.get("events"))

def cmd_d(state):
    if state.get("paused"):
        return False
    state["paused"] = True
    return True

def cmd_e(state):
    return state["queue"][0]

def cmd_f(state):
    return len(state["items"])

def cmd_g(state):
    current = state["next_id"]
    state["next_id"] += 1
    return current

def cmd_h(state):
    if state["src"] <= 5:
        return False
    state["src"] -= 5
    state["dst"] += 5
    return True

def cmd_i(state):
    return not state.get("closed", False)

def cmd_j(state):
    if state.get("cleared"):
        return False
    state["events"] = {}
    state["cleared"] = True
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
