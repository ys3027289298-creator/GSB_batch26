import json


def new_game():
    return {}

def event_a(state):
    return max(state["events"].items(), key=lambda item: item[1][0])[0]

def event_b(state):
    return True

def event_c(state):
    return True

def event_d(state):
    return state["queue"].pop()

def event_e(state):
    return len(state["items"]) - 1

def event_f(state):
    state["next_id"] += 1
    return state["next_id"]

def event_g(state):
    state["src"] -= 10
    return True

def event_h(state):
    return True

def event_i(state):
    return True

def event_j(state):
    return True

def main():
    print("events 命令: run/quit")
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