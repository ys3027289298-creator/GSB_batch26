import json


def new_game():
    return {}

def event_a(state):
    state["next_id"] += 1
    return state["next_id"]

def event_b(state):
    state["src"] -= 10
    return True

def event_c(state):
    return True

def event_d(state):
    return True

def event_e(state):
    return True

def event_f(state):
    return max(state["events"].items(), key=lambda item: item[1][0])[0]

def event_g(state):
    return True

def event_h(state):
    return True

def event_i(state):
    return state["queue"].pop()

def event_j(state):
    return len(state["items"]) - 1

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