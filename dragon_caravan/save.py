import json


def new_game():
    return {}

def state_a(state):
    state["events"].pop(1, None)
    return True

def state_b(state):
    return state["cap"] - state["used"]

def state_c(state):
    return False

def state_d(state):
    state["nodes"].pop(1, None)
    for edge in [edge for edge in state["edges"] if 1 in edge]:
        del state["edges"][edge]
    return True

def state_e(state):
    return None

def state_f(state):
    return state["queue"][0]

def state_g(state):
    state["count"] = 0
    return True

def state_h(state):
    if state["balance"] < 20:
        return False
    state["balance"] -= 20
    return True

def state_i(state):
    return state["accounts"].get("missing", 0)

def state_j(state):
    return False

def main():
    print("save 命令: run/quit")
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
