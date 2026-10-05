"""星之熔炉最小演示：按固定命令序列跑通完整流程，任一断言失败则以非零退出。"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import engine


def main():
    state = engine.new_game()
    failures = []

    def check(label, actual, expected):
        if actual != expected:
            failures.append("%s: 期望 %r, 实际 %r" % (label, expected, actual))

    # 投入矿石：重复矿石被拒、熔炉满仍投入被拒
    check("add ore-1", engine.dispatch(state, "add", "ore-1", "iron"), True)
    check("add ore-2", engine.dispatch(state, "add", "ore-2", "iron"), True)
    check("add ore-3", engine.dispatch(state, "add", "ore-3", "iron"), True)
    check("重复矿石被拒", engine.dispatch(state, "add", "ore-1", "iron"), False)
    check("熔炉满仍投入被拒", engine.dispatch(state, "add", "ore-4", "iron"), False)

    # 查看矿石不删除
    check("查看矿石", engine.dispatch(state, "view"),
          [("ore-1", "iron"), ("ore-2", "iron"), ("ore-3", "iron")])
    check("查看后矿石仍在", engine.dispatch(state, "view"),
          [("ore-1", "iron"), ("ore-2", "iron"), ("ore-3", "iron")])

    # 空配方锻造返回 None（不返回文本）
    check("空配方返回 None", engine.dispatch(state, "forge"), None)

    # 选择配方并锻造：先到矿石先冶炼、星尘足量、单次只累计一次
    check("设置配方", engine.dispatch(state, "recipe", "iron_ingot"), True)
    first = engine.dispatch(state, "forge")
    check("先到矿石先冶炼", first, {"ore": "ore-1", "recipe": "iron_ingot", "stardust": 10})
    check("星尘足量", engine.dispatch(state, "stardust"), 10)
    check("单次锻造只累计一次", engine.dispatch(state, "forged"), 1)
    check("产物计数", engine.dispatch(state, "products"), {"iron_ingot": 1})

    # 暂停时不能锻造，恢复后可以继续
    check("暂停", engine.dispatch(state, "pause"), True)
    check("暂停仍锻造被拒", engine.dispatch(state, "forge"), False)
    check("恢复", engine.dispatch(state, "resume"), True)
    second = engine.dispatch(state, "forge")
    check("恢复后锻造", second, {"ore": "ore-2", "recipe": "iron_ingot", "stardust": 10})
    check("星尘累计", engine.dispatch(state, "stardust"), 20)

    # 存档、继续游戏、再存档
    check("存档 1", engine.dispatch(state, "save"), 1)
    engine.dispatch(state, "forge")
    check("存档 2", engine.dispatch(state, "save"), 2)

    # 重置清空全部进度
    check("重置", engine.dispatch(state, "reset"), True)
    check("重置清空矿石", engine.dispatch(state, "view"), [])
    check("重置清空星尘", engine.dispatch(state, "stardust"), 0)
    check("重置清空锻造数", engine.dispatch(state, "forged"), 0)

    # 读档恢复且存档编号不跳号
    check("读档 1", engine.dispatch(state, "load", 1), True)
    check("读档恢复星尘", engine.dispatch(state, "stardust"), 20)
    check("读档恢复矿石", engine.dispatch(state, "view"), [("ore-3", "iron")])
    check("读档不跳号", engine.dispatch(state, "save"), 3)
    check("存档列表", engine.dispatch(state, "saves"), [1, 2, 3])

    if failures:
        for failure in failures:
            print("FAIL", failure)
        print("演示失败：%d 项断言未通过" % len(failures))
        return 1
    print("演示通过：全部断言成功")
    return 0


if __name__ == "__main__":
    sys.exit(main())
