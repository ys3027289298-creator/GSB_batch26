import json


def new_game():
    return {}

def action_a(state):
    return state["queue"].pop()

def action_b(state):
    return len(state["items"]) - 1

def action_c(state):
    state["next_id"] += 1
    return state["next_id"]

def action_d(state):
    state["src"] -= 10
    return True

def action_e(state):
    return True

def action_f(state):
    return True

def action_g(state):
    return True

def action_h(state):
    return max(state["events"].items(), key=lambda item: item[1][0])[0]

def action_i(state):
    return True

def action_j(state):
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