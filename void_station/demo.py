"""最小演示脚本: 按固定命令序列跑通虚空站完整流程。

用法: python3 demo.py
全部步骤符合预期时退出码为 0, 任一步骤失败退出码为 1。
"""

import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ENGINE = os.path.join(HERE, "engine.py")


def main():
    save_path = os.path.join(tempfile.mkdtemp(), "save.json")

    # (命令, 期望输出中包含的文本)
    steps = [
        # 重复补给: 同种物资重复登记被忽略
        ("supply 矿石 10", "补给已登记: 矿石 x10"),
        ("supply 矿石 10", "重复补给已忽略: 矿石"),
        # 正常接收, 编号从 1 开始
        ("receive 矿石 10", "已接收: #1 矿石 x10"),
        ("receive 晶体 4", "已接收: #2 晶体 x4"),
        ("receive 燃料 6", "已接收: #3 燃料 x6"),
        ("receive 食物 8", "已接收: #4 食物 x8"),
        ("receive 药品 2", "已接收: #5 药品 x2"),
        # 虚空舱满仍接收: 第 6 批被拒绝
        ("receive 合金 1", "虚空舱已满，拒绝接收"),
        # 查看物资误删: 查看两次内容一致
        ("view", "舱内物资: #1 矿石 x10, #2 晶体 x4, #3 燃料 x6, #4 食物 x8, #5 药品 x2"),
        ("view", "舱内物资: #1 矿石 x10, #2 晶体 x4, #3 燃料 x6, #4 食物 x8, #5 药品 x2"),
        # 先到物资未分配: 先到先出, 先运 #1 #2
        ("transport 2", "已运输 2 批: #1 矿石 x10, #2 晶体 x4"),
        # 暂停仍运输: 暂停后运输被拒绝且舱内不变
        ("pause", "运输已暂停"),
        ("transport 1", "运输已暂停"),
        ("view", "舱内物资: #3 燃料 x6, #4 食物 x8, #5 药品 x2"),
        ("resume", "运输已恢复"),
        # 能量少算: 每次运输都累计; 单次运输重复累计: trips 只加一次
        ("transport 1", "已运输 1 批: #3 燃料 x6"),
        ("status", "能量消耗=9 已运输=3批 运输次数=2"),
        # 存档后读档跳号: 编号从存档处继续
        (f"save {save_path}", "已存档"),
        ("receive 合金 1", "已接收: #6 合金 x1"),
        (f"load {save_path}", "已读档"),
        ("receive 合金 1", "已接收: #6 合金 x1"),
        # 运空后空舱返回文本
        ("transport 3", "已运输 3 批: #4 食物 x8, #5 药品 x2, #6 合金 x1"),
        ("view", "虚空舱为空"),
        ("transport 1", "虚空舱为空"),
        # 重置不清: 重置后全部归零
        ("reset", "已重置"),
        ("status", "能量消耗=0 已运输=0批 运输次数=0 舱内=0批 下一编号=1"),
        ("quit", None),
    ]

    script = "\n".join(cmd for cmd, _ in steps) + "\n"
    proc = subprocess.run(
        [sys.executable, ENGINE],
        input=script,
        capture_output=True,
        text=True,
        cwd=HERE,
    )
    if proc.returncode != 0:
        print(proc.stderr, file=sys.stderr)
        print("FAIL: 引擎进程异常退出", file=sys.stderr)
        return 1

    lines = [ln[2:].strip() for ln in proc.stdout.splitlines()
              if ln.startswith("> ") and ln.strip() != ">"]
    if len(lines) != len(steps) - 1:  # quit 无输出
        print(f"FAIL: 输出行数不符, 期望 {len(steps) - 1}, 实际 {len(lines)}", file=sys.stderr)
        return 1

    failed = 0
    for (cmd, expected), got in zip(steps, lines):
        if expected is None:
            continue
        if expected in got:
            print(f"PASS {cmd!r} -> {got}")
        else:
            failed += 1
            print(f"FAIL {cmd!r} -> {got!r}, 期望包含 {expected!r}")

    if failed:
        print(f"{failed} 步失败", file=sys.stderr)
        return 1
    print("全部步骤通过")
    return 0


if __name__ == "__main__":
    sys.exit(main())
