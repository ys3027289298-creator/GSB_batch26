"""古代档案馆检索保存 — 存档 / 读档模块。

行为说明
========

暂停恢复 (pause / resume)
-------------------------
- ``save_game(state, slot)`` 把当前游戏状态完整写入指定槽位, 之后进程
  可以安全退出; ``load_game(slot)`` 读回的状态与暂停前逐项一致。
- 恢复时不跳号、不丢项: 检索队列的先后顺序、烛火余额、检索计数、
  典籍编号计数器(``next_id``)等全部按原样还原, 读档不会消耗或推进
  任何计数器, 重复读同一槽位结果相同(幂等)。
- 同一槽位再次保存会原子覆盖旧档(先写临时文件再 rename), 写入中途
  崩溃不会留下半残存档; 不同槽位互不影响, 槽位号连续不跳号。

损坏存档 (corrupted save)
-------------------------
- 槽位不存在: ``load_game`` 返回 ``None``, 不抛异常, 调用方按新开局
  处理。
- 存档内容损坏(非法 JSON、缺字段、版本或校验和不匹配): ``load_game``
  返回 ``None``, 并把损坏文件原样备份为 ``<存档>.corrupt`` 以便人工
  排查, 不删除、不覆盖原始损坏数据。
- 读档失败绝不修改调用方内存中的当前状态, 也不会产生任何槽位文件。
"""

import hashlib
import json
import os
import tempfile

SAVE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "saves")
FORMAT_VERSION = 1

REQUIRED_FIELDS = ("queue", "count", "balance", "next_id")


def _slot_path(slot):
    return os.path.join(SAVE_DIR, "slot_{}.json".format(int(slot)))


def _checksum(payload):
    raw = json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def save_game(state, slot):
    """把 state 完整写入槽位 slot, 原子覆盖旧档。"""
    os.makedirs(SAVE_DIR, exist_ok=True)
    payload = {
        "version": FORMAT_VERSION,
        "state": state,
    }
    envelope = dict(payload)
    envelope["checksum"] = _checksum(payload)
    fd, tmp_path = tempfile.mkstemp(dir=SAVE_DIR, prefix=".tmp_", suffix=".json")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(envelope, fh, ensure_ascii=False, sort_keys=True)
        os.replace(tmp_path, _slot_path(slot))
    except BaseException:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise
    return _slot_path(slot)


def _validate(envelope):
    if not isinstance(envelope, dict):
        return False
    if envelope.get("version") != FORMAT_VERSION:
        return False
    payload = {"version": envelope.get("version"), "state": envelope.get("state")}
    if envelope.get("checksum") != _checksum(payload):
        return False
    state = envelope.get("state")
    if not isinstance(state, dict):
        return False
    return all(field in state for field in REQUIRED_FIELDS)


def load_game(slot):
    """读取槽位 slot。

    返回状态 dict; 槽位缺失或存档损坏时返回 None, 损坏文件会被备份为
    ``<存档>.corrupt``。本函数不修改任何调用方状态。
    """
    path = _slot_path(slot)
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as fh:
            envelope = json.load(fh)
    except (OSError, ValueError):
        envelope = None
    if envelope is None or not _validate(envelope):
        backup = path + ".corrupt"
        if not os.path.exists(backup):
            os.replace(path, backup)
        else:
            os.unlink(path)
        return None
    return json.loads(json.dumps(envelope["state"]))


def list_slots():
    """按槽位号升序列出已存在的槽位, 不跳号。"""
    if not os.path.isdir(SAVE_DIR):
        return []
    slots = []
    for name in os.listdir(SAVE_DIR):
        if name.startswith("slot_") and name.endswith(".json"):
            try:
                slots.append(int(name[len("slot_"):-len(".json")]))
            except ValueError:
                continue
    return sorted(slots)


def next_slot():
    """返回下一个可用槽位号, 从 0 开始连续递增。"""
    slots = list_slots()
    return slots[-1] + 1 if slots else 0
