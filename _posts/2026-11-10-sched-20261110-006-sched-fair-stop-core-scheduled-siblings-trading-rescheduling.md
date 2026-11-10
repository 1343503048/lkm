---
id: sched-20261110-006
date: '2026-11-10'
subject: 'sched/fair: Stop core-scheduled siblings trading rescheduling IPIs'
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: <20261109194827.87349-1-sieberf@amazon.com>
lore_url: https://lore.kernel.org/all/20261109194827.87349-1-sieberf@amazon.com/
authors:
- Fernand Sieber
maintainers_involved: []
current_version: v1
patch_series:
- version: v1
  msgid: <20261109194827.87349-1-sieberf@amazon.com>
  date: '2026-11-10'
  summary: patch 1 repick 续期 slice 保护；patch 2 新增 core scheduling IPI selftest
  review_outcome: 当日无评审回复
upstream_commit: null
fixes_commit: 0b9ca2dcabc3
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
  - patch 1 repick 续期语义待维护者确认
  next_action: 等待 sched/fair 维护者评审后收敛
contribution_opportunities:
- kind: testing
  description: 在真实 SMT + core scheduling（含 PREEMPT_LAZY=y）复测 repick 续期无副作用
- kind: review
  description: 评估 repick 重武装 vprot 与「protected period 结束要 resched」初衷的兼容性
generated_at: '2026-11-11T09:00:00+08:00'
source_email_count: 3
related_articles: []
tags:
- cfs
- core_sched
- regression
title: 'sched/fair: Stop core-scheduled siblings trading rescheduling IPIs'
layout: article
---

## TL;DR

Fernand Sieber（Amazon）发 2 补丁系列修复 core scheduling 下两个 SMT 兄弟互相发 rescheduling IPI 的回归：自 v6.17 起 commit `0b9ca2dcabc3` 让 `update_curr()` 在保护 slice 过期后每次都要 reschedule，而 `set_protect_slice()` 只在 fresh pick（SNT_PICK）时重新武装；被再次 pick 的实体保留过期的 vprot，之后每次 `update_curr()` 都再要一次 reschedule——core scheduling 下这个「要 reschedule」是跨核远程动作，两兄弟互相 IPI、各自 re-pick 同一个实体、什么都没 renew、又 IPI 回去。patch 1 在 repick 时续期保护，patch 2 加一个 selftest 复现并设阈值（>1000 IPIs/CPU/s 判失败）。补丁含复现数据：4 vCPU QEMU 客户机里无 patch 1 时 7 次运行 6 次失败（808-2123 IPIs/CPU/s），打补丁后 7 次全部通过（224-271）。

## 背景与问题

`set_protect_slice()` 只在 fresh pick（`SNT_PICK`）时重新武装保护期，所以一个被「再次 pick」的实体保留了已过期的 vprot，之后每次 `update_curr()` 对它的调用都会再问一次 reschedule。在 core scheduling 下，core-wide 的 pick 会调用每个兄弟 runqueue 的 `pick_task()`——也就是 `update_curr()`——所以每个兄弟都向对方 IPI，对方 schedule、重新 pick 同一个实体、什么都不 renew、又 IPI 回来，形成数万次/秒的空转 IPI。作者定位起点为 `0b9ca2dcabc3 ("sched/fair: Always trigger resched at the end of a protected period")`。

## 技术方案

patch 1 `sched/fair: Renew slice protection when current is picked again`：在 repick（current 被再次选中）时续期 slice 保护，让后续 `update_curr()` 不再反复要求 reschedule。patch 2 `selftests/sched: Add a core scheduling rescheduling IPI test`：新增 `cs_resched_ipi_test.c`（377 行），用 cookie 标记一个 SMT 对、在每兄弟上跑两个 spinners，超过 1000 rescheduling IPIs/CPU/s 即判失败。作者交代整个系列（含 changelog）在 AI 编码辅助下准备、已全部人工评审与测试。

## 版本演进与当前进展

*current_version: v1（2026-11-10，`<20261109194827.87349-1-sieberf@amazon.com>`）*。当日无评审回复。补丁自带复现与阈值。

## Maintainer 意见与讨论焦点

当日缓存无维护者回复。该回归方向（保护 slice / SNT_PICK 重武装）此前由 Vincent 等维护者参与过，需等其对 repick 续期的语义做确认。无 NAK。

## 合入评估

*likelihood=medium*。修复针对明确回归、带 `Fixes:` 与 selftest、复现数据完整；但触及 `sched/fair` 的 slice protection 核心语义，需维护者确认「repick 也续期」不会影响别的路径。*blocking_issues*：① patch 1 的 repick 续期语义待维护者确认；② selftest 阈值（1000 IPIs/CPU/s）是否合理。*next_action*：等待 sched/fair 维护者评审，确认后续取。

## 效果评估

作者给出 QEMU（`-smp 4,sockets=1,cores=2,threads=2`）复现数据：`CONFIG_SCHED_CORE=y`、`CONFIG_PREEMPT_LAZY=n` 下，无 patch 1 时 7 次运行 6 次失败、IPI 808-2123/CPU/s；打补丁后 7 次全部通过、224-271/CPU/s。

## 我可以参与的点

- **testing**：在真实 SMT + core scheduling 环境复测（尤其 `CONFIG_PREEMPT_LAZY=y` 变体），验证 repick 续期不会引入新的调度行为差异。
- **review**：评估 patch 1「repick 也重武装保护期」对 EEVDF vprot 语义是否有副作用（与「protected period 结束要 resched」的初衷是否冲突）。

## 参考链接

- lore thread: https://lore.kernel.org/all/20261109194827.87349-1-sieberf@amazon.com/
