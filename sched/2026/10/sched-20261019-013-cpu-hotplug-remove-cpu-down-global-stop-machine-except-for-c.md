# cpu/hotplug: Remove cpu_down() global stop_machine() except for CPUHP_TEARDOWN_CPU itself

## TL;DR

Frederic Weisbecker 发往 lkml 的大规模 RFC（49 补丁）：把 CPU down 路径里所有 teardown 回调从全局 stop_machine 移入一个新「post stop_machine」阶段——stop_machine 主函数跑完后、其它 CPU 可退出的同时、IRQ 仍关闭地执行，从而消解「teardown 阶段停掉全系统 CPU」与 RT/隔离任务的不兼容。调度相关为 03/49（sched CPUHP_AP_SCHED_STARTING）、05/49（cpuidle）、46/49（tick-sched 简化）。当日新发，暂无回帖。

## 背景与问题

在 `CPUHP_TEARDOWN_CPU` 与 `CPUHP_AP_OFFLINE` 之间，stop_machine 停掉全系统所有 CPU 来执行每个 teardown 回调。这与运行中的 RT 或隔离（isolated）任务天然冲突——down 一个 CPU 要短暂打断全机。目标是平滑过渡到「teardown 回调与其它 CPU 之间更细粒度同步」，最终除 `CPUHP_TEARDOWN_CPU` 本身外移除全局 stop_machine。

## 技术方案

49 补丁按子系统逐个把 teardown 回调移到 post stop_machine 阶段（新增 stop_machine post 函数，在主函数之后、IRQ 仍关闭时执行，其它 CPU 可退出 stop_machine）。sched/idle/tick 相关：

- **03/49 sched: Move CPUHP_AP_SCHED_STARTING to post stop_machine()**：作者逐条论证安全——nohz_full 远程 tick 可并发关、离线时改 RQ clock 无碍、离线后无任务可被远程入队、dl server stop 已用 rq 锁同步、`calc_load_migrate()` 只是折叠到全局、`update_max_interval()` 只依赖稳定的 online CPU 数、`hrtick_clear()` 纯本地、`sched_core_cpu_dying()` 无竞态。
- **05/49 cpuidle: Move CPUHP_AP_CPU_PM_STARTING post stop_machine()**：该 teardown 回调只碰本地数据与本地 power 设备（持 power 锁），对其它 CPU 安全。
- **46/49 tick-sched: Convert ad-hoc implementation of irq_work_kick_cpu()**：用通用 `irq_work_kick_cpu()` 替换 `nohz_full_kick_work` 的自制实现（−10 行）。
- 其余覆盖 rcu（04）、各类 irqchip/clocksource/perf STARTING（06-42）、hrtimer（44）、tick（47）、ARM/x86 dying（48/49）等。

## 版本演进与当前进展

*current_version: v1*（RFC）。当日新发（封面 `<20261019130856.49711-1-frederic@kernel.org>`），暂无 review 意见。

## Maintainer 意见与讨论焦点

暂无回帖。潜在评审点（无人提出）：post stop_machine 阶段「IRQ 仍关、其它 CPU 可退出」的同步语义是否足够严格，03/49 列出的 sched 各回调并发安全性论证需各子系统维护者逐条确认。

## 合入评估

*likelihood=unknown*。RFC 覆盖面极广（49 补丁、跨 sched/rcu/irqchip/clocksource/perf/tick/x86/ARM），需十余个子系统维护者分别背书；此类大重构通常分多轮推进。*blocking_issues*：RFC 无 review、跨子系统安全论证待逐条确认。*next_action*：等各子系统维护者对 post stop_machine 语义与自身回调并发安全性的 review。

## 效果评估

无 benchmark 数据；目标是缩短/消除 down 单 CPU 时对全机（尤其 RT/isolated 负载）的 stop 干扰，属正确性/隔离性改进。补丁 46 的代码简化为客观收益（删 10 行自制实现）。

## 我可以参与的点

- `review`：逐条核对 03/49 中 sched teardown 回调在「IRQ 关、其它 CPU 运行」下的并发安全论证（dl server stop、RQ clock、hrtick_clear 等）。
- `testing`：在 NOHZ_FULL + RT/isolated 负载下验证 down/up CPU 不再打断全系统任务。

## 参考链接

- 封面信：https://lore.kernel.org/all/20261019130856.49711-1-frederic@kernel.org/

---
id: sched-20261019-013
subject: "cpu/hotplug: Remove cpu_down() global stop_machine() except for CPUHP_TEARDOWN_CPU itself"
date: 2026-10-19
subsystem: sched
type: feature
status: rfc
severity: none
thread_root_msgid: "<20261019130856.49711-1-frederic@kernel.org>"
lore_url: "https://lore.kernel.org/all/20261019130856.49711-1-frederic@kernel.org/"
authors: ["Frederic Weisbecker"]
maintainers_involved: []
current_version: v1
patch_series:
  - version: v1
    msgid: "<20261019130856.49711-1-frederic@kernel.org>"
    date: 2026-10-19
    summary: "RFC 49 补丁：把 teardown 回调移入 post stop_machine 阶段，逐子系统移除全局 stop_machine（sched 为 03/49）"
    review_outcome: "暂无回帖"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues: ["RFC 无 review", "跨十余子系统的并发安全论证待逐条确认"]
  next_action: "等各子系统维护者对 post stop_machine 语义与回调安全性的 review"
contribution_opportunities:
  - kind: review
    description: "逐条核对 03/49 中 sched teardown 回调在 IRQ 关/其它 CPU 运行下的并发安全论证"
  - kind: testing
    description: "NOHZ_FULL + RT/isolated 负载下验证 CPU down/up 不再打断全系统任务"
generated_at: "2026-10-20T01:30:00"
source_email_count: 3
related_articles: []
tags: [nohz, tick, idle]
---