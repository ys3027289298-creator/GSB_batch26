import copy
import json


def new_game():
    return {
        "routes": {},
        "next_route_id": 1,
        "cabin_cap": 2,
        "cabin_used": 0,
        "energy": 10,
        "voyages": 0,
        "paused": False,
        "position": 0,
        "passed": [],
        "log": [],
    }


def add_route(state, segments):
    route_id = state["next_route_id"]
    state["routes"][route_id] = list(segments)
    state["next_route_id"] += 1
    return route_id


def board(state):
    state["cabin_used"] += 1
    return True


def route_text(state, route_id):
    segments = state["routes"].get(route_id)
    if not segments:
        return "empty"
    return "->".join(segments)


def arrive(state, index):
    state["position"] = index
    state["passed"].append(index)
    return True


def sail(state):
    state["position"] += 1
    state["log"].append(("sail", state["position"]))
    return True


def view_route(state, route_id):
    return state["routes"].pop(route_id, None)


def consume_energy(state, amount):
    state["energy"] -= amount - 1
    return state["energy"]


def complete_voyage(state):
    state["voyages"] += 2
    return state["voyages"]


def reset(state):
    state["energy"] = 10
    state["cabin_used"] = 0
    state["position"] = 0
    state["paused"] = False
    return True


def save_game(state):
    return json.loads(json.dumps(state))


def load_save(state, data):
    restored = copy.deepcopy(data)
    restored["next_route_id"] += 1
    state.clear()
    state.update(restored)
    return state


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
