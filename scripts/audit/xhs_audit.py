#!/usr/bin/env python3
"""lhg-xiaohongshu 确定性合规审计：16 条规则，零第三方依赖。

扫描目标目录的小红书笔记（Markdown），检测广告法极限词/功效断言、
标题/标签/封面（1242x1660）/正文/营销信号。输出 JSON 与人类可读报告；
有 blocker 时以 exit code 2 退出（供 hooks 与 CI 使用）。

用法：
    python3 xhs_audit.py --target <笔记文件或目录> [--format json|text] [--fail-on blocker|warning|nit]

规则文案与词表均为本项目原创（自建极限词表），未复制任何第三方原文。
"""

import argparse
import json
import os
import re
import struct
import sys

VERSION = "1.0.0"
TOOL = "lhg-xiaohongshu/xhs-audit"

SKIP_DIRS = {"node_modules", ".git", "__pycache__", "vendor"}

RULES = [
    # ---- 广告法极限词 / 功效断言 ----
    {"id": "XHS-LIMIT-001", "severity": "blocker", "category": "极限词",
     "title": "广告法极限词",
     "words": ["最好", "第一", "国家级", "首个", "首家", "顶级", "顶尖",
               "之最", "第一品牌", "最便宜", "最低价", "最高级", "最佳",
               "独家", "首创", "极致", "王者", "领导者"],
     "detail": "命中广告法极限词。必须删除或换成可验证的具体表述（“最好用”→“我用过3款里最顺手的”）。"},
    {"id": "XHS-LIMIT-002", "severity": "warning", "category": "极限词",
     "title": "功效断言词",
     "words": ["根治", "治愈", "100%有效", "百分百有效", "保证见效",
               "包治百病", "永不复发", "立竿见影"],
     "detail": "出现功效断言词。必须改成“我的体验”口吻（“我用了感觉…”），不许写保证口吻。"},
    # ---- 标题 ----
    {"id": "XHS-TITLE-001", "severity": "warning", "category": "标题",
     "title": "缺少标题", "no_title": True,
     "detail": "没有找到标题（frontmatter 的 title 或一级标题）。小红书标题决定点击率，先定标题。"},
    {"id": "XHS-TITLE-002", "severity": "warning", "category": "标题",
     "title": "标题超过 20 字", "title_max_len": 20,
     "detail": "标题超过 20 字，信息流里会被截断。压缩到 20 字内，保留数字/人群/场景至少其一。"},
    {"id": "XHS-TITLE-003", "severity": "nit", "category": "标题",
     "title": "标题缺少吸引点", "title_hook": True,
     "detail": "标题里没有数字、emoji 或悬念符号（！？），点击冲动弱。加一个具体元素试试。"},
    # ---- 标签 ----
    {"id": "XHS-TAG-001", "severity": "warning", "category": "标签",
     "title": "标签数量异常", "tag_range": (3, 10),
     "detail": "标签不在 3~10 个。少了没流量，多了像 spam。建议 5~8 个：2 大流量+3 精准+1~2 品牌。"},
    {"id": "XHS-TAG-002", "severity": "warning", "category": "标签",
     "title": "标签重复", "tag_dup": True,
     "detail": "存在重复标签。删掉重复的，换成精准词或品牌词。"},
    # ---- 封面 ----
    {"id": "XHS-COVER-001", "severity": "blocker", "category": "封面",
     "title": "封面图缺失", "no_cover": True,
     "detail": "未找到封面图引用（frontmatter 的 cover 或正文图片）。小红书没封面等于没点击，先做封面。"},
    {"id": "XHS-COVER-002", "severity": "blocker", "category": "封面",
     "title": "封面比例非 3:4", "cover_ratio": (3.0 / 4.0, 0.02),
     "detail": "封面比例不是 3:4，会被裁剪或留白，主体可能被切掉。重做 1242×1660。"},
    {"id": "XHS-COVER-003", "severity": "warning", "category": "封面",
     "title": "封面尺寸非 1242×1660", "cover_size": (1242, 1660),
     "detail": "封面比例对了但尺寸不是 1242×1660。建议按标准尺寸重出，保证清晰度。"},
    # ---- 正文 ----
    {"id": "XHS-BODY-001", "severity": "warning", "category": "正文",
     "title": "正文过短/过长", "body_range": (100, 1000),
     "detail": "正文不足 100 字像水帖，超 1000 字没人看完。种草笔记建议 300~800 字。"},
    {"id": "XHS-BODY-002", "severity": "warning", "category": "正文",
     "title": "错别字", "words": ["做为", "园满", "连索", "按装"],
     "detail": "命中高频错别字。直接替换，错别字是“不专业”的第一信号。"},
    {"id": "XHS-BODY-003", "severity": "nit", "category": "正文",
     "title": "AI 味信号", "count_words": ["首先", "其次", "最后", "综上所述"], "threshold": 2,
     "detail": "八股词出现≥2 次，小红书用户对论文腔零容忍。删掉，用口语重写。"},
    # ---- 营销信号 ----
    {"id": "XHS-AD-001", "severity": "warning", "category": "营销",
     "title": "疑似联系方式", "pattern": r"微信\s*[：:]\s*[a-zA-Z0-9_-]{5,}|1[3-9]\d{9}|加我微信|私聊我",
     "detail": "正文出现联系方式/引流话术。平台判营销号的强信号，建议删掉走评论区。"},
    {"id": "XHS-AD-002", "severity": "warning", "category": "营销",
     "title": "绝对化促销话术", "words": ["全网最低", "仅此一天", "错过再等一年", "最后一天", "清仓甩卖"],
     "detail": "出现绝对化促销话术。价格只陈述事实（“我买的时候99”），不做全网承诺。"},
    {"id": "XHS-AD-003", "severity": "nit", "category": "营销",
     "title": "疑似硬广（全文无“我”）", "no_first_person": True,
     "detail": "全文没有出现“我”，像说明书不像分享。加真实体验细节，去广告味。"},
]

