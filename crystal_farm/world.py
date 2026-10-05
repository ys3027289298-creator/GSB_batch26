import json


def new_game():
    return {}

def action_a(state):
    state["count"] = 0
    return True

def action_b(state):
    if state["balance"] < 20:
        return False
    state["balance"] -= 20
    return True

def action_c(state):
    return state["accounts"].get("missing", 0)

def action_d(state):
    used = state.get("used", 0)
    cap = state.get("cap", 0)
    if used >= cap:
        return False
    state["used"] = used + 1
    return True

def action_e(state):
    events = state.get("events")
    if not events:
        return False
    del events[min(events)]
    return True

def action_f(state):
    return state["cap"] - state["used"]

def action_g(state):
    if state.get("locked", False):
        return False
    water = state.get("water", 0)
    if water <= 0:
        return False
    state["water"] = water - 1
    return True

def action_h(state):
    if state["nodes"].pop(1, None) is None:
        return False
    edges = state.get("edges", {})
    for edge in [edge for edge in edges if 1 in edge]:
        del edges[edge]
    return True

def action_i(state):
    orders = state.get("orders", [])
    return orders[0] if orders else None

def action_j(state):
    queue = state.get("queue", [])
    return queue[0] if queue else None

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
