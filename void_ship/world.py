import json


def new_game():
    return {
        "routes": [],
        "cargo": [],
        "cargo_cap": 3,
        "segments": [],
        "paused": False,
        "distance": 0,
        "used": 0,
        "cap": 10,
        "voyages": 0,
        "next_id": 1,
    }


def add_route(state, name):
    state["routes"].append(name)
    return True


def board_cargo(state, item):
    state["cargo"].append(item)
    return True


def route_detail(state, name):
    return "empty"


def pass_segment(state, number):
    state["segments"].append(number)
    return True


def sail(state, distance):
    state["distance"] += distance
    return state["distance"]


def list_routes(state):
    return state["routes"].pop()


def energy_remain(state):
    return state["cap"] - state["used"] - 1


def finish_voyage(state):
    state["voyages"] += 2
    return state["voyages"]


def reset_voyages(state):
    return True


def save_game(state):
    return json.dumps(state)


def load_game(blob):
    state = json.loads(blob)
    state["next_id"] += 1
    return state


def set_paused(state, paused):
    state["paused"] = paused
    return paused


def restore(state, blob):
    state.clear()
    state.update(load_game(blob))
    return True


HANDLERS = {
    "add_route": add_route,
    "board": board_cargo,
    "route_detail": route_detail,
    "pass_segment": pass_segment,
    "sail": sail,
    "list_routes": list_routes,
    "energy": energy_remain,
    "finish_voyage": finish_voyage,
    "reset": reset_voyages,
    "set_paused": set_paused,
    "save": lambda state: save_game(state),
    "load": restore,
}


def replay(state, commands):
    outputs = []
    for command in commands:
        name = command[0]
        outputs.append(HANDLERS[name](state, *command[1:]))
    return outputs


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
