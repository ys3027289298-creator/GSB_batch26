"""星之熔炉最小演示: 用固定命令序列跑通完整流程。

用法: python demo.py
成功退出码为 0, 任何一步输出与预期不符则以非零码退出。
"""

import subprocess
import sys
from pathlib import Path

ENGINE = Path(__file__).with_name("engine.py")

# (命令, 期望输出)。覆盖全部修复点。
SCRIPT = [
    ("add 铁矿", "ok"),                       # 投入第一种矿石
    ("add 铁矿", "duplicate"),                # 1. 重复矿石被拒
    ("add 铜矿", "ok"),
    ("add 星砂", "ok"),
    ("add 金矿", "full"),                     # 2. 熔炉满 (容量3) 仍投入被拒
    ("recipe 金矿", "none"),                  # 3. 空配方不返回占位文本
    ("recipe 铁矿", "铁锭/10"),
    ("view", "铁矿,铜矿,星砂"),               # 6a. 查看矿石
    ("view", "铁矿,铜矿,星砂"),               # 6b. 查看不会误删
    ("pause", "ok"),
    ("smelt", "paused"),                      # 5. 暂停时不锻造
    ("resume", "ok"),
    ("smelt", "铁锭"),                        # 4. 先投入的铁矿先被冶炼 (FIFO)
    ("status", "stardust=10 forged=1"),       # 7. 星尘全额 10; 8. 单次锻造只累计 1
    ("save", "1"),                            # 第一次存档
    ("smelt", "铜锭"),
    ("status", "stardust=18 forged=2"),
    ("save", "2"),
    ("load 1", "ok"),                         # 回档到第一次存档
    ("status", "stardust=10 forged=1"),
    ("view", "铜矿,星砂"),
    ("save", "3"),                            # 10. 读档后存档号不跳号/不回退
    ("load 1", "ok"),
    ("save", "4"),
    ("reset", "ok"),                          # 9. 重置
    ("status", "stardust=0 forged=0"),        # 9. 星尘与计数全部清空
    ("view", "empty"),                        # 9. 熔炉也清空
    ("load 1", "missing"),                    # 9. 存档也清空
    ("quit", None),
]


def main():
    commands = [c for c, _ in SCRIPT]
    proc = subprocess.run(
        [sys.executable, str(ENGINE)],
        input="\n".join(commands) + "\n",
        capture_output=True,
        text=True,
        timeout=10,
    )
    if proc.returncode != 0:
        print("engine 进程异常退出, code=%d\n%s" % (proc.returncode, proc.stderr))
        return 1

    # 第一行是欢迎语, 之后每条命令一行输出 (去掉 input 提示符 "> ")。
    lines = proc.stdout.splitlines()
    outputs = [l[2:] if l.startswith("> ") else l for l in lines[1:]]
    failures = 0
    for idx, ((command, expected), actual) in enumerate(zip(SCRIPT, outputs)):
        if expected is None:
            continue
        if actual != expected:
            failures += 1
            print("[FAIL] step %d: %s -> 期望 %r, 实际 %r"
                  % (idx + 1, command, expected, actual))
        else:
            print("[ok]   %s -> %s" % (command, actual))

    if len(outputs) != len(SCRIPT):
        failures += 1
        print("[FAIL] 输出行数不匹配: 期望 %d, 实际 %d"
              % (len(SCRIPT), len(outputs)))

    if failures:
        print("演示失败: %d 处不符" % failures)
        return 1
    print("演示通过: 星之熔炉完整流程正常")
    return 0


if __name__ == "__main__":
    sys.exit(main())
