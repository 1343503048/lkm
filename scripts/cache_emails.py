#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
cache_emails.py — 拉取 QQ 邮箱邮件并按日期逐封落盘为独立文件。

设计目标：
  - 通过 run-qqmail.sh 调用时，凭证（QQ_EMAIL_ACCOUNT / QQ_EMAIL_AUTH_CODE）
    已由 run-qqmail.sh 注入到当前进程环境，这里直接继承即可。
  - 先调用 receive.js 拿到邮件清单（含主题/发件人/日期/UID），
    按 skill 的关键词筛选出与调度子系统相关的候选邮件，
    再用 get-body.js 逐封取回正文，落盘为独立 JSON 文件。
  - 每个日期一个目录：emails/<YYYYMMDD>/<uid>.json，并附带 index.md 便于人工索引；
    同时保留 emails/<YYYYMMDD>.json 合并数组以兼容 skill 原有逻辑。

用法（经 run-qqmail.sh）：
  bash run-qqmail.sh cache-emails --days 2
  bash run-qqmail.sh cache-emails --date 20260726 --root /home/zq/kernel-mail-digest
"""

import argparse
import json
import os
import re
import subprocess
import sys

QQMAIL_DIR = "/home/zq/.codebuddy/skills/QQ邮箱"
DEFAULT_ROOT = "/home/zq/kernel-mail-digest"
DEFAULT_OUT = "sched/.state/emails"

# 调度相关主题关键词（来自 skill 文档的调度子系统关注范围）
# 注意：rt:/cfs 等短词必须加 \b 词边界，否则会误伤 isert:/ocfs2 等无关子系统。
SCHED_KW = re.compile(
    r'\bsched|kernel/sched|proxy exec|sched_ext|perf sched|psi:|'
    r'\[tip: sched|cpuidle|cpufreq|load balanc|\bfair:|\bcfs|\brt:|deadline:',
    re.I,
)
# 内核 bug / 回归关键词（用于捕获可能波及调度的异常报告）
# \bOops\b 避免误伤 "loops" 等。
BUG_KW = re.compile(
    r'\[BUG\]|soft lockup|NULL pointer|\bOops\b|kernel BUG|WARNING|'
    r'regression|rcu stall|deadlock|use-after-free|KASAN',
    re.I,
)


def run_node(script, *args, timeout=120):
    """在 QQ 邮箱脚本目录下执行 node 脚本，返回 stdout。"""
    env = os.environ.copy()
    proc = subprocess.run(
        ["node", os.path.join(QQMAIL_DIR, "scripts", script), *args],
        capture_output=True, text=True, env=env, timeout=timeout,
    )
    if proc.returncode != 0:
        sys.stderr.write(f"[cache-emails] {script} 返回非零: {proc.stderr[:300]}\n")
    return proc.stdout


def parse_listing(text):
    """解析 receive.js 的文本清单，返回邮件元数据列表。"""
    blocks = re.split(r'\n--- (\d+) ---\n', text)
    out = []
    for i in range(1, len(blocks), 2):
        body = blocks[i + 1]
        sm = re.search(r'主题:\s*(.+)', body)
        fm = re.search(r'发件人:\s*(.+)', body)
        dm = re.search(r'日期:\s*(.+)', body)
        um = re.search(r'UID:\s*(\S+)', body)
        if not (sm and fm and dm and um):
            continue
        out.append({
            "subject": sm.group(1).strip(),
            "author": fm.group(1).strip(),
            "date_raw": dm.group(1).strip(),
            "uid": um.group(1).strip(),
        })
    return out


def parse_date(date_raw):
    """将 '2026/7/26 23:53:41' 转换为 (iso, ymd)。无法解析时返回 (原串, None)。"""
    m = re.match(r'(\d{4})/(\d{1,2})/(\d{1,2})\s+(\d{1,2}):(\d{2}):(\d{2})', date_raw)
    if not m:
        return date_raw, None
    y, mo, d, h, mi, s = (int(x) for x in m.groups())
    iso = f"{y:04d}-{mo:02d}-{d:02d}T{h:02d}:{mi:02d}:{s:02d}+08:00"
    return iso, f"{y:04d}{mo:02d}{d:02d}"


def is_candidate(subject):
    return bool(SCHED_KW.search(subject) or BUG_KW.search(subject))


def is_kept(subject, body):
    """取回正文后做最终判定：调度主题直接保留；bug 类需正文也提及 sched。"""
    if SCHED_KW.search(subject):
        return True
    if BUG_KW.search(subject) and "sched" in (subject + body).lower():
        return True
    return False


def main():
    ap = argparse.ArgumentParser(description="拉取邮件并逐封落盘")
    ap.add_argument("--days", type=int, default=2, help="拉取最近 N 天（receive.js --days）")
    ap.add_argument("--date", help="仅缓存该 YYYYMMDD（默认缓存清单内所有日期）")
    ap.add_argument("--root", default=DEFAULT_ROOT, help="项目根目录")
    ap.add_argument("--out", default=DEFAULT_OUT, help="相对 root 的缓存目录")
    ap.add_argument("--limit", type=int, default=99999, help="receive.js 单日上限")
    ap.add_argument("--no-body", action="store_true", help="只写清单不取正文（调试用）")
    args = ap.parse_args()

    out_base = os.path.join(args.root, args.out)
    os.makedirs(out_base, exist_ok=True)

    sys.stderr.write(f"[cache-emails] 拉取清单 --days {args.days} ...\n")
    listing = run_node("receive.js", "--days", str(args.days), "--limit", str(args.limit))
    emails = parse_listing(listing)
    sys.stderr.write(f"[cache-emails] 解析到 {len(emails)} 封邮件\n")

    # 候选筛选（基于主题）
    candidates = [e for e in emails if is_candidate(e["subject"])]
    sys.stderr.write(f"[cache-emails] 候选（主题命中关键词）: {len(candidates)} 封\n")

    by_date = {}
    for e in candidates:
        iso, ymd = parse_date(e["date_raw"])
        e["date"] = iso
        e["ymd"] = ymd
        if args.date and ymd != args.date:
            continue
        if ymd is None:
            continue
        by_date.setdefault(ymd, []).append(e)

    total_saved = 0
    for ymd in sorted(by_date):
        ddir = os.path.join(out_base, ymd)
        os.makedirs(ddir, exist_ok=True)
        kept = []
        for e in by_date[ymd]:
            body = "" if args.no_body else run_node("get-body.js", "--uid", e["uid"]).strip()
            if not args.no_body and not is_kept(e["subject"], body):
                continue
            rec = {
                "msgid": f"<uid-{e['uid']}@qq-imap>",
                "subject": e["subject"],
                "author": e["author"],
                "date": e["date"],
                "uid": e["uid"],
                "body": body,
            }
            with open(os.path.join(ddir, f"{e['uid']}.json"), "w", encoding="utf-8") as f:
                json.dump(rec, f, ensure_ascii=False, indent=2)
            kept.append(rec)
            total_saved += 1
            sys.stderr.write(f"  [cache-emails] {ymd} uid={e['uid']} 已存 ({len(body)} 字节)\n")

        # 合并数组（兼容 skill 原有 emails/<YYYYMMDD>.json）
        with open(os.path.join(out_base, f"{ymd}.json"), "w", encoding="utf-8") as f:
            json.dump(kept, f, ensure_ascii=False, indent=2)
        # 索引（便于人工查找）
        with open(os.path.join(ddir, "index.md"), "w", encoding="utf-8") as f:
            f.write(f"# 邮件缓存索引 {ymd}\n\n")
            f.write(f"共 {len(kept)} 封（独立文件见本目录 `<uid>.json`）\n\n")
            for e in kept:
                f.write(f"- `{e['uid']}` {e['date']} — {e['subject']}  \n")
                f.write(f"  作者: {e['author']}\n")

        # 清理本日期旧的零散 .json 合并文件之外的历史（保留 index.md 与本目录）
        sys.stderr.write(f"[cache-emails] {ymd}: 落盘 {len(kept)} 封 -> {ddir}\n")

    sys.stderr.write(f"[cache-emails] 完成，共保存 {total_saved} 封邮件\n")
    print(json.dumps({"saved": total_saved, "dates": sorted(by_date.keys())}, ensure_ascii=False))


if __name__ == "__main__":
    main()
