# sched/stats: Fix run_delay over-count for proxy-migrated blocked donors

## TL;DR

本文为增量更新，完整脉络见 related_articles。

- sched-20261101-005：Wei Yang 修 proxy execution 下 blocked donor 迁移后 `/proc/<tid>/schedstat` run_delay 重复计数，并建议把 DELAY_DEQUEUE 与 proxy 两处拆独立补丁以便 backport。
- sched-20261102（今天）：作者回帖给出更全实测（v6.12.115 内核、带与不带 v4），证明未打补丁时 run_delay 多计约 147.98ms、打补丁归 0；并强调 DELAY_DEQUEUE 过度计数**与 proxy exec 无关**（v6.12 无 proxy），`p->is_blocked` 只存在于 v7.2+，两者合一会使 v6.12.y..v7.1.y 完全无修复。

## 背景与问题

（承接）run_delay 反映任务等待 CPU 时间，proxy/DELAY_DEQUEUE 均会重复累计。今日进一步坐实「DELAY_DEQUEUE 过度计数独立于 proxy exec」：v6.12 根本没有 proxy，故该部分与 proxy 修复必须拆开。

## 技术方案

（承接）无新代码；作者补充了四组对照数据支持「拆成两补丁」的既有主张，并提出 `p->is_blocked` 版本无法在 6.12 构建——合一会导致 6.12.y 到 7.1.y 无修复。

## 版本演进与当前进展

v1 未更新；今日为补充测试证据与 backport 论证。

## Maintainer 意见与讨论焦点

无维护者表态；作者数据完备、论点清晰，等待 sched 维护者决定拆分/收取。

## 合入评估

likelihood=medium。测试数据完整、拆分理由充分，但仍无 maintainer ACK。

## 效果评估

四组数据：6.12.115 未打 patched run_delay delta 147.98-147.99ms（hit 8/20）、+v4 归 0（0/100）；v7.3+ master 未打补丁 147.94-147.99ms（5/20）、+diff 归 0（0/100）。delta 与 worker 自身 `t_wake - t_migrate`（147.99 vs 148.00ms）吻合，证明整段 sleep 被charge。

## 我可以参与的点

- review：评估「拆 DELAY_DEQUEUE/proxy 两 patch + 各自 Fixes」的 backport 策略是否合理。
- testing：在 6.12.y 与 7.x 上按作者 reproducer 复核 run_delay 归零。

## 参考链接

- lore thread: https://lore.kernel.org/all/20261101143101.353033-1-albin_yang@163.com/

---
type: fix
status: under_review
severity: medium
thread_root_msgid: <20261101143101.353033-1-albin_yang@163.com>
authors:
- Wei Yang
maintainers_involved: []
current_version: v1
patch_series: []
merge_assessment:
  likelihood: medium
  blocking_issues:
  - 无 maintainer ACK；是否拆分补丁未定
  next_action: 作者按 DELAY_DEQUEUE/proxy 拆分补丁并标注各自 Fixes
contribution_opportunities:
- kind: review
  description: 评估拆分与 Fixes/backport 策略
- kind: testing
  description: 6.12.y/7.x 上复核 run_delay 归零
upstream_commit: null
fixes_commit: null
merged_branch: null
source_email_count: 1
related_articles:
- sched-20261101-005
tags:
- proxy_execution
- eevdf
- sched_debug
id: sched-20261102-012
subject: 'sched/stats: Fix run_delay over-count for proxy-migrated blocked donors'
date: '2026-11-02'
subsystem: sched
generated_at: '2026-11-03T01:22:31'
lore_url: null
---
