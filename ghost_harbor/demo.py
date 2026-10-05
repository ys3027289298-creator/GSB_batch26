import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ENGINE = os.path.join(HERE, "engine.py")


def build_script(save_path):
    return [
        ("arrive 幽灵一号 5", "编号 1"),
        ("arrive 幽灵一号 5", "已在港内"),
        ("arrive 幽灵二号 3", "编号 2"),
        ("arrive 幽灵三号 7", "编号 3"),
        ("arrive 幽灵四号 2", "编号 4"),
        ("dock", "幽灵一号 停靠 1"),
        ("dock", "幽灵二号 停靠 2"),
        ("dock", "幽灵三号 停靠 3"),
        ("dock", "泊位已满"),
        ("undock 幽灵五号", "泊位为空"),
        ("view 幽灵一号", "灵异值 5, 状态 已停靠"),
        ("view 幽灵一号", "灵异值 5, 状态 已停靠"),
        ("haunt", "灵异值总计: 17"),
        ("status", "引航次数 3"),
        ("pause", "港口已暂停"),
        ("dock", "已暂停, 无法引航"),
        ("undock 幽灵一号", "已暂停, 无法离港"),
        ("resume", "港口已恢复"),
        ("save " + save_path, "已存档"),
        ("reset", "港口已重置"),
        ("haunt", "灵异值总计: 0"),
        ("status", "泊位 0/3 排队 0 引航次数 0 下一编号 1"),
        ("load " + save_path, "已读档"),
        ("status", "泊位 3/3 排队 1 引航次数 3 下一编号 5"),
        ("undock 幽灵一号", "已离港"),
        ("dock", "幽灵四号 停靠 3"),
        ("arrive 幽灵五号 1", "编号 5"),
    ]


def main():
    with tempfile.TemporaryDirectory() as tmp:
        save_path = os.path.join(tmp, "save.json")
        script = build_script(save_path)

        stdin = "\n".join(line for line, _ in script) + "\nquit\n"
        proc = subprocess.run(
            [sys.executable, ENGINE],
            input=stdin,
            capture_output=True,
            text=True,
        )

    if proc.returncode != 0:
        print("FAIL: 引擎异常退出, code=%d" % proc.returncode)
        print(proc.stderr)
        return 1

    lines = [line.strip() for line in proc.stdout.splitlines()]
    lines = [line for line in lines if line and line != ">"]
    responses = lines[1:]

    failures = 0
    for (command, expected), got in zip(script, responses):
        if expected in got:
            print("PASS %-28s -> %s" % (command, got))
        else:
            failures += 1
            print("FAIL %-28s -> %s (期望包含 %s)" % (command, got, expected))

    if len(responses) != len(script):
        failures += 1
        print("FAIL: 响应行数 %d 与命令数 %d 不符" % (len(responses), len(script)))

    if failures:
        print("演示失败: %d 项" % failures)
        return 1
    print("演示通过: %d 项全部正确" % len(script))
    return 0


if __name__ == "__main__":
    sys.exit(main())
