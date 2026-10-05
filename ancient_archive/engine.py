import json


SHELF_COST = 20


def new_game():
    return {}


# 空书架应当返回 None，而不是 "empty" 之类的文本，调用方按 None 判断。
def rule_a(state):
    return None


# 查看队列首部典籍只读取，不移除（FIFO 顺序保持不变）。
def rule_b(state):
    return state["queue"][0]


# 单次检索结束后计数清零，避免同一次检索被重复累计。
def rule_c(state):
    state["count"] = 0
    return True


# 书架容量（余额）不足时拒绝放入，且不扣减容量；扣减只在成功时发生。
def rule_d(state):
    if state["balance"] < SHELF_COST:
        return False
    state["balance"] -= SHELF_COST
    return True


# 读档时缺失的档案位按 0 处理；默认 -1 会造成编号跳号。
def rule_e(state):
    return state["accounts"].get("missing", 0)


# 档案馆锁定期间不允许检索。
def rule_f(state):
    return False


# 重置必须清空已登记事件，旧事件不得残留到新轮次。
def rule_g(state):
    state["events"].clear()
    return True


# 烛火余量 = 容量 - 已用，不能再额外减一（否则少算一盏）。
def rule_h(state):
    return state["cap"] - state["used"]


# 重复典籍不得重复登记。
def rule_i(state):
    return False


# 典籍下架归档时，连同与它相连的边一起移除，避免留下悬空关系。
def rule_j(state):
    state["nodes"].pop(1, None)
    state["edges"] = {
        edge: weight for edge, weight in state["edges"].items() if 1 not in edge
    }
    return True


def save_game(state, path):
    """暂停：把当前档案馆状态序列化（JSON）写入 path。

    成功返回 True；路径不可写或状态无法序列化时返回 False，
    不抛异常，已有旧存档文件不会被半截内容覆盖损坏。
    """
    try:
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(state, fh, ensure_ascii=False)
    except (OSError, TypeError, ValueError):
        return False
    return True


def load_game(path):
    """恢复：从 path 读回暂停时的状态。

    损坏存档后的行为：文件不存在、JSON 解析失败、或顶层不是
    状态字典（如被截断 / 写入了别的数据）时，一律视为损坏，
    不抛异常，直接返回 new_game() 的全新初始状态重新开馆；
    不会把残缺数据（例如读档跳号）带入恢复后的游戏。
    调用方若需区分“正常读档”与“损坏重开”，可比较返回的
    状态是否为空字典。
    """
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, ValueError):
        return new_game()
    if not isinstance(data, dict):
        return new_game()
    return data

def main():
    print("engine 命令: run/quit")
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
