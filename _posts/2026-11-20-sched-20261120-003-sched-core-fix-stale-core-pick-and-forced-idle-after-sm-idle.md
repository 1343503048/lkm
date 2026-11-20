---
id: sched-20261120-003
date: '2026-11-20'
subject: 'sched/core: Fix stale core_pick and forced idle after SM_IDLE fast path'
subsystem: sched
type: bug
status: under_review
severity: high
thread_root_msgid: <20261120105822.7770-1-lshahed@amazon.de>
lore_url: https://lore.kernel.org/all/20261120105822.7770-1-lshahed@amazon.de/
authors:
- Ibrahim Elshahed
maintainers_involved:
- Peter Zijlstra
current_version: v2
patch_series:
- version: v1
  msgid: <20261117142704.6878-1-lshahed@amazon.de>
  date: '2026-11-17'
  summary: 2 补丁：修 SM_IDLE fast path 后 core_pick/forced-idle 状态残留
  review_outcome: Peter 质疑 patch 2 条件冗余、建议补 selftests
- version: v2
  msgid: <20261120105822.7770-1-lshahed@amazon.de>
  date: '2026-11-20'
  summary: 3 补丁：按 Peter 意见去条件冗余、新增 selftest
  review_outcome: 待 Peter 复审
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
  - v2 待 Peter 复审
  next_action: Peter 复审 v2，确认后进 tip/sched/core 或 urgent
contribution_opportunities:
- kind: review
  description: 核对 patch 2 非 forceidle 场景的选择语义副作用与 selftest UAF 捕获充分性
- kind: testing
  description: 真实 SMT 硬件与 mwait/poll idle 状态下复跑 cs_forceidle_test
generated_at: '2026-11-21T09:00:00+08:00'
source_email_count: 216
related_articles:
- sched-20261118-002
tags:
- core_sched
- crash
- hyperthreading
title: 'sched/core: Fix stale core_pick and forced idle after SM_IDLE fast path'
layout: article
---

## TL;DR

本文为增量更新，完整脉络见下。

- <a class="article-ref" href="/lkm/2026/11/18/sched-20261118-002-sched-core-fix-stale-core-pick-and-forced-idle-after-sm-i.html">sched-20261118-002</a>：Ibrahim Elshahed（Amazon）发两补丁系列修复 core scheduling 的 SM_IDLE fast path 下 `rq->core_pick` 与 forced-idle 状态残留；Peter Zijlstra 质疑 patch 2 条件冗余、建议补 selftests。
- <a class="article-ref" href="/lkm/2026/11/20/sched-20261120-003-sched-core-fix-stale-core-pick-and-forced-idle-after-sm-idle.html">sched-20261120-003</a>（今天）：**v2 发出，扩为 3 补丁**，按 Peter 意见重做：patch 1 在 dequeue 时清 `rq->core_pick`，patch 2 丢弃原 `rq->core_pick` 检查、改为「forced idle 时 idle CPU 不走 SM_IDLE fast path」，patch 3 新增 selftest。作者给出完整测试矩阵（复现 oops/UAF、无补丁下崩溃、有补丁下 0 stall）。此前的 UAF 现可稳定复现并已被 v2 修复。

## 背景与问题

core scheduling（SMT 隔离）下，core-wide 选择会把 pick 留到 idle sibling 的 `rq->core_pick` 并强制另一 sibling idle。若被选任务在 idle sibling 调度前被迁移走、且那是它唯一任务，SM_IDLE fast path（v6.12+）会让该 sibling 无 pick 地回 idle——core 随后带着残留状态强制 idle、无事可跑，且 forced-idle 记账继续使用过期指针，甚至在任务与其 cgroup 释放之后仍读写（UAF）。v1 两补丁：修复 fast path 后残留 `core_pick` 状态、避免 idle 重入队时跳过待处理 core-wide pick。

## 技术方案

v2 三补丁（`base-commit: d7e670601af6`）：

- **patch 1/3** `Clear a stale rq->core_pick after dequeue`：被选任务 dequeue 时清 `rq->core_pick`。
- **patch 2/3** `Don't take the idle fast path while the core is forced idle`：丢弃 v1 的 `rq->core_pick` 检查（Peter 指出有 patch 1 后 pending pick 必在其 rq 上、空 runqueue 必无 pick），仅按 `core_forceidle_count` 判定；改标题与 changelog。
- **patch 3/3** `selftests/sched: Add a test for stuck forced idle under core scheduling`：由复现器派生的新 selftest（471 行），检查 stuck forced idle，且带 cgroup v2 + schedstats 时逐个释放 stall 任务以捕获 UAF。

## 版本演进与当前进展

*current_version: v2（2026-11-20，`<20261120105822.7770-1-lshahed@amazon.de>`，3 补丁）*。v1（2 补丁，2026-11-17）→ v2（3 补丁）：patch 2 按 Peter 意见去掉条件冗余、加 patch 3 selftest、更新标题/changelog。

## Maintainer 意见与讨论焦点

- **Peter Zijlstra（sched maintainer）**：v1 时质疑 patch 2 的 `rq->core_pick` 条件冗余、建议补 selftests；v2 作者已全盘采纳（`<20261120104108.73673-1-lshahed@amazon.de>`「Right, the check only mattered without patch 1. I'll drop it in v2 and keep only core_forceidle_count.」）。
- 无 NAK；方向（修 fast path 状态残留 + UAF）明确，v2 回应了全部既有意见。

## 合入评估

*likelihood=medium*。补丁覆盖了「UAF + stuck forced idle」两类问题、测试矩阵完备，且回应了 Peter 的既有意见；但 v2 今日刚发出、尚未见 Peter 对 v2 的复审表态。*blocking_issues*：v2 待 Peter 复审。*next_action*：Peter 复审 v2，确认后进入 tip/sched/core（或 urgent）。

## 效果评估

作者给出量化测试（tip sched/core `d7e670601af6`、schedstats=enable）：KVM guest 2c×2t、无补丁时两次 boot 都在 `__cgroup_account_cputime_field()` oops；v2 6 次 240s boot（972562 次尝试）无 stuck forced idle、无 oops，no-migrate 对照（194596 次）干净。`cs_forceidle_test`：无补丁 11 次全崩（0.4-2.2s 内，KASAN 下首发 slab-UAF in `__account_forceidle_time()`），v2 10/10 通过 0 stall、dmesg 干净；单独 patch 1 仍有 42/43/34 stall、patch 2 单独 0 stall。

## 我可以参与的点

- **review**：核对 patch 2 的「forced idle 时跳过 SM_IDLE fast path」是否在非 forceidle 场景带来选择语义副作用；复核 selftest 对 UAF 的捕获是否充分。
- **testing**：在真实 SMT 硬件（非 KVM 2c×2t）与不同 idle 状态（mwait/poll）下复跑 `cs_forceidle_test`。

## 参考链接

- lore thread（v2 cover）: https://lore.kernel.org/all/20261120105822.7770-1-lshahed@amazon.de/
- v1 cover: https://lore.kernel.org/lkml/20261117142704.6878-1-lshahed@amazon.de/
