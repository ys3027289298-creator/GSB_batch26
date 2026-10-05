"""void_station 最小演示脚本。

按固定命令序列跑通完整调度流程, 逐步校验输出;
全部通过时退出码为 0, 任何一步不符合预期即以非零退出。
"""

import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import engine


def main():
    state = engine.new_game()
    save_path = os.path.join(tempfile.mkdtemp(prefix="void_station_"), "save.json")

    # (命令, 期望输出); 期望为 None 表示只要求不抛异常。
    script = [
        # 重复补给: 同一单号只接收一次
        ("supply S1", "OK supply S1"),
        ("supply S1", "ERR supply S1"),
        ("supply S2", "OK supply S2"),
        ("supply S3", "OK supply S3"),
        # 虚空舱满 (容量 3) 拒绝继续接收
        ("supply S4", "ERR supply S4"),
        # 查看物资不删除, 数量不变
        ("view", "bay S1 S2 S3"),
        ("view", "bay S1 S2 S3"),
        # 先到的物资先分配
        ("allocate", "alloc S1"),
        ("allocate", "alloc S2"),
        # 空出舱位后可继续接收
        ("supply S4", "OK supply S4"),
        # 空舱返回空文本
        ("allocate", "alloc S3"),
        ("allocate", "alloc S4"),
        ("allocate", "alloc none"),
        ("view", "bay empty"),
        # 运输编号 1、2; 存档后读档, 编号连续不跳号
        ("enqueue A", "enqueued 1"),
        ("enqueue B", "enqueued 2"),
        ("save " + save_path, "saved"),
        ("load " + save_path, "loaded"),
        ("enqueue C", "enqueued 3"),
        # 暂停期间拒绝运输
        ("pause", "paused"),
        ("ship", "ERR ship"),
        ("resume", "resumed"),
        # 每次运输只扣 10 点能量, 不重复累计 (25 -> 15 -> 5)
        ("ship", "shipped A"),
        ("status", "status energy=15 shipped=1 bay=0 queue=2"),
        ("ship", "shipped B"),
        ("status", "status energy=5 shipped=2 bay=0 queue=1"),
        # 能量不足拒绝运输
        ("ship", "ERR ship"),
        ("recharge 10", "energy 15"),
        ("ship", "shipped C"),
        # 队列空拒绝运输
        ("ship", "ERR ship"),
        # 重置清空全部状态 (含能量与编号)
        ("reset", "reset done"),
        ("view", "bay empty"),
        ("status", "status energy=25 shipped=0 bay=0 queue=0"),
        ("enqueue D", "enqueued 1"),
        ("ship", "shipped D"),
    ]

    failures = 0
    for step, (command, expected) in enumerate(script, 1):
        try:
            actual = engine.run_command(state, command)
        except Exception as exc:  # 命令执行抛异常也算失败
            actual = "EXCEPTION " + repr(exc)
        ok = expected is None or actual == expected
        mark = "PASS" if ok else "FAIL"
        print("[{:02d}] {:<4} {:<28} -> {}".format(step, mark, command, actual))
        if not ok:
            failures += 1
            print("     expected: {}".format(expected))

    if failures:
        print("demo FAILED: {} step(s) mismatch".format(failures))
        return 1
    print("demo OK: all {} steps passed".format(len(script)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
