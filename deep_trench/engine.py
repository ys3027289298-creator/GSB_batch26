"""深海海沟规则层：rule_a ~ rule_j 是 save.py 通用规则在固定字段上的封装。

修复的问题（与 save.py 中的实现一一对应）：
- rule_a  氧气少算：余额不足时拒绝转移，不再扣成负数。
- rule_b  暂停仍下潜：暂停标志为真时拒绝操作。
- rule_c  重复样本：同一事件只登记一次，重复登记返回 False。
- rule_d  空样本返回文本：空集合返回 False，由调用方给出空提示文本。
- rule_e  先到样本未登记：按到达次序取最早事件（min 而非 max）。
- rule_f  重置不清：确实清空进度字段；无可重置字段时返回 False。
- rule_g  单次采集重复累计：一次性开关，重复触发返回 False。
- rule_h  查看样本误删：查看队首但不移除元素。
- rule_i  样本舱满仍采集：剩余容量 = 上限 - 已用，去掉差一错误。
- rule_j  读档跳号：先分配当前编号再自增，编号连续不跳号。
"""

import json

import save


def new_game():
    return {}


def rule_a(state):
    return save.transfer(state, "src", "dst", 10)


def rule_b(state):
    return save.gate(state, "closed")


def rule_c(state):
    return save.register_once(state.setdefault("events", {}), "__default__")


def rule_d(state):
    return save.empty_reply(state.get("samples"))


def rule_e(state):
    return save.pick_earliest(state["events"])


def rule_f(state):
    return save.reset_fields(state, ("progress", "done", "collected", "samples"))


def rule_g(state):
    return save.one_shot(state, "counted")


def rule_h(state):
    return save.peek_front(state["queue"])


def rule_i(state):
    return save.remaining_capacity(state["items"], state.get("cap", 2))


def rule_j(state):
    return save.alloc_id(state)


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
