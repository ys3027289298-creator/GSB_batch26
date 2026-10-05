"""幽灵港调度最小演示:按固定命令序列跑通完整流程。

用法: python3 demo.py
退出码 0 表示全部符合预期,非零表示失败。
"""

import os
import subprocess
import sys
import tempfile

ENGINE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "engine.py")
SAVE_PATH = os.path.join(tempfile.gettempdir(), "ghost_harbor_demo_save.json")

# (命令, 期望输出) 固定序列,覆盖:拒绝重复船只、泊位满拒停、空泊位文本、
# 先到先引航、暂停禁进出、查看不误删、灵异值全计、单次引航只计一次、
# 重置清空、读档不跳号。
SCRIPT = [
    ("arrive 幽影号 2", "进港 幽影号 #1"),
    ("arrive 幽影号 2", "拒绝 重复船只 幽影号"),
    ("arrive 雾行者 3", "进港 雾行者 #2"),
    ("arrive 低语号 5", "进港 低语号 #3"),
    ("arrive 残灯号 7", "进港 残灯号 #4"),
    ("pilot", "引航 幽影号 入泊位0"),
    ("pilot", "引航 雾行者 入泊位1"),
    ("pilot", "引航 低语号 入泊位2"),
    ("pilot", "泊位已满 无法停靠"),
    ("berth 0", "泊位0 幽影号"),
    ("berth 2", "泊位2 低语号"),
    ("depart 低语号", "出港 低语号"),
    ("berth 2", "泊位2 空泊位"),
    ("view 雾行者", "船只 雾行者 #2 灵异值3"),
    ("berth 1", "泊位1 雾行者"),
    ("haunting", "灵异值 12"),
    ("status", "状态 等待1 泊位2/3 引航3 灵异12 下一编号#5 暂停关"),
    ("pause", "已暂停"),
    ("arrive 新鬼号 1", "暂停中 禁止进出"),
    ("depart 幽影号", "暂停中 禁止进出"),
    ("pilot", "暂停中 禁止进出"),
    ("resume", "已恢复"),
    ("save " + SAVE_PATH, "已存档 " + SAVE_PATH),
    ("reset", "已重置"),
    ("status", "状态 等待0 泊位0/3 引航0 灵异0 下一编号#1 暂停关"),
    ("load " + SAVE_PATH, "已读档 " + SAVE_PATH),
    ("status", "状态 等待1 泊位2/3 引航3 灵异12 下一编号#5 暂停关"),
    ("arrive 新星号 1", "进港 新星号 #5"),
    ("quit", None),
]


def run_engine():
    commands = [cmd for cmd, _ in SCRIPT]
    proc = subprocess.run(
        [sys.executable, ENGINE],
        input="\n".join(commands) + "\n",
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        print("演示失败: 引擎退出码 {}".format(proc.returncode), file=sys.stderr)
        sys.stderr.write(proc.stderr)
        return None
    lines = []
    for raw in proc.stdout.splitlines()[1:]:  # 跳过首行命令提示
        line = raw.strip()
        if line.startswith(">"):
            line = line[1:].strip()
        if line:
            lines.append(line)
    return lines


def main():
    expected = [out for _, out in SCRIPT if out is not None]
    actual = run_engine()
    if actual is None:
        return 1
    if actual != expected:
        print("演示失败: 输出与预期不符", file=sys.stderr)
        for index in range(max(len(actual), len(expected))):
            got = actual[index] if index < len(actual) else "<缺失>"
            want = expected[index] if index < len(expected) else "<多余>"
            mark = " " if got == want else "!"
            print("{} [{:02d}] 期望: {} | 实际: {}".format(mark, index, want, got),
                  file=sys.stderr)
        return 1
    print("演示通过: {} 条命令的完整流程全部符合预期".format(len(SCRIPT)))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    finally:
        if os.path.exists(SAVE_PATH):
            os.remove(SAVE_PATH)
