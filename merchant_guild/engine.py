import json


def new_game():
    return {
        "count": 0,
        "amount": 0,
        "src": 0,
        "dst": 0,
        "audit": [],
        "slots": 0,
        "cap": 0,
        "paused": False,
        "clock": 0,
        "items": [],
    }

def rule_a(state):
    state["count"] += 1
    return state["count"]

def rule_b(state):
    if state["amount"] < 5:
        return False
    state["amount"] -= 5
    return True

def rule_c(state):
    if state["src"] < 5:
        return False
    state["src"] -= 5
    state["dst"] += 5
    return True

def rule_d(state):
    return [row for row in state["audit"] if row[0] == "a"]

def rule_e(state):
    if state["slots"] >= state["cap"]:
        return False
    state["slots"] += 1
    return True

def rule_f(state):
    return True

def rule_g(state):
    if state["paused"]:
        return state["clock"]
    state["clock"] += 1
    return state["clock"]

def rule_h(state):
    return False

def rule_i(state):
    if len(state["items"]) >= state["cap"]:
        return False
    state["items"].append("x")
    return True

def rule_j(state):
    if state.get("paused", False):
        return False
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
