import json


RIFT_CAPACITY = 3
REPAIR_REWARD = 10


def new_game():
    return {
        "timelines": {},
        "rift_occupants": [],
        "rift_capacity": RIFT_CAPACITY,
        "events": {},
        "locked": False,
        "coins": 0,
        "repairs": 0,
        "next_event_id": 1,
        "clock": 0,
        "location": "prime",
    }


def add_timeline(state, name):
    if name in state["timelines"]:
        return False
    state["timelines"][name] = []
    return True


def enter_rift(state, traveler):
    if len(state["rift_occupants"]) >= state["rift_capacity"]:
        return False
    state["rift_occupants"].append(traveler)
    return True


def describe_timeline(state, name):
    event_ids = state["timelines"].get(name)
    if not event_ids:
        return None
    return list(event_ids)


def schedule_event(state, timeline, text):
    if timeline not in state["timelines"]:
        return None
    event_id = state["next_event_id"]
    state["events"][event_id] = {
        "arrival": state["clock"],
        "timeline": timeline,
        "text": text,
    }
    state["timelines"][timeline].append(event_id)
    state["clock"] += 1
    state["next_event_id"] += 1
    return event_id


def view_event(state, event_id):
    return state["events"].get(event_id)


def repair_event(state):
    if not state["events"]:
        return None
    event_id = min(
        state["events"],
        key=lambda eid: (state["events"][eid]["arrival"], eid),
    )
    record = state["events"].pop(event_id)
    timeline = record["timeline"]
    if timeline in state["timelines"] and event_id in state["timelines"][timeline]:
        state["timelines"][timeline].remove(event_id)
    state["repairs"] += 1
    state["coins"] += REPAIR_REWARD
    return event_id


def lock(state):
    state["locked"] = True
    return True


def unlock(state):
    state["locked"] = False
    return True


def jump(state, timeline):
    if state["locked"]:
        return False
    if timeline not in state["timelines"]:
        return False
    state["location"] = timeline
    return True


def reset(state):
    fresh = new_game()
    state.clear()
    state.update(fresh)
    return state


def save_game(state, path):
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(state, fh, indent=2, sort_keys=True)
    return True


def load_game(path):
    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    state = new_game()
    state.update(data)
    state["events"] = {
        int(event_id): record for event_id, record in data.get("events", {}).items()
    }
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
