import json

SAIL_CAPACITY = 4
ENERGY_PER_SAIL = 10


def new_game():
    return {
        "routes": {},
        "route_order": [],
        "next_route_id": 1,
        "sail_capacity": SAIL_CAPACITY,
        "sails_deployed": 0,
        "light_energy": 0,
        "paused": False,
        "active_route": None,
        "position": 0,
        "passed_segments": [],
        "completed_voyages": [],
        "voyage_count": 0,
    }


def add_route(state, name, segments):
    """Add a route; duplicates are rejected without touching state or the id counter."""
    segments = list(segments)
    for route_id in state["route_order"]:
        route = state["routes"][route_id]
        if route["name"] == name and route["segments"] == segments:
            return None
    route_id = state["next_route_id"]
    state["routes"][route_id] = {"name": name, "segments": segments}
    state["route_order"].append(route_id)
    state["next_route_id"] += 1
    return route_id


def view_route(state, route_id):
    """Read-only lookup; never mutates state. Returns None for missing/empty routes."""
    route = state["routes"].get(route_id)
    if route is None or not route["segments"]:
        return None
    return {"id": route_id, "name": route["name"], "segments": list(route["segments"])}


def deploy_sail(state):
    """Deploy one sail panel; fails without side effects when the mast is full."""
    if state["sails_deployed"] >= state["sail_capacity"]:
        return False
    state["sails_deployed"] += 1
    return True


def furl_sail(state):
    if state["sails_deployed"] <= 0:
        return False
    state["sails_deployed"] -= 1
    return True


def set_paused(state, paused):
    state["paused"] = bool(paused)
    return state["paused"]


def sail(state):
    """Sail one turn. Paused ships gain nothing; energy counts every deployed sail."""
    if state["paused"]:
        return 0
    gain = state["sails_deployed"] * ENERGY_PER_SAIL
    state["light_energy"] += gain
    return gain


def start_voyage(state, route_id):
    """Begin a voyage on a route; unknown routes leave the state untouched."""
    if route_id not in state["routes"]:
        return False
    state["active_route"] = route_id
    state["position"] = 0
    state["passed_segments"] = []
    return True


def pass_segment(state, index):
    """Mark a segment passed only if every earlier segment was passed first."""
    route = state["routes"].get(state["active_route"])
    if route is None or not 0 <= index < len(route["segments"]):
        return False
    passed = set(state["passed_segments"])
    if any(earlier not in passed for earlier in range(index)):
        return False
    if index not in passed:
        state["passed_segments"].append(index)
    state["position"] = index + 1
    return True


def complete_voyage(state, voyage_id):
    """Count a finished voyage exactly once; repeats are ignored."""
    if voyage_id in state["completed_voyages"]:
        return False
    state["completed_voyages"].append(voyage_id)
    state["voyage_count"] += 1
    return True


def reset_voyage(state):
    """Fully clear voyage progress: position, segments, sails, energy, pause flag."""
    state["active_route"] = None
    state["position"] = 0
    state["passed_segments"] = []
    state["sails_deployed"] = 0
    state["light_energy"] = 0
    state["paused"] = False
    return True


def save_game(state):
    payload = {
        "routes": {
            str(route_id): {
                "name": state["routes"][route_id]["name"],
                "segments": list(state["routes"][route_id]["segments"]),
            }
            for route_id in state["route_order"]
        },
        "route_order": list(state["route_order"]),
        "next_route_id": state["next_route_id"],
        "sail_capacity": state["sail_capacity"],
        "sails_deployed": state["sails_deployed"],
        "light_energy": state["light_energy"],
        "paused": state["paused"],
        "active_route": state["active_route"],
        "position": state["position"],
        "passed_segments": list(state["passed_segments"]),
        "completed_voyages": list(state["completed_voyages"]),
        "voyage_count": state["voyage_count"],
    }
    return json.dumps(payload, sort_keys=True)


def load_game(data):
    """Restore a save exactly; the id counter continues without skipping."""
    payload = json.loads(data) if isinstance(data, str) else data
    state = new_game()
    state["route_order"] = [int(route_id) for route_id in payload["route_order"]]
    state["routes"] = {
        int(route_id): {"name": route["name"], "segments": list(route["segments"])}
        for route_id, route in payload["routes"].items()
    }
    state["next_route_id"] = int(payload["next_route_id"])
    state["sail_capacity"] = int(payload["sail_capacity"])
    state["sails_deployed"] = int(payload["sails_deployed"])
    state["light_energy"] = int(payload["light_energy"])
    state["paused"] = bool(payload["paused"])
    state["active_route"] = payload["active_route"]
    state["position"] = int(payload["position"])
    state["passed_segments"] = [int(i) for i in payload["passed_segments"]]
    state["completed_voyages"] = list(payload["completed_voyages"])
    state["voyage_count"] = int(payload["voyage_count"])
    return state


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
