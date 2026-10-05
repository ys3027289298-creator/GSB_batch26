"""固定输入重放：对修复版与缺陷版回放同一条命令序列。

每个缺陷对应一个状态级断言（不是只看返回值）：
修复版应全部通过，缺陷版应全部失败，失败即复现成功。
"""

import copy
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import buggy_main as buggy_engine
import main as fixed_engine

# 固定输入：{save} 在运行时替换为各引擎独立的临时存档路径
SCRIPT = [
    "bag",        # 0
    "explore",    # 1  -> 1 号（奇数，缺陷版不登记）
    "pickup 1",   # 2
    "pickup 1",   # 3  重复拾取
    "explore",    # 4  -> 2 号
    "pickup 2",   # 5
    "explore",    # 6  -> 3 号
    "pickup 3",   # 7  背包装满（修复版）
    "explore",    # 8  -> 4 号
    "pickup 4",   # 9  背包满仍拾取？
    "inspect 2",  # 10 查看遗物
    "pause",      # 11
    "explore",    # 12 暂停中探索？
    "resume",     # 13
    "explore",    # 14 -> 5 号
    "save {save}",# 15
    "reset",      # 16
    "status",     # 17
    "load {save}",# 18
    "explore",    # 19 读档后应发 6 号，不跳号/重号
    "explore",    # 20
    "explore",    # 21
    "explore",    # 22
    "explore",    # 23 修复版此时恰好剩 0 体力
    "explore",    # 24 0 体力必须拒绝
]


def run(engine, save_path):
    state = engine.new_game()
    transcript = []
    snaps = {}
    for idx, line in enumerate(SCRIPT):
        line = line.format(save=save_path)
        result = engine.dispatch(state, line)
        transcript.append((line, result))
        snaps[idx] = copy.deepcopy(state)
    return transcript, snaps


CHECKS = []


def check(name):
    def deco(fn):
        CHECKS.append((name, fn))
        return fn
    return deco


@check("1 重复遗物：重复拾取被拒，背包保持 [1]")
def c1(t, s):
    return t[3][1][0] is False and s[3]["bag"] == [1]


@check("2 背包满仍拾取：满后拒绝且背包仍为 [1,2,3]")
def c2(t, s):
    return t[9][1][0] is False and s[9]["bag"] == [1, 2, 3]


@check("3 空背包返回文本：空包 view_bag 必须返回 None")
def c3(t, s):
    return t[0][1] is None


@check("4 先到遗物未登记：1 号发现后必须在 registry")
def c4(t, s):
    return "1" in s[1]["registry"]


@check("5 暂停仍触发：暂停中探索整体失败且状态不变")
def c5(t, s):
    return (t[12][1][0] is False and s[12]["stamina"] == s[11]["stamina"]
            and s[12]["explorations"] == s[11]["explorations"]
            and s[12]["next_id"] == s[11]["next_id"])


@check("6 查看遗物误删：inspect 前后背包不变且仍含 2")
def c6(t, s):
    return s[10]["bag"] == s[9]["bag"] and 2 in s[10]["bag"]


@check("7 体力少算：恰剩 1 点时可探索且只扣到 0，0 点拒绝")
def c7(t, s):
    return (t[23][1][0] is True and s[23]["stamina"] == 0
            and t[24][1][0] is False and s[24]["stamina"] == 0)


@check("8 单次探索重复累计：5 次成功探索 explorations==5")
def c8(t, s):
    return s[14]["explorations"] == 5


@check("9 重置不清：reset 后所有计数/背包/登记归零")
def c9(t, s):
    return (s[17]["stamina"] == 10 and s[17]["explorations"] == 0
            and s[17]["bag"] == [] and s[17]["registry"] == {}
            and s[17]["next_id"] == 1 and s[17]["paused"] is False)


@check("10 读档跳号：读档后 next_id==6，再探索发 6 号")
def c10(t, s):
    return (s[18]["next_id"] == 6
            and set(s[18]["registry"]) == {"1", "2", "3", "4", "5"}
            and t[19][1][0] is True and "6" in s[19]["registry"]
            and s[19]["next_id"] == 7)


def score(label, engine, save_path, verbose):
    transcript, snaps = run(engine, save_path)
    if verbose:
        print("=" * 64)
        print("重放转录：%s" % label)
        print("=" * 64)
        for idx, (line, result) in enumerate(transcript):
            print("%2d > %-12s -> %r" % (idx, line, result))
        print()
    return [(name, bool(fn(transcript, snaps))) for name, fn in CHECKS]


def main():
    verbose = "-v" in sys.argv
    tmp = tempfile.mkdtemp(prefix="relic_replay_")
    fixed_rows = score("修复版 main.py", fixed_engine,
                       os.path.join(tmp, "fixed.json"), verbose)
    buggy_rows = score("缺陷版 buggy_main.py", buggy_engine,
                       os.path.join(tmp, "buggy.json"), verbose)

    print("%-46s %-8s %-8s" % ("缺陷检查（状态级）", "修复版", "缺陷版"))
    print("-" * 64)
    all_good = True
    for (name, ok_fixed), (_, ok_buggy) in zip(fixed_rows, buggy_rows):
        print("%-46s %-8s %-8s" % (name, "PASS" if ok_fixed else "FAIL",
                                   "复现" if not ok_buggy else "未复现"))
        all_good &= ok_fixed and not ok_buggy
    print("-" * 64)
    print("结论：%s" % ("全部 10 个缺陷已在缺陷版复现、修复版全部通过"
                       if all_good else "存在异常，需检查"))
    return 0 if all_good else 1


if __name__ == "__main__":
    sys.exit(main())
