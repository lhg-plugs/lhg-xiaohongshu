#!/usr/bin/env python3
"""lhg-xiaohongshu 硬门①：发布相关命令执行前跑合规审计，有 blocker 则拦截。

触发：PreToolUse / Bash。脚本先判断本次 Bash 命令是否与"发布"相关
（publish / 发布 / 小红书），不是则 0 开销直接放行；是则对笔记目录
运行插件自带的合规审计脚本，有 blocker 时拒绝执行。

逃生方式（按推荐度排序）：
  1. 跑 `/lhg-xiaohongshu:xhs-audit` 修掉 blocker 后重新执行（推荐）。
  2. 紧急情况：LHG_XHS_HOOKS_OFF=1 <原命令>（单次豁免本次 hook）。
  3. /plugin disable lhg-xiaohongshu（整个插件停用，hooks 不再触发）。

设计原则：脚本内部出错（找不到审计脚本、超时、笔记目录不存在等）时
fail-open 直接放行，不因插件自身故障骚扰用户。
零第三方依赖。
"""

import json
import os
import re
import subprocess
import sys

AUDIT_TIMEOUT = 60
PUBLISH_RE = re.compile(r"xhs|xiaohongshu|publish|发布|小红书", re.I)


def main() -> int:
    # 逃生开关
    if os.environ.get("LHG_XHS_HOOKS_OFF") == "1":
        return 0

    try:
        raw = sys.stdin.read()
        payload = json.loads(raw) if raw.strip() else {}
    except Exception:
        return 0  # 输入解析失败：fail-open

    tool_input = payload.get("tool_input", {}) or {}
    command = tool_input.get("command", "") or ""

    # 非发布相关命令：快速放行
    if not PUBLISH_RE.search(command):
        return 0

    plugin_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    script = os.path.join(plugin_root, "scripts", "audit", "xhs_audit.py")
    if not os.path.isfile(script):
        return 0  # 审计脚本缺失：fail-open，不拦截用户

    project_dir = os.environ.get("CLAUDE_PROJECT_DIR", "") or os.getcwd()
    notes = os.path.join(project_dir, "notes")
    target = notes if os.path.isdir(notes) else None
    if target is None:
        return 0  # 没有笔记目录：fail-open

    try:
        r = subprocess.run(
            [sys.executable, script, "--target", target, "--format", "json"],
            capture_output=True, text=True, timeout=AUDIT_TIMEOUT)
        data = json.loads(r.stdout)
    except Exception:
        return 0  # 审计失败：fail-open

    blockers = [f for f in data.get("findings", [])
                if f.get("severity") == "blocker"]
    if not blockers:
        return 0

    lines = ["【lhg-xiaohongshu】发布前门禁：发现 %d 个 blocker，已拦截本次发布命令。" % len(blockers)]
    for f in blockers[:8]:
        lines.append("  - [%s] %s:%s %s" % (
            f.get("rule_id"), f.get("file"), f.get("line"), f.get("title")))
    if len(blockers) > 8:
        lines.append("  …还有 %d 个，跑 /lhg-xiaohongshu:xhs-audit 看全部" % (len(blockers) - 8))
    lines.append("修掉后重新执行；紧急豁免：LHG_XHS_HOOKS_OFF=1 <原命令>")

    out = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": "\n".join(lines),
        }
    }
    print(json.dumps(out, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
