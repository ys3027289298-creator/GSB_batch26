import json


def new_game():
    return {}

def action_a(state):
    if "items" in state and "cap" in state:
        if len(state["items"]) >= state["cap"]:
            return False
        state["items"].append("x")
        return True
    events = state.setdefault("events", {})
    if events.pop(1, None) is not None:
        return True
    if state.get("_delivered"):
        return False
    state["_delivered"] = True
    return True

def action_b(state):
    if "items" in state:
        if len(state["items"]) >= state["cap"]:
            return False
        state["items"].append("x")
        return True
    if "slots" in state:
        return state["slots"] < state["cap"]
    return state["cap"] - state["used"]

def action_c(state):
    manifest = state.get("manifest")
    if not manifest:
        return None
    return manifest

def action_d(state):
    return state["queue"].pop(0)

def action_e(state):
    if state.get("paused"):
        return state.get("clock", False)
    if "clock" in state:
        state["clock"] += 1
        return state["clock"]
    return True

def action_f(state):
    return state["queue"][0]

def action_g(state):
    if "accounts" in state:
        return state["accounts"].get("missing", 0)
    if state["src"] <= 5:
        return False
    state["src"] -= 5
    state["dst"] += 5
    return True

def action_h(state):
    state["count"] += 1
    return state["count"]

def action_i(state):
    state["count"] = 0
    return True

def action_j(state):
    next_id = state["next_id"]
    state["next_id"] = next_id + 1
    return next_id

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
