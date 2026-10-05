import json

RIFT_CAPACITY = 3
REPAIR_REWARD = 10


def new_game():
    return {
        "timelines": [],
        "current": None,
        "locked": False,
        "events": {},
        "next_id": 1,
        "clock": 0,
        "coins": 0,
        "repairs": 0,
        "capacity": RIFT_CAPACITY,
    }


def add_timeline(state, name):
    if name in state["timelines"]:
        return False
    state["timelines"].append(name)
    if state["current"] is None:
        state["current"] = name
    return True


def set_lock(state, locked):
    state["locked"] = bool(locked)
    return state["locked"]


def jump(state, name):
    if state["locked"]:
        return False
    if name not in state["timelines"]:
        return False
    state["current"] = name
    return True


def enter_rift(state, desc, tick=None):
    if len(state["events"]) >= state["capacity"]:
        return None
    if tick is None:
        tick = state["clock"]
        state["clock"] += 1
    event_id = state["next_id"]
    state["next_id"] += 1
    state["events"][event_id] = {
        "id": event_id,
        "timeline": state["current"],
        "tick": tick,
        "desc": desc,
    }
    return event_id


def timeline_events(state, name=None):
    if name is None:
        name = state["current"]
    return [event for event in state["events"].values() if event["timeline"] == name]


def current_event(state):
    events = timeline_events(state)
    if not events:
        return None
    return min(events, key=lambda event: (event["tick"], event["id"]))


def view_event(state, event_id):
    return state["events"].get(event_id)


def repair(state):
    if not state["events"]:
        return None
    event_id = min(
        state["events"],
        key=lambda eid: (state["events"][eid]["tick"], eid),
    )
    del state["events"][event_id]
    state["coins"] += REPAIR_REWARD
    state["repairs"] += 1
    return event_id


def reset(state):
    state.update(new_game())
    return state


def save_game(state):
    return json.dumps(state, sort_keys=True)


def load_game(payload):
    data = json.loads(payload)
    state = new_game()
    state.update(data)
    state["events"] = {int(eid): event for eid, event in data["events"].items()}
    state["next_id"] = data["next_id"]
    return state


def replay(state, commands):
    outputs = []
    for command in commands:
        name, args = command[0], command[1:]
        if name == "add_timeline":
            outputs.append(add_timeline(state, *args))
        elif name == "jump":
            outputs.append(jump(state, *args))
        elif name == "lock":
            outputs.append(set_lock(state, True))
        elif name == "unlock":
            outputs.append(set_lock(state, False))
        elif name == "enter":
            outputs.append(enter_rift(state, *args))
        elif name == "current":
            outputs.append(current_event(state))
        elif name == "view":
            outputs.append(view_event(state, *args))
        elif name == "repair":
            outputs.append(repair(state))
        elif name == "reset":
            outputs.append(reset(state))
        else:
            raise ValueError("unknown command: %r" % (name,))
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
