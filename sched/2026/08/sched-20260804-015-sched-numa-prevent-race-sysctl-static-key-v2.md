# sched/numa: Prevent race on sysctl_numa_balancing static key

# sched/numa: 静态键切换竞态修复（v1 推进）

## TL;DR
`sysctl_numa_balancing` 静态键切换竞态（UAF/use-after-uninit，附 syzkaller repro + Fixes）在 08-04 继续推进。这是 08-03-006 的延续，合入可能性 high。

## 背景与问题
NUMA_BALANCING 经 jump_label 在 sysctl 写时切换，切换期间未禁止抢占，若抢占点发生在静态键释放/重分配与后续读取之间，会读到已释放/未初始化内存。详见 08-03-006。

## 技术方案
在静态键切换处加抢占保护并保证写入与读取顺序。附 syzkaller C repro 与 `Fixes: 6604b3a6b7ba`。

## 版本演进与当前进展
- 08-03：v1 发出（08-03-006）。
- 08-04：进入后续讨论/修订。

## Maintainer 意见与讨论焦点
Peter Zijlstra / Mel Gorman 尚未在 08-04 给出最终认可。改法保守，预期无方向反对。

## 合入评估
合入可能性 high。有可复现 race + Fixes + 保守改法，应被快速接收。

## 效果评估
提供 syzkaller repro + KASAN/KCSAN 报告，属「有实证」的 bug 修复。

## 我可以参与的点
- 用 syzkaller C repro 在 KASAN/KCSAN 内核复现并验证补丁后竞态消失，回帖 tested-by。

## 参考链接
- 08-03 文章：sched-20260803-006-sched-numa-prevent-race-on-sysctl_numa_balancing-static-key

---
subject: "sched/numa: Prevent race on sysctl_numa_balancing static key"
id: sched-20260804-015
date: 2026-08-04
subsystem: sched
type: bug
status: under_review
severity: high
thread_root_msgid: "<unknown>"
lore_url: "unknown"
authors: [Chen Jinghuang]
maintainers_involved: [Peter Zijlstra, Mel Gorman]
current_version: v1
patch_series:
  - version: v1
    msgid: "<unknown>"
    date: 2026-08-03
    summary: "sysctl 切换 NUMA_BALANCING 静态键时未禁止抢占，存在 use-after-free/use-after-uninit 竞态，附 syzkaller C repro 与 Fixes: 6604b3a6b7ba。（详见 08-03-006）"
    review_outcome: "08-03-006 已覆盖；08-04 上该系列进入 v1 后续讨论/修订。"
upstream_commit: null
fixes_commit: "6604b3a6b7ba"
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: ["待 maintainer 对『抢占保护 + static key 写顺序』改法的认可"]
  next_action: "等待 PeterZ/Mel 接收。"
contribution_opportunities:
  - kind: testing
    description: "基于作者 syzkaller C repro 在 KASAN/KCSAN 内核复现并验证补丁后竞态消失，回帖 tested-by（08-03-006 已提过，仍是最直接参与点）。"
generated_at: "2026-08-05T00:25:00"
source_email_count: 1
related_articles: ["sched-20260803-006-sched-numa-prevent-race-on-sysctl_numa_balancing-static-key"]
tags: [numa, sched_debug]
---
