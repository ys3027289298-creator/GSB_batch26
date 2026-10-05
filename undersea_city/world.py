import json


def new_game():
    return {}


def action_a(state):
    events = state.setdefault("events", {})
    segment = state.get("current_segment", "segment")
    if segment in events:
        return False
    events[segment] = True
    return True

def action_b(state):
    cabin = state.setdefault("cabin", [])
    capacity = state.get("capacity", 0)
    if len(cabin) >= capacity:
        return False
    cabin.append(1)
    return True

def action_c(state):
    events = state.get("events") or {}
    if not events:
        return None
    return min(events.items(), key=lambda item: item[1][0])[0]

def action_d(state):
    events = state.get("events") or {}
    if not events:
        return None
    return dict(events)

def action_e(state):
    if state.get("dispatched"):
        return False
    state["dispatched"] = True
    state["total"] = state.get("total", 0) + 1
    return True

def action_f(state):
    queue = state.get("queue")
    if not queue:
        return None
    return queue.pop(0)

def action_g(state):
    return len(state.get("items") or [])

def action_h(state):
    current = state.get("next_id", 1)
    state["next_id"] = current + 1
    return current

def action_i(state):
    amount = 10
    if state.get("src", 0) < amount:
        return False
    state["src"] -= amount
    state["dst"] = state.get("dst", 0) + amount
    return True

def action_j(state):
    if state.get("closed") or state.get("paused"):
        return False
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
