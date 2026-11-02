---
type: fix
status: merged_tip
severity: none
thread_root_msgid: <20260819081207.12150-1-hongyan.xia@transsion.com>
authors:
- Hongyan Xia
maintainers_involved:
- Peter Zijlstra
current_version: null
patch_series: []
merge_assessment:
  likelihood: merged
  blocking_issues: []
  next_action: 随 riscv/linux.git 走后续合并流程
contribution_opportunities:
- kind: new_patch
  description: 继续迁移 sched 内残余 deprecated static_key 用法
upstream_commit: a5576ebce920
fixes_commit: null
merged_branch: riscv/linux.git (fixes)
source_email_count: 2
related_articles:
- sched-20260819-003
tags:
- cfs
- x86
- riscv
id: sched-20261102-027
subject: 'sched: Convert paravirt_steal to new static key APIs'
date: '2026-11-02'
subsystem: sched
generated_at: '2026-11-03T01:22:31'
lore_url: null
title: 'sched: Convert paravirt_steal to new static key APIs'
layout: article
---

## TL;DR

Hongyan Xia 的 paravirt_steal 静态 key API 迁移补丁（RESEND 单补丁，亦为「Remove deprecated static key API in scheduler code」0/3 系列的 2/3）已被 Peter Zijlstra 收取，commit `a5576ebce920` 进 riscv/linux.git（fixes）。这是跨月的静态 key 清理工作的收尾：`paravirt_steal_*` 从 deprecated raw `static_key` 迁到 `static_branch_*`，无功能变化。

## 背景与问题

（承接，见 <a class="article-ref" href="/lkm/2026/08/19/sched-20260819-003-sched-migrate-static-key-api-resend.html">sched-20260819-003</a>）`struct static_key` 旧 API 已废弃，`paravirt_steal_{rq_,}enabled` 等仍用旧 API。此前 paravirt 部分已获 Juergen Gross Acked-by，系列拆分后等待收取。

## 技术方案

`paravirt_steal_rq_enabled`/`paravirt_steal_enabled` 迁移到新的 `static_branch_*` API，配合 sched_feat 等的 union 包装方案（详见 prior 文章）。

## 版本演进与当前进展

今日（2026-11-02）patchwork-bot 确认：`[RESEND] sched: Convert paravirt_steal to new static key APIs` 与 `[2/3]` 同补丁均被 Peter Zijlstra 应用于 riscv/linux.git（fixes），commit `a5576ebce920`。

## Maintainer 意见与讨论焦点

Peter Zijlstra 亲自应用，无异议；此前 Juergen Gross Acked paravirt 部分。

## 合入评估

likelihood=merged。已进 riscv/linux.git（fixes），将经 riscv tree 走后续合并。

## 效果评估

无功能变化（API 迁移）。

## 我可以参与的点

- new_patch：继续把 sched 内残余的 deprecated static_key 用法（如 `__cfs_bandwidth_used`、`sched_feat` 之外的残留点）迁移完。

## 参考链接

- commit: https://git.kernel.org/riscv/c/a5576ebce920
- lore thread: https://lore.kernel.org/all/20260819081207.12150-1-hongyan.xia@transsion.com/
