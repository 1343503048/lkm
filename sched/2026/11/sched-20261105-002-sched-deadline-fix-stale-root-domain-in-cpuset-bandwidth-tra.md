# sched/deadline: Fix stale root domain in cpuset bandwidth transfer

## TL;DR

（增量更新，完整脉络见下）Juri Lelli 此前的 4 补丁带宽记账系列（patch 1「Fix stale root domain in cpuset bandwidth transfer」已进 linux-next 为 b4a61fdc19c5）被 Marek Szyprowski 在 Amlogic ODROID-N2 上复现出 CPU hotplug 的 `kernel BUG at kernel/sched/deadline.c:3340`，Ingo 随即把这些修复从 sched/urgent 撤下并要求「严格只发 -stable 可用的修复」。Juri 已将 Marek 引导至 Mathieu Desnoyers 的 v2 系列（见 sched-20261105-001），Marek 实测确认 v2 修复了该崩溃。

## 背景与问题

- sched-20261103-001：Juri Lelli 的 4 补丁系列修复多个 SCHED_DEADLINE dl_bw/total_bw 记账 bug（stale root domain、!queued 切出泄漏、KEEP_PARAMS 换类、zombie 准入），当日由 Ingo 全数合入 tip/sched/urgent，其中 patch 1「Fix stale root domain in cpuset bandwidth transfer」落地为 commit b4a61fdc19c5。

今天的新进展：Marek Szyprowski（Samsung）在 CPU hotplug 压测中发现该修复在 linux-next 上触发内核 BUG。他在 Amlogic Meson G12B 的 ODROID-N2 板（arm64）上执行 `echo 0 >/sys/devices/system/cpu/cpu[1-9]/online` 再 `echo 1 ...` 的 offline/online 循环后复现：`kernel BUG at kernel/sched/deadline.c:3340!`，调用栈 `dl_task_root_domain_cpu+0x44/0x48` 由 `sugov:2` 线程触发，`Internal error: Oops - BUG`。回退 b4a61fdc19c5（连同依赖 commit 41a7968022ca）后问题消失。

## 技术方案

- 原始修复（patch 1）引入 `dl_task_root_domain_cpu()`，用任务 `cpus_mask` 而非过期的 `task_rq(p)->rd` 定位记账所在 root domain。但该函数在任务 affinity 没有任何 active CPU 时 BUG()，CPU hotplug 过程中恰会进入该窗口。

后续方案即 Mathieu Desnoyers 的 v2 系列（sched-20261105-001），其中 patch 5「Do not BUG() on a deadline task with no active CPU allowed」正是把这一处 BUG() 改为安全回退（Juri 对该处给出 Acked-by），并有 patch 15 起记录「记账所在 root domain」的系统性修复。

## 版本演进与当前进展

*current_version: v1（原系列，已被撤）*。本线程今日无新版本，仅讨论：Marek 报告崩溃 → Juri 指向 Mathieu v2 → Marek 确认 v2 整体通过 → Ingo 撤下 sched/urgent 中的该修复并等待更新系列 → Juri 道歉并承诺补上 v2 未覆盖的部分。

## Maintainer 意见与讨论焦点

- **Ingo Molnar**：明确表示「第一补丁就触发崩溃，我已把这些修复从 sched/urgent 暂时移除」，并要求「能否只发严格 -stable 适用的修复子集」——这是本系列能否重新合入的关键分歧。
- **Juri Lelli**：先回应 Marek 让其验证 Mathieu 的 v2；再对 Ingo 表示「抱歉我这份破碎的系列造成的噪音」，并承诺「审阅 v2 并从我的原修复集中补上 v2 未覆盖的部分」。
- **Marek Szyprowski**：给出崩溃日志 + 回退验证；应用 Mathieu v2 整系列后「Everything works fine now」，并给 Tested-by。

## 合入评估

*likelihood=rejected*。原 patch 1（b4a61fdc19c5）已因 hotplug 崩溃被 Ingo 从 sched/urgent 撤下，短期内不会以原样回归。*blocking_issues*：① 原修复在无 active CPU 时 BUG()，需按 Ingo 要求重做为严格 -stable 适用的子集；② 修复责任已转移到 Mathieu 的 v2 系列。*next_action*：Juri 完成对 Mathieu v2 的审阅，并把 v2 未覆盖的原修复不要部分整理成新的、严格 -stable 可用的系列。

## 效果评估

Marek 提供了可复现的证据：ODROID-N2（6 核 big.LITTLE 配置）CPU offline/online 循环即触发 `kernel BUG at kernel/sched/deadline.c:3340`；回退 b4a61fdc19c5 + 41a7968022ca 后消失；应用 Mathieu v2 整系列后 CPU hotplug 测试「everything works fine」。崩溃来自 `dl_task_root_domain_cpu()` 的 BUG_ON，属确定性可复现，非偶发。

## 我可以参与的点

- **testing**：在带 cpuset 分区 + CPU hotplug 的异构（big.LITTLE）平台复跑 offline/online 循环，验证 Mathieu v2 的 patch 5/15-18 是否彻底消除该崩溃。
- **review**：关注 Juri 后续补上的「v2 未覆盖」部分是否仍复现 stale root domain 记账错误。

## 参考链接

- lore thread（patch 1/4）: https://lore.kernel.org/all/20261103-b4-sched-dl-bw-fixes-v1-1-dd761fe005b4@redhat.com/
- Marek 原崩溃报告: https://lore.kernel.org/all/eb0e386b-da07-4a2b-bff3-79441fd6be1f@samsung.com/
- Ingo 撤下公告: https://lore.kernel.org/all/auxm5whgKM-uiSGe@gmail.com/

---
id: sched-20261105-002
date: 2026-11-05
subject: "sched/deadline: Fix stale root domain in cpuset bandwidth transfer"
subsystem: sched
type: regression
status: superseded
severity: critical
thread_root_msgid: "<20261103-b4-sched-dl-bw-fixes-v1-1-dd761fe005b4@redhat.com>"
lore_url: "https://lore.kernel.org/all/20261103-b4-sched-dl-bw-fixes-v1-1-dd761fe005b4@redhat.com/"
authors: [Juri Lelli]
maintainers_involved: [Ingo Molnar, Juri Lelli]
current_version: v1
patch_series:
  - version: v1
    msgid: "<20261103-b4-sched-dl-bw-fixes-v1-1-dd761fe005b4@redhat.com>"
    date: 2026-11-03
    summary: "patch 1/4 修复 cpuset 带宽迁移中的 stale root domain，落地 b4a61fdc19c5。"
    review_outcome: "Marek 复现 hotplug BUG；Ingo 撤下 sched/urgent。"
upstream_commit: "b4a61fdc19c5"
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: rejected
  blocking_issues:
    - "原修复在无 active CPU 时 BUG()，CPU hotplug 可触发"
    - "需重做为严格 -stable 适用的修复子集（Ingo 要求）"
  next_action: "Juri 审阅 Mathieu v2 并重发严格 -stable 可用的更新系列"
contribution_opportunities:
  - kind: testing
    description: "在带 cpuset 分区 + CPU hotplug 的异构平台复跑 offline/online 循环验证修复"
generated_at: "2026-11-06T09:00:00+08:00"
source_email_count: 5
related_articles: [sched-20261103-001]
tags: [deadline, cgroup, regression]
---