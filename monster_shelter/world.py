import json


def new_game():
    return {
        "src": 0,
        "dst": 0,
        "audit": [],
        "slots": 0,
        "cap": 0,
        "paused": False,
        "clock": 0,
        "items": [],
        "pending": [],
        "count": 0,
        "amount": 0,
    }

def action_a(state):
    if state["src"] < 5:
        return False
    state["src"] -= 5
    state["dst"] += 5
    return True

def action_b(state):
    return [row for row in state["audit"] if row[0] == "a"]

def action_c(state):
    return state["slots"] < state["cap"]

def action_d(state):
    return state.get("slots", 0) == 0

def action_e(state):
    if state.get("paused"):
        return state["clock"]
    state["clock"] += 1
    return state["clock"]

def action_f(state):
    return bool(state.get("pending"))

def action_g(state):
    if "x" in state["items"] or len(state["items"]) >= state["cap"]:
        return False
    state["items"].append("x")
    return True

def action_h(state):
    return not state.get("paused", False)

def action_i(state):
    state["count"] += 1
    return state["count"]

def action_j(state):
    if state["amount"] < 5:
        return False
    state["amount"] -= 5
    return True

def main():
    print("world 命令: run/quit")
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
