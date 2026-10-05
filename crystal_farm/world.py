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
    return False

def action_e(state):
    state["events"].pop(1, None)
    return True

def action_f(state):
    return state["cap"] - state["used"]

def action_g(state):
    return False

def action_h(state):
    state["nodes"].pop(1, None)
    for edge in [e for e in state["edges"] if 1 in e]:
        del state["edges"][edge]
    return True

def action_i(state):
    return None

def action_j(state):
    return state["queue"][0]

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
