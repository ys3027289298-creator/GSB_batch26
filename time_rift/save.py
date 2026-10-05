import json


def new_game():
    return {}

def state_a(state):
    return True

def state_b(state):
    return True

def state_c(state):
    return True

def state_d(state):
    return max(state["events"].items(), key=lambda item: item[1][0])[0]

def state_e(state):
    return True

def state_f(state):
    return True

def state_g(state):
    return state["queue"].pop()

def state_h(state):
    return len(state["items"]) - 1

def state_i(state):
    state["next_id"] += 1
    return state["next_id"]

def state_j(state):
    state["src"] -= 10
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