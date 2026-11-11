---
id: sched-20261111-001
date: '2026-11-11'
subject: 'sched: RT throttling cleanup and a bit of documentation'
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: <20261110-sched_dl-v2-0-cc9399f7aeb1@linutronix.de>
lore_url: https://lore.kernel.org/all/20261110-sched_dl-v2-0-cc9399f7aeb1@linutronix.de/
authors:
- Sebastian Andrzej Siewior
maintainers_involved:
- Paul E. McKenney
- Randy Dunlap
current_version: v2
patch_series:
- version: v1
  msgid: <20261105164724.yxONBd03@linutronix.de>
  date: '2026-11-05'
  summary: 从 RFC 改为正式系列，先标记 RT_GROUP_SCHED broken 再解耦 DL 接口
  review_outcome: Tejun 与 Peter Zijlstra 要求先标记 broken
- version: v2
  msgid: <20261110-sched_dl-v2-0-cc9399f7aeb1@linutronix.de>
  date: '2026-11-10'
  summary: 新增 sysfs per-CPU fair_server 旋钮、DL 准入控制迁 sysfs、rcutorture 迁移
  review_outcome: Paul McKenney 认可但指出 divide-by-zero 未解；Randy Dunlap 文档 nit
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
  - Paul McKenney 报告的 rcutorture divide-by-zero 问题在 v2 中是否修复尚未确认
  next_action: 作者确认并修复 divide-by-zero，回复 Paul McKenney
contribution_opportunities:
- kind: testing
  description: 复现 Paul McKenney 报告的 divide-by-zero 并验证 v2 是否修复
- kind: review
  description: 审阅 /sys/kernel/sched/cpuX/fair_server_* sysfs ABI 的单位与命名（作者提出可改用 ns）
generated_at: '2026-11-12T09:00:00+08:00'
source_email_count: 10
related_articles: []
tags:
- rt
- dl_server
- rt_bandwidth
- cgroup
title: 'sched: RT throttling cleanup and a bit of documentation'
layout: article
---

## TL;DR

Sebastian Andrzej Siewior（PREEMPT_RT 维护者）发 v2 七补丁系列，梳理 RT throttling 机制遗留的历史包袱：把 CONFIG_RT_GROUP_SCHED 标记为 broken（作者想直接删除但未被允许）、把 SCHED_DEADLINE 的准入控制从 `sched_rt_{period,runtime}_us` 解耦并迁到 `/sys/kernel/sched/dl_{period,runtime}_us`、把 rcutorture 从 procfs 接口迁移走、新增 `/sys/kernel/sched/cpuX/fair_server_{period,runtime}` 的 per-CPU sysfs 接口，并顺带更新文档。今日 Paul E. McKenney 回复「Nice」但指出该系列仍带着此前已报告的 divide-by-zero 问题，Randy Dunlap 提了一处文档措辞 nit，作者已当场修正。

## 背景与问题

自 v6.12 起，写 `-1` 到 `/proc/sys/kernel/sched_rt_runtime_us` 已经不再真正关闭 RT throttling——该机制早被 fair_server（一个 SCHED_DEADLINE server）接管，而 fair_server 却只能经 debugfs 配置。这一点几乎没有文档记录，只在 `Documentation/scheduler/sched-rt-group.rst` 里以「你得先知道要找什么」的方式带过。更糟的是，全局 DL 资源控制（SCHED_DEADLINE 的准入控制）仍与 RT 共用同一个 proc 文件，而当 `CONFIG_RT_GROUP_SCHED` 启用时这个 proc 文件会被卡死（stuck）无法修改，导致 DL 准入控制实际上只能靠写 `-1` 来禁用。CONFIG_RT_GROUP_SCHED 本身在 cgroup v2 下无法给任务组分配 runtime（根组已占满全部 runtime），所有主流发行版（Debian/OpenSUSE/Fedora/Arch）都已默认禁用，作者认为它「烂到无法修复」，正等待 HCBS（hierarchical constant bandwidth server）这类后继方案取代它。

## 技术方案

七补丁，一条线：先「标记 broken」阻断新用户，再把 DL 与 RT 的接口解耦，最后把 fair_server 配置搬到稳定的 sysfs ABI 下：

