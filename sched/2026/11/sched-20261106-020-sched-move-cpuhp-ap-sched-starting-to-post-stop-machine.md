# sched: Move CPUHP_AP_SCHED_STARTING to post stop_machine()

## TL;DR

Frederic Weisbecker 的 CPU hotplug 重构系列（47 补丁）中的 03/47：把 `CPUHP_AP_SCHED_STARTING` 这个 teardown 回调从「stop_machine 主阶段」挪到新引入的「stop machine post function」（IRQ 仍禁、但其它 CPU 已可退出 stop_machine）。目的是从全局 stop_machine 平滑过渡到更细粒度的 teardown 同步——全局 stop 与运行中的 RT/isolated 任务混不到一起。改动仅在 `kernel/cpu.c`（`take_cpu_down`/`take_cpu_down_post` 的目标状态调整）。

## 背景与问题

CPU 下线阶段，`CPUHP_TEARDOWN_CPU` 到 `CPUHP_AP_OFFLINE` 之间 stop_machine 会停住系统里所有 CPU 执行 teardown 回调，这与正在运行的 RT 任务、isolated 任务「混不好」。作者的方向是从全局 stop_machine 过渡到「teardown 回调与其它 CPU 之间更细粒度的同步」——为此引入一个 post function：在主 stop_machine 之后、IRQ 仍禁用的状态下执行，而此时其它 CPU 已可退出 stop_machine。

## 技术方案

在 `kernel/cpu.c` 中把 `take_cpu_down()` 的 target 从 `CPUHP_AP_CACHECTRL_STARTING` 提到 `CPUHP_AP_SCHED_STARTING`，`take_cpu_down_post()` 的 `WARN_ON` 断言同步调整。作者逐条论证调度 teardown 回调在 post 阶段、其它 CPU 并发时依然安全：nohz_full 远程 tick 可安全关闭；离线时更新 RQ clock 没问题；CPU 已视为 offline、不会再有任务入队；dl server 停止用 rq 锁同步；`hrtimer_try_to_cancel()` 即便变 racy 也会 early return；`calc_load_migrate()` 只是把本地负载并进全局；`update_max_interval()` 只依赖在线 CPU 数（该阶段稳定）；`hrtick_clear()` 处理纯本地 timer；`sched_core_cpu_dying()` 无竞态。

## 版本演进与当前进展

*current_version: v1（2026-11-06 发出，03/47）*。本缓存仅含 03/47（sched 相关）一封，系列 cover 与其余 patch 不在本日 sched 范围内。当日无评审。

## Maintainer 意见与讨论焦点

当日无回复。作者为主调度/内核维护者 Frederic Weisbecker 本人，系列为自研的 hotplug 架构演进方向，无 NAK。

## 合入评估

*likelihood=unknown*。作为 47 补丁系列的一个 sched 片段，需随整个系列一起评审；单独评估意义有限。*blocking_issues*：① 单 patch 无法脱离系列评审；② 无 cover/changelog 在本日范围。*next_action*：观察整系列与 Peter/内核 hotplug 侧评审。

## 效果评估

无性能数据。收益为架构层面：CPU 下线不再全局停住所有 CPU，减少对 RT/isolated 任务的扰动（作者定性描述，未见数据）。

## 我可以参与的点

当前阶段暂无明显参与空间（系列片段、需整体视角），可持续观察该 hotplug 重构系列的后续版本。

## 参考链接

- lore thread: https://lore.kernel.org/all/20261105163045.38862-4-frederic@kernel.org/

---
id: sched-20261106-020
date: 2026-11-06
subject: "sched: Move CPUHP_AP_SCHED_STARTING to post stop_machine()"
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: "<20261105163045.38862-4-frederic@kernel.org>"
lore_url: "https://lore.kernel.org/all/20261105163045.38862-4-frederic@kernel.org/"
authors: [Frederic Weisbecker]
maintainers_involved: []
current_version: v1
patch_series:
  - version: v1
    msgid: "<20261105163045.38862-4-frederic@kernel.org>"
    date: 2026-11-06
    summary: "CPUHP_AP_SCHED_STARTING teardown 挪到 post stop_machine（03/47）。"
    review_outcome: "暂无评审。"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues:
    - "单 patch 无法脱离 47 补丁系列评审"
    - "无 cover/changelog 在本日范围"
  next_action: "观察整系列与 sched/hotplug 侧评审"
contribution_opportunities: []
generated_at: "2026-11-07T09:00:00+08:00"
source_email_count: 1
related_articles: []
tags: [topology]
---