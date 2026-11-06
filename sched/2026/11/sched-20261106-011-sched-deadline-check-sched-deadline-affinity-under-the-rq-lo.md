# sched/deadline: Check SCHED_DEADLINE affinity under the rq lock

## TL;DR

Andrea Parri 修复 sched_setaffinity 与 sched_setattr(SCHED_DEADLINE) 的竞态：二者并发作用在同一任务上时可能**双双成功**——setattr 把任务设成 SCHED_DEADLINE、setaffinity 把其 affinity 缩窄到比 root domain 还小，得到一个「affinity 窄于 root domain」的 deadline 任务（本应 setaffinity 报 -EBUSY 或 setattr 报 -EPERM）。修复把 `dl_task_check_affinity()` 挪进 `__set_cpus_allowed_ptr_locked()`、与准入检查同锁，并以 `SCA_DL_CHECK` 标志限定其仅对 `__sched_setaffinity()` 生效。作者带 100 万轮复现程序：修前约 92-98 万轮双双成功，修后 0 轮。已带 `Fixes`/`Cc: stable`，可独立于 Mathieu 的 deadline 系列合入（但 SCA_ 标志位与其 patch 16 冲突需错位）。

## 背景与问题

`__sched_setaffinity()` 在 `__set_cpus_allowed_ptr()` 取 task_rq_lock **之前**就调 `dl_task_check_affinity()`，而 `__sched_setscheduler()` 的准入检查与策略切换在一个 task_rq_lock 内完成——于是两个调用都能各自通过检查：CPU1 先看到任务非 DL 而放行缩窄，CPU2 在 CPU1 取锁前把任务设成 SCHED_DEADLINE，最后任务以「窄 affinity + DL 类」收场。作者复现：一个线程把睡眠任务缩窄到 CPU0、另一个把它设成 SCHED_DEADLINE，三次 boot 各有 923514/959547/983997（共 100 万轮）轮两端都成功。

## 技术方案

把 deadline affinity 检查移入 `__set_cpus_allowed_ptr_locked()`（紧挨 `PF_NO_SETAFFINITY` 复查处、与准入检查同锁），谁后取到 task_rq_lock 谁就看到对方的结果。新增 `SCA_DL_CHECK` 标志（值 0x10）选择性地启用该检查：仅 `__sched_setaffinity()` 置位，`relax_compatible_cpus_allowed_ptr()` 沿用检查，其它调用方不启用；`__sched_setaffinity()` 在与 cpuset 更新竞速后的第二条 `__set_cpus_allowed_ptr()` 前清掉 `SCA_DL_CHECK`，保证 cpuset mask 仍赢。改动 3 文件 +19/-5 行。作者并给第二个复现程序验证 cpuset retry 路径。

## 版本演进与当前进展

*current_version: v1（2026-11-06 发出）*。作者说明与 Mathieu 的 deadline 系列 patch 16 存在 SCA_ 标志位冲突（都占了 0x10，后进者需取下一个空闲位）。补丁适用于 v6.18+，更老的 stable 需手工 backport（v6.12 上下文不同、v6.11 前 hunk 在 core.c、v6.2 前无 `affinity_context`）。

## Maintainer 意见与讨论焦点

当日无维护者回复。作者标注 `Reported-by: Sebastian Andrzej Siewior`（Sebastian 在审阅 [1] 时报告），并说明「两个补丁相互独立、可任意顺序应用」。无 NAK。

## 合入评估

*likelihood=medium*。补丁自带完整复现与修复后 0 回归数据、`Fixes`/`Cc: stable` 齐全、可独立合入，但需与 Mathieu deadline 系列的 SCA_ 标志位错开，且当日尚无维护者表态。*blocking_issues*：① SCA_ 标志位 0x10 与 Mathieu patch 16 冲突需协调；② 无维护者审阅。*next_action*：等待 Juri/Peter 审阅，并与 Mathieu 系列就 SCA_ 位错开达成一致。

## 效果评估

作者数据（4-CPU x86_64 guest，每 boot 100 万轮、三次 boot）：修前双双成功 923514/959547/983997 轮；修后 0 轮，且 sched_setaffinity 输掉时按预期返回 -EBUSY。cpuset retry 验证：修前 10 boot 中 8 次任务被留在已丢弃的 CPU3，修后 0/100000 轮（每 boot，10 boot）。lockdep 与 PREEMPT_RT 下均无告警。未覆盖 arm64 非对称 32 位 `relax_compatible_cpus_allowed_ptr()` 路径。

## 我可以参与的点

- **review**：审阅 `SCA_DL_CHECK` 的置位/清除时机（尤其 cpuset retry 路径）与 arm64 非对称路径未测的缺口。
- **testing**：在 arm64 非对称 32 位系统上验证 `relax_compatible_cpus_allowed_ptr()` 路径。

## 参考链接

- lore thread: https://lore.kernel.org/all/20261105164856.29698-1-parri.andrea@gmail.com/
- 补丁内引用 [1]（Sebastian 的触发报告）: https://lore.kernel.org/20261103081149.DuyWNhVe@linutronix.de

---
id: sched-20261106-011
date: 2026-11-06
subject: "sched/deadline: Check SCHED_DEADLINE affinity under the rq lock"
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: "<20261105164856.29698-1-parri.andrea@gmail.com>"
lore_url: "https://lore.kernel.org/all/20261105164856.29698-1-parri.andrea@gmail.com/"
authors: [Andrea Parri]
maintainers_involved: []
current_version: v1
patch_series:
  - version: v1
    msgid: "<20261105164856.29698-1-parri.andrea@gmail.com>"
    date: 2026-11-06
    summary: "dl_task_check_affinity 移入 rq lock 下，以 SCA_DL_CHECK 限定。"
    review_outcome: "暂无维护者回复；带完整复现与修后 0 回归数据。"
upstream_commit: null
fixes_commit: "332ac17ef5bf"
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
    - "SCA_ 标志位 0x10 与 Mathieu deadline 系列 patch 16 冲突需协调"
    - "无维护者审阅"
  next_action: "等待 Juri/Peter 审阅并与 Mathieu 系列错开 SCA_ 位"
contribution_opportunities:
  - kind: testing
    description: "在 arm64 非对称 32 位系统验证 relax_compatible_cpus_allowed_ptr 路径"
  - kind: review
    description: "审阅 SCA_DL_CHECK 置位/清除时机与 cpuset retry 路径"
generated_at: "2026-11-07T09:00:00+08:00"
source_email_count: 1
related_articles: []
tags: [deadline, affinity]
---