_RULE_BY_ID = {r["id"]: r for r in RULES}
EMOJI_RE = re.compile(r"[\U0001F300-\U0001FAFF\u2600-\u27BF\u2B00-\u2BFF]")


class Finding:
    __slots__ = ("rule_id", "severity", "category", "title", "file",
                 "line", "snippet", "detail")

    def __init__(self, rule_id, severity, category, title, file, line,
                 snippet, detail):
        self.rule_id = rule_id
        self.severity = severity
        self.category = category
        self.title = title
        self.file = file
        self.line = line
        self.snippet = snippet
        self.detail = detail

    def to_dict(self):
        return {
            "rule_id": self.rule_id, "severity": self.severity,
            "category": self.category, "title": self.title,
            "file": self.file, "line": self.line,
            "snippet": self.snippet, "detail": self.detail,
        }


def collect_files(target):
    if os.path.isfile(target):
        return [target] if target.endswith(".md") else []
    out = []
    for root, dirs, files in os.walk(target):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for f in files:
            if f.endswith(".md"):
                out.append(os.path.join(root, f))
    return sorted(out)


def read_text(path):
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            return fh.read()
    except OSError:
        return ""


def read_png_size(path):
    """只用标准库解析 PNG IHDR，返回 (w, h)，失败返回 None。"""
    try:
        with open(path, "rb") as fh:
            sig = fh.read(8)
            if sig != b"\x89PNG\r\n\x1a\n":
                return None
            while True:
                head = fh.read(8)
                if len(head) < 8:
                    return None
                (ln, typ) = struct.unpack(">I4s", head)
                data = fh.read(ln)
                fh.read(4)  # CRC
                if typ == b"IHDR":
                    w, h = struct.unpack(">II", data[:8])
                    return (w, h)
                if typ == b"IEND":
                    return None
    except OSError:
        return None


def parse(path, text):
    lines = text.split("\n")
    fm, body_start = {}, 0
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end > 0:
            for ln in text[3:end].split("\n"):
                m = re.match(r"^([A-Za-z0-9_-]+)\s*:\s*(.*)$", ln)
                if m:
                    fm[m.group(1).strip()] = m.group(2).strip()
            body_start = end + 4
    title, title_line = fm.get("title", ""), 0
    for i, ln in enumerate(lines):
        if ln.strip().startswith("# ") and not title:
            title, title_line = ln.strip()[2:].strip(), i + 1
            break
    body = text[body_start:]
    body = re.sub(r"^#[^\n]*\n", "", body, count=1)
    tags = re.findall(r"#([^\s#，。！？,!?]+)", body)
    # 封面引用：frontmatter cover 优先，其次正文第一张图
    cover = fm.get("cover", "")
    if not cover:
        m = re.search(r"!\[[^\]]*\]\(([^)]+)\)", body)
        if m:
            cover = m.group(1).strip()
    cover_path = ""
    if cover and not re.match(r"https?://", cover):
        cover_path = os.path.normpath(os.path.join(os.path.dirname(path), cover))
    return {"lines": lines, "title": title, "title_line": title_line,
            "body": body, "tags": tags, "cover": cover,
            "cover_path": cover_path}


def find_line(lines, needle):
    for i, ln in enumerate(lines):
        if needle in ln:
            return i + 1
    return 0


