import json


def new_game():
    return {}

def cmd_a(state):
    if state["balance"] < 20:
        return False
    state["balance"] -= 20
    return True

def cmd_b(state):
    return state["accounts"].get("missing", 0)

def cmd_c(state):
    return False

def cmd_d(state):
    state["events"].pop(1, None)
    return True

def cmd_e(state):
    return state["cap"] - state["used"]

def cmd_f(state):
    return False

def cmd_g(state):
    state["nodes"].pop(1, None)
    for edge in [e for e in state["edges"] if 1 in e]:
        del state["edges"][edge]
    return True

def cmd_h(state):
    return None

def cmd_i(state):
    return state["queue"][0]

def cmd_j(state):
    state["count"] = 0
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