1. `sched: Mark RT_GROUP_SCHED broken`——`depends on CGROUP_SCHED && BROKEN`，把仅在 RT_GROUP_SCHED 下使用的代码（含 `RT_RUNTIME_SHARE`）收进对应 IFDEF，并更新文档措辞。
2. `rcutorture: Don't try to disable to RT throttling`（本封未在缓存中，系列由 cover 列出）。
3. `sched: rcutorture: Allow to disable DL fair_server`——新增 `dl_server_fair_disable()`，仅供 built-in 的 rcutorture 关闭 fair_server（该测试结束后随即重启，没必要保留）。
4. `sched: Move DL's admission control to sysfs`——把 `global_rt_period()/global_rt_runtime()` 替换为 `sysfs_dl_period/sysfs_dl_runtime`，暴露 `/sys/kernel/sched/dl_{runtime,period}_us`，从 `sched_rt_handler()` 中移除 `sched_domains_mutex.*` 与 `rebuild_sched_domains()`。
5. `sched: Limit sysctl sched_rt_{period|runtime}_us to RT_GROUP_SCHED`——把这两个 sysctl 收进 RT_GROUP_SCHED，避免「改了却不生效」误导用户。
6. `sched: Add sysfs files for the per-CPU fair_server knobs`——每个 rq 加 kobject，暴露 `/sys/kernel/sched/cpuX/{fair_server_period,fair_server_runtime}`，复用 debugfs 的 set 逻辑。
7. `Documentation/sched: Add fairserver to sched-deadline`——把 fair_server 与新增 sysfs 旋钮写进文档。

## 版本演进与当前进展

*current_version: v2（2026-11-10，`<20261110-sched_dl-v2-0-cc9399f7aeb1@linutronix.de>`）*。v1→v2：按 Tejun 与 Peter Zijlstra 的要求，先把「标记 CONFIG_RT_GROUP_SCHED broken」作为 patch 1 独立前置，其余 patch 依次排后。更早的 RFC→v1：作者最初尝试直接删除 RT_GROUP_SCHED，未获允许后改为「标记 broken」。

## Maintainer 意见与讨论焦点

- **Paul E. McKenney（rcutorture 维护者）**：认可方向（「Nice, thank you!」），但指出该系列仍带着此前（延迟）报告的同一 divide-by-zero 问题（引用 `e58e48c3-ac62-40cd-b5d3-2de87db12496@paulmck-laptop` 线程），尚未解决。
- **Randy Dunlap（文档维护者）**：对 patch 1 的 WARNING 段给了一处 `-ENOPARSE` 的措辞歧义（「If you don't use or schedule real-time tasks...」语义不清），作者当场改写成「If you don't use RT-group scheduling, schedule real-time tasks and experience throttling issues...」。
- 无 NAK。主要未解决项是 Paul 提出的 divide-by-zero（作者尚未在当日回复是否已修）。

## 合入评估

*likelihood=medium*。方向获认可、且与作者「RT_GROUP_SCHED 该废弃」的长期路线（HCBS 取代）一致，但 Paul McKenney 明确点出还有一个未解决的 divide-by-zero 问题，需先厘清才能继续推进。*blocking_issues*：Paul 报告的 rcutorture divide-by-zero（是否已在 v2 中修复未在当日邮件中确认）。*next_action*：作者确认/修复 divide-by-zero 并回复 Paul；可能需等 HCBS（RFC v7，另见 20261110-007）路线明朗后再决定 RT_GROUP_SCHED 去留。

## 效果评估

暂无性能数据。作者从 ABI 语义角度说明动机：procfs 旋钮「改了却不生效」对用户是误导，迁到 sysfs 并限定作用域后行为可预期；`_us` 单位保留旧语义，作者注明「可以改 ns，但先保留 _us」。

## 我可以参与的点

- **testing**：复现 Paul McKenney 报告的 divide-by-zero（rcutorture 场景下禁用/重建 fair_server 或写 DL 准入控制），确认 v2 是否已修复并在线程里回帖结果。
- **review**：审阅 patch 6 新增 sysfs ABI（`/sys/kernel/sched/cpuX/fair_server_{period,runtime}`）的命名与单位语义——cover 里作者自己提出「是否应改用 ns」，这是个明确的接口设计讨论点。

## 参考链接

- lore thread: https://lore.kernel.org/all/20261110-sched_dl-v2-0-cc9399f7aeb1@linutronix.de/
- v1: https://lore.kernel.org/all/20261105164724.yxONBd03@linutronix.de/
- RFC: https://lore.kernel.org/all/20261023161348.t3lpPLQZ@linutronix.de/
- Paul McKenney 报告的 divide-by-zero: https://lore.kernel.org/all/e58e48c3-ac62-40cd-b5d3-2de87db12496@paulmck-laptop/