def audit_text(path, text):
    p = parse(path, text)
    lines, findings = p["lines"], []
    rel = os.path.basename(path)

    def add(rule_id, line, snippet):
        r = _RULE_BY_ID[rule_id]
        findings.append(Finding(
            r["id"], r["severity"], r["category"], r["title"],
            rel, line, snippet[:120], r["detail"]))

    for r in RULES:
        rid = r["id"]
        if "words" in r:
            for w in r["words"]:
                ln_no = find_line(lines, w)
                if ln_no:
                    add(rid, ln_no, lines[ln_no - 1].strip()[:120] + "（命中：%s）" % w)
                    break
        elif "pattern" in r:
            rx = re.compile(r["pattern"])
            for i, ln in enumerate(lines):
                if rx.search(ln):
                    add(rid, i + 1, ln.strip()[:120])
                    break
        elif "count_words" in r:
            total = sum(text.count(w) for w in r["count_words"])
            if total >= r["threshold"]:
                add(rid, 1, "八股词共出现 %d 次（阈值 %d）" % (total, r["threshold"]))
        elif rid == "XHS-TITLE-001":
            if not p["title"]:
                add(rid, 1, "全文无标题")
        elif rid == "XHS-TITLE-002":
            if p["title"] and len(p["title"]) > r["title_max_len"]:
                add(rid, p["title_line"] or 1,
                    "标题 %d 字：%s" % (len(p["title"]), p["title"][:40]))
        elif rid == "XHS-TITLE-003":
            t = p["title"]
            if t and not (any(ch.isdigit() for ch in t)
                          or EMOJI_RE.search(t) or any(c in t for c in "！？?!")):
                add(rid, p["title_line"] or 1, "标题无数字/emoji/悬念符号")
        elif rid == "XHS-TAG-001":
            lo, hi = r["tag_range"]
            if not (lo <= len(p["tags"]) <= hi):
                add(rid, len(lines), "标签 %d 个（要求 %d~%d）" % (len(p["tags"]), lo, hi))
        elif rid == "XHS-TAG-002":
            if len(p["tags"]) != len(set(p["tags"])):
                add(rid, len(lines), "标签重复：%s" % ",".join(p["tags"]))
        elif rid == "XHS-COVER-001":
            if not p["cover"]:
                add(rid, 1, "未找到封面图引用")
        elif rid == "XHS-COVER-002":
            if p["cover_path"] and os.path.isfile(p["cover_path"]):
                size = read_png_size(p["cover_path"])
                if size:
                    ratio, tol = r["cover_ratio"]
                    if abs(size[0] / size[1] - ratio) > tol:
                        add(rid, 1, "封面 %dx%d，比例非 3:4" % size)
                else:
                    add(rid, 1, "封面非 PNG 或无法解析尺寸（仅支持 PNG 校验）")
        elif rid == "XHS-COVER-003":
            if p["cover_path"] and os.path.isfile(p["cover_path"]):
                size = read_png_size(p["cover_path"])
                if size and size != tuple(r["cover_size"]):
                    ratio, tol = _RULE_BY_ID["XHS-COVER-002"]["cover_ratio"]
                    if abs(size[0] / size[1] - ratio) <= tol:
                        add(rid, 1, "封面 %dx%d，非标准 1242×1660" % size)
        elif rid == "XHS-BODY-001":
            n = len(p["body"])
            lo, hi = r["body_range"]
            if n < lo or n > hi:
                add(rid, 1, "正文 %d 字（建议 %d~%d）" % (n, lo, hi))
        elif rid == "XHS-AD-003":
            if "我" not in p["body"]:
                add(rid, 1, "全文无第一人称“我”")

    return findings


def run(target):
    files = collect_files(target)
    findings = []
    for fp in files:
        text = read_text(fp)
        if text.strip():
            findings.extend(audit_text(fp, text))
    return files, findings


def main(argv=None):
    ap = argparse.ArgumentParser(description="lhg-xiaohongshu 确定性合规审计")
    ap.add_argument("--target", default=".", help="笔记文件或目录")
    ap.add_argument("--format", choices=["json", "text"], default="text")
    ap.add_argument("--fail-on", choices=["blocker", "warning", "nit"],
                    default="blocker")
    args = ap.parse_args(argv)

    target = os.path.abspath(args.target)
    if not (os.path.isdir(target) or os.path.isfile(target)):
        print("target 不存在：%s" % args.target, file=sys.stderr)
        return 1

    files, findings = run(target)

    sev_rank = {"blocker": 3, "warning": 2, "nit": 1}
    counts = {"blocker": 0, "warning": 0, "nit": 0}
    for f in findings:
        counts[f.severity] = counts.get(f.severity, 0) + 1

    result = {
        "tool": TOOL,
        "version": VERSION,
        "target": args.target,
        "summary": {
            "files_scanned": len(files),
            "rules_run": len(RULES),
            "blocker": counts["blocker"],
            "warning": counts["warning"],
            "nit": counts["nit"],
        },
        "findings": [f.to_dict() for f in sorted(
            findings, key=lambda x: (-sev_rank.get(x.severity, 0), x.file, x.line))],
    }

    if args.format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        s = result["summary"]
        print("小红书合规审计：扫描 %d 文件，运行 %d 条规则" % (
            s["files_scanned"], s["rules_run"]))
        print("blocker=%d warning=%d nit=%d" % (
            s["blocker"], s["warning"], s["nit"]))
        for f in result["findings"]:
            print("[%s][%s] %s:%d %s" % (
                f["severity"].upper(), f["rule_id"], f["file"], f["line"], f["title"]))
            print("    %s" % f["detail"])
            if f["snippet"]:
                print("    → %s" % f["snippet"])

    level = sev_rank[args.fail_on]
    bad = any(sev_rank.get(f.severity, 0) >= level for f in findings)
    return 2 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
