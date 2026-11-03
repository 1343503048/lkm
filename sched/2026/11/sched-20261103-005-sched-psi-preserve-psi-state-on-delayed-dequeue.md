# sched/psi: Preserve PSI state on delayed dequeue

## TL;DR

Shubhang Kaushik（Ampere）修 PSI：EEVDF 的 delayed dequeue（`DEQUEUE_DELAYED`）只会「完成」先前已记账的 sleep dequeue，但 `psi_dequeue()` 仍清掉全部 PSI 标志（含 TSK_IOWAIT），导致睡眠压力记账被提前终止、唤醒时 `psi_enqueue()` 期望清理的保留状态落空。修复让 `DEQUEUE_DELAYED` 与 `DEQUEUE_SAVE` 一样保持 PSI 状态不变。单补丁，当日无人回帖。

## 背景与问题

EEVDF 会把阻塞的 fair 任务作为 `sched_delayed` 保留到最终移除前。初次 sleep 时 `psi_dequeue()` 因任务仍 TSK_ONCPU 而什么都不做，`psi_sched_switch(sleep=true)` 把任务从 runnable 转 sleeping 并保留 TSK_IOWAIT 与持久内存 stall 状态。之后 delayed 任务可能在仍 asleep 时被物理移除（`wait_task_inactive() → dequeue_task(DEQUEUE_SLEEP|DEQUEUE_DELAYED)`，或 `switching_from_fair() → dequeue_task(...|DEQUEUE_DELAYED|DEQUEUE_NOCLOCK)`）。`psi_dequeue()` 当前清掉所有 PSI 标志（含 TSK_IOWAIT），尽管任务仍 asleep，使睡眠压力记账提前结束；唤醒时 `psi_enqueue()` 期望清理 TSK_IOWAIT 却扑空，触发 `psi: inconsistent task state` 警告。

## 技术方案

`kernel/sched/stats.h` 中把 `psi_dequeue()` 的提前返回条件从 `if (flags & DEQUEUE_SAVE)` 扩展为 `if (flags & (DEQUEUE_SAVE | DEQUEUE_DELAYED))`，并同步更新注释说明 delayed dequeue 完成的是前一次 sleep dequeue 记账。`Fixes:` 两个历史 commit：`f5aaff7bfa11`、`b7ca5743a260`。

## 版本演进与当前进展

*current_version: v1（2026-11-03 发出，msgid 20261102-psi-delayed-deq-v1-1-8cd517c8fe51@gentwo.org）*。当日无回帖。

## Maintainer 意见与讨论焦点

无维护者表态（刚发出）。

## 合入评估

*likelihood=unknown*。方向清晰、修复最小（+7/−2 行量级），并附 Ampere Altra 80 核上的复现/验证，但尚无任何 reviewer 表态。

## 效果评估

作者在 80-core Ampere Altra 上实测：v7.4-rc1 基线切换 delayed direct-I/O 任务（SCHED_OTHER→SCHED_FIFO）触发 `psi: inconsistent task state`；加补丁后相同测试无 PSI 警告。

## 我可以参与的点

- testing：在其它架构/CONFIG_PSI 配置下复跑 direct-I/O 切换场景，确认无 `psi: inconsistent task state`。
- review：核对 `DEQUEUE_DELAYED` 与 `DEQUEUE_SAVE` 在 PSI 语义上是否完全等价（是否都「不改变 PSI 状态」）。

## 参考链接

- lore thread: https://lore.kernel.org/all/20261102-psi-delayed-deq-v1-1-8cd517c8fe51@gentwo.org/

---
id: sched-20261103-005
date: 2026-11-03
subject: "sched/psi: Preserve PSI state on delayed dequeue"
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: "<20261102-psi-delayed-deq-v1-1-8cd517c8fe51@gentwo.org>"
lore_url: "https://lore.kernel.org/all/20261102-psi-delayed-deq-v1-1-8cd517c8fe51@gentwo.org/"
authors: ["Shubhang Kaushik (Ampere)"]
maintainers_involved: []
current_version: v1
patch_series:
  - version: v1
    msgid: "<20261102-psi-delayed-deq-v1-1-8cd517c8fe51@gentwo.org>"
    date: 2026-11-03
    summary: "psi_dequeue() 对 DEQUEUE_DELAYED 保持 PSI 状态不变（同 DEQUEUE_SAVE）。"
    review_outcome: "刚发出，暂无 review。"
upstream_commit: null
fixes_commit: "f5aaff7bfa11"
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues: []
  next_action: "等 reviewer（PSI，Johannes/Suren 或 sched 维护者）表态。"
contribution_opportunities:
  - kind: testing
    description: "其它架构/CONFIG_PSI 下复跑 direct-I/O 切换场景。"
  - kind: review
    description: "核对 DEQUEUE_DELAYED 与 DEQUEUE_SAVE 在 PSI 语义上是否完全等价。"
generated_at: "2026-11-04T09:00:00+08:00"
source_email_count: 1
related_articles: []
tags: [psi, eevdf]
---