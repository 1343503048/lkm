# sched: fix typos and repeated words in comments

## TL;DR

本文为增量更新，两个补丁各自改什么的完整分析见 related_articles 中的 sched-20260907-016。09-09 01:13 这条线落地了：Tejun Heo 回 `[PATCH 0/2]` 封面「Applied 1-2 to sched_ext/for-7.4」，两枚纯注释修正全部被收下，等待随 sched_ext 的 7.4 合并窗口进主线。从发出到收取只用了约 18 小时，且全程没有任何 review 争议。

## 背景与问题

Hemanth Selam 用 `checkpatch.pl` + `scripts/spelling.txt` 扫出调度器注释里的两类文字缺陷：`kernel/sched/ext/ext.c` 两处把 "up to" 写成 "upto"，以及 `tools/sched_ext/include/scx/common.bpf.h` 里一个重复的 "be"。不影响任何代码路径，属纯代码质量改进。作者刻意每处独立成补丁，便于维护者单独丢弃。

## 技术方案

1/2 改 `bypass_lb_node()` 注释与 `scx_bpf_dispatch` kfunc 注释里的 "upto" → "up to"；2/2 删掉 `tools/sched_ext/include/scx/common.bpf.h` 中重复的 "be"。合计 2 files changed, 3 insertions(+), 3 deletions(-)。作者说明标识符相关的词故意不动，并给出等价性验证方法（删注释 + 字符串占位 + 压缩空白后比对前后源码）。

## 版本演进与当前进展

- v1（09-07 14:49 发出，封面 `<20260907064943.25304-1-hemanth.selam@gmail.com>`）。
- 09-09 01:13 Tejun Heo 回帖 "Applied 1-2 to sched_ext/for-7.4."（`<178888758275.2.6189775612518482207@kernel.org>`），两枚一并收取，无 v2。

## Maintainer 意见与讨论焦点

Tejun Heo 直接收取，未提出任何修改要求，也没有其他人回帖。09-07 那篇里我提的两个观察（同作者当天另有多个同类拼写系列、`Assisted-by: Cursor:claude-opus-5` 标注是否会被挑）本日都没有被提及——维护者对这两点均未表态，按事实记录。

## 合入评估

`likelihood=merged`。已进 `sched_ext/for-7.4` topic 分支，剩下的只是随该分支合入 mainline 的时间问题。风险接近零：改动全在注释，无功能影响。

## 效果评估

无效果数据，也不需要——纯注释改动，作者自陈无任何代码变化并给出了源码等价性验证方法。

## 我可以参与的点

当前阶段无参与空间：系列已收讫。可延续的做法是把作者这套「checkpatch + spelling.txt，每处独立成补丁，并附删注释后源码等价性证明」的流程用在自己分支的注释修正上——这类补丁收取率高、成本极低。

## 参考链接

- 封面与收取回帖: https://lore.kernel.org/all/20260907064943.25304-1-hemanth.selam@gmail.com/
- Tejun Heo "Applied 1-2 to sched_ext/for-7.4": https://lore.kernel.org/all/178888758275.2.6189775612518482207@kernel.org/
- tip-bot commit: 未获取到
- stable backport: 未获取到

---
id: "sched-20260909-002"
date: "2026-09-09"
subject: "sched: fix typos and repeated words in comments"
subsystem: sched
type: fix
status: merged_tip
severity: none
thread_root_msgid: "20260907064943.25304-1-hemanth.selam@gmail.com"
lore_url: "https://lore.kernel.org/all/178888758275.2.6189775612518482207@kernel.org/"
upstream_commit: null
fixes_commit: null
merged_branch: "sched_ext/for-7.4"
current_version: v1
generated_at: "2026-09-10T00:40:00"
authors:
  - "Hemanth Selam"
maintainers_involved:
  - "Tejun Heo"
patch_series:
  - version: v1
    msgid: "20260907064943.25304-1-hemanth.selam@gmail.com"
    date: "2026-09-07"
    summary: "2 补丁纯注释修正：1/2 把 kernel/sched/ext/ext.c 两处 upto 改为 up to，2/2 删除 tools/sched_ext/include/scx/common.bpf.h 中重复的 be；2 files changed, 3 insertions(+), 3 deletions(-)。"
    review_outcome: "09-09 01:13 Tejun Heo 回复 Applied 1-2 to sched_ext/for-7.4，两枚全部收取，无修改要求。"
merge_assessment:
  likelihood: merged
  blocking_issues: []
  next_action: "无需进一步动作，等待 sched_ext/for-7.4 随合并窗口进入 mainline"
contribution_opportunities: []
source_email_count: 1
related_articles:
  - "sched-20260907-016"
tags:
  - "sched_ext"
---
