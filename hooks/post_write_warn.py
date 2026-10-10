#!/usr/bin/env python3
"""lhg-fullstack 硬门②（警告级，不拦截）：写生产代码无对应测试文件时提醒。

触发：PostToolUse / Write|Edit。只做提醒，永远 exit 0、不拦截写入。

逃生方式：LHG_FS_HOOKS_OFF=1（环境变量）可关闭本提醒；
或 /plugin disable lhg-fullstack 停用整个插件。
零第三方依赖。
"""

import json
import os
import re
import sys

CODE_EXTS = {".ts", ".tsx", ".js", ".jsx", ".py"}
TEST_BASENAME_RES = [
    re.compile(r".*\.test\..*"),
    re.compile(r".*\.spec\..*"),
    re.compile(r"test_.*\.py"),
    re.compile(r".*_test\.py"),
]
SKIP_DIR_PARTS = {
    "node_modules", ".next", "dist", "build", "coverage",
    "__tests__", "tests", "test", "fixtures", ".git", "__pycache__",
}


def is_test_file(path: str) -> bool:
    base = os.path.basename(path)
    if any(r.match(base) for r in TEST_BASENAME_RES):
        return True
    parts = path.replace("\\", "/").split("/")
    return any(p in SKIP_DIR_PARTS for p in parts)


def find_test_for(path: str) -> bool:
    """同目录找 <stem>.test.<ext> / <stem>.spec.<ext> / test_<stem>.py 等。"""
    d = os.path.dirname(path) or "."
    stem, ext = os.path.splitext(os.path.basename(path))
    candidates = [
        os.path.join(d, "%s.test%s" % (stem, ext)),
        os.path.join(d, "%s.spec%s" % (stem, ext)),
    ]
    if ext == ".py":
        candidates += [
            os.path.join(d, "test_%s.py" % stem),
            os.path.join(d, "%s_test.py" % stem),
        ]
    # 也看看 tests/ 与 __tests__/ 目录
    for tdir in ("tests", "__tests__", "test"):
        td = os.path.join(d, tdir)
        candidates += [
            os.path.join(td, "%s.test%s" % (stem, ext)),
            os.path.join(td, "test_%s.py" % stem),
        ]
    return any(os.path.isfile(c) for c in candidates)


def main() -> int:
    if os.environ.get("LHG_FS_HOOKS_OFF") == "1":
        return 0

    try:
        raw = sys.stdin.read()
        payload = json.loads(raw) if raw.strip() else {}
    except Exception:
        return 0

    tool_input = payload.get("tool_input", {}) or {}
    file_path = tool_input.get("file_path", "") or ""
    if not file_path:
        return 0

    _, ext = os.path.splitext(file_path)
    if ext not in CODE_EXTS:
        return 0
    if is_test_file(file_path):
        return 0  # 写的是测试文件本身，不提醒
    if find_test_for(file_path):
        return 0  # 已有对应测试，不提醒

    msg = (
        "TDD 提醒（lhg-fullstack）：%s 疑似生产代码，未找到对应的测试文件。\n"
        "建议补一个对应测试；如本次确无必要，在 /lhg-fullstack:ship 报告中写清豁免理由。\n"
        "关闭本提醒：export LHG_FS_HOOKS_OFF=1（当前会话有效）。"
    ) % file_path
    out = {
        "hookSpecificOutput": {
            "hookEventName": "PostToolUse",
            "additionalContext": msg,
        }
    }
    sys.stdout.write(json.dumps(out, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
