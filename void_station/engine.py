"""虚空站资源调度引擎。

命令:
  supply <物资> <数量>   登记补给订单(同种物资重复登记会被忽略)
  receive <物资> <数量>  接收物资进入虚空舱(舱满拒绝)
  view                   查看舱内物资(只读, 不移除)
  transport [批数]       按先到先出运输物资(暂停时拒绝)
  pause / resume         暂停 / 恢复运输
  reset                  重置全部状态
  save <路径> / load <路径>  存档 / 读档(编号连续不跳号)
  status                 查看能量与运输统计
  quit                   退出
"""

import json
import sys

BAY_CAPACITY = 5      # 虚空舱容量(批)
ENERGY_PER_BATCH = 3  # 每运输一批消耗的能量


def new_state():
    return {
        "next_id": 1,        # 下一批物资编号
        "supplies": [],      # 待补给订单 [[item, qty], ...]
        "bay": [],           # 舱内物资批次 [[bid, item, qty], ...] 先到先出
        "paused": False,
        "energy_spent": 0,   # 累计能量消耗
        "transported": 0,    # 累计运输批数
        "trips": 0,          # 累计运输次数
    }


def _fmt_batch(batch):
    bid, item, qty = batch
    return f"#{bid} {item} x{qty}"


def cmd_supply(state, args):
    item, qty = args[0], int(args[1])
    if any(order[0] == item for order in state["supplies"]):
        return f"重复补给已忽略: {item}"
    state["supplies"].append([item, qty])
    return f"补给已登记: {item} x{qty}"


def cmd_receive(state, args):
    item, qty = args[0], int(args[1])
    if len(state["bay"]) >= BAY_CAPACITY:
        return "虚空舱已满，拒绝接收"
    bid = state["next_id"]
    state["next_id"] += 1
    state["bay"].append([bid, item, qty])
    state["supplies"] = [o for o in state["supplies"] if o[0] != item]
    return f"已接收: {_fmt_batch(state['bay'][-1])}"


def cmd_view(state, _args):
    if not state["bay"]:
        return "虚空舱为空"
    return "舱内物资: " + ", ".join(_fmt_batch(b) for b in state["bay"])


def cmd_transport(state, args):
    if state["paused"]:
        return "运输已暂停"
    if not state["bay"]:
        return "虚空舱为空"
    count = int(args[0]) if args else 1
    moved = []
    for _ in range(min(count, len(state["bay"]))):
        moved.append(state["bay"].pop(0))  # 先到先出
    state["energy_spent"] += ENERGY_PER_BATCH * len(moved)
    state["transported"] += len(moved)
    state["trips"] += 1  # 单次运输只累计一次
    return f"已运输 {len(moved)} 批: " + ", ".join(_fmt_batch(b) for b in moved)


def cmd_pause(state, _args):
    state["paused"] = True
    return "运输已暂停"


def cmd_resume(state, _args):
    state["paused"] = False
    return "运输已恢复"


def cmd_reset(state, _args):
    state.clear()
    state.update(new_state())
    return "已重置"


def cmd_save(state, args):
    with open(args[0], "w", encoding="utf-8") as fh:
        json.dump(state, fh, ensure_ascii=False)
    return f"已存档: {args[0]}"


def cmd_load(state, args):
    with open(args[0], encoding="utf-8") as fh:
        data = json.load(fh)
    state.clear()
    state.update(data)  # 恢复 next_id, 读档后编号连续
    return f"已读档: {args[0]}"


def cmd_status(state, _args):
    return (
        f"能量消耗={state['energy_spent']} "
        f"已运输={state['transported']}批 "
        f"运输次数={state['trips']} "
        f"舱内={len(state['bay'])}批 "
        f"下一编号={state['next_id']}"
    )


COMMANDS = {
    "supply": cmd_supply,
    "receive": cmd_receive,
    "view": cmd_view,
    "transport": cmd_transport,
    "pause": cmd_pause,
    "resume": cmd_resume,
    "reset": cmd_reset,
    "save": cmd_save,
    "load": cmd_load,
    "status": cmd_status,
}


def execute(state, line):
    parts = line.split()
    if not parts:
        return ""
    cmd, args = parts[0], parts[1:]
    handler = COMMANDS.get(cmd)
    if handler is None:
        return f"未知命令: {cmd}"
    try:
        return handler(state, args)
    except (IndexError, ValueError):
        return f"命令参数错误: {line}"
    except OSError as exc:
        return f"文件错误: {exc}"


def main():
    print("void_station 命令: " + "/".join(sorted(COMMANDS)) + "/quit")
    state = new_state()
    while True:
        try:
            raw = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not raw or raw == "quit":
            break
        print(execute(state, raw))


if __name__ == "__main__":
    main()
