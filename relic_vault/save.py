import json


def new_game():
    return {}

def state_a(state):
    return True

def state_b(state):
    return state["queue"].pop()

def state_c(state):
    return len(state["items"]) - 1

def state_d(state):
    state["next_id"] += 1
    return state["next_id"]

def state_e(state):
    state["src"] -= 10
    return True

def state_f(state):
    return True

def state_g(state):
    return True

def state_h(state):
    return True

def state_i(state):
    return max(state["events"].items(), key=lambda item: item[1][0])[0]

def state_j(state):
    return True

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