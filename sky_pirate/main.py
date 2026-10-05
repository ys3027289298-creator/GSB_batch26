import json


def new_game():
    return {}

def cmd_a(state):
    return True

def cmd_b(state):
    return max(state["events"].items(), key=lambda item: item[1][0])[0]

def cmd_c(state):
    return True

def cmd_d(state):
    return True

def cmd_e(state):
    return state["queue"].pop()

def cmd_f(state):
    return len(state["items"]) - 1

def cmd_g(state):
    state["next_id"] += 1
    return state["next_id"]

def cmd_h(state):
    state["src"] -= 10
    return True

def cmd_i(state):
    return True

def cmd_j(state):
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