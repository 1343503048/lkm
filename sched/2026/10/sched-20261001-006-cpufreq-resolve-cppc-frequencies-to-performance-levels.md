# cpufreq: Resolve CPPC frequencies to performance levels

> **subject**：`cpufreq: Resolve CPPC frequencies to performance levels`

## TL;DR

本文为增量更新，完整脉络见 related_articles。

- sched-20260929-010：Christian Loehle 的 3 补丁系列——table-less 的 cppc-cpufreq 缺少「频率→性能级」解析，不同 kHz 请求会 miss schedutil 的频率缓存却写同一个 Desired Performance 值；系列新增 `->resolve_freq()` 回调让 table-less `->target()` 驱动规范化请求，CPPC 预计算仿射转换做解析，schedutil 在 limits 未变时跳过冗余回调。实测 schbench mean p99 降 10%、`cppc_set_perf()` 调用降 23.8%。
- sched-20261001-006（今天）：系列获得两份重量级表态——Mario Limonciello（amd-pstate 维护者）给出 `Reviewed-by`；Peter Zijlstra（sched 维护者）「No objection to the kernel/sched/ change. I'm assuming rjw or other cpufreq maintainer will take this?」——schedutil 侧放行，球交给 Rafael/Viresh 的 cpufreq 通道。

## 背景与问题

（承接 sched-20260929-010）基于频率表的 cpufreq 驱动会在交给 governor 前把请求解析到频率表条目（不同 kHz 请求选了同一条目就不必再打给驱动）；table-less 的 cppc-cpufreq 缺这一步——内核返回请求的 kHz 本身，即使固件只暴露少数 CPPC performance level（测试的 ARM AGI CPU 仅 61 级），不同请求 miss 掉 schedutil 的频率缓存、却最终写同一个 Desired Performance 值，造成大量冗余 `cppc_set_perf()` 调用。今天无新背景，进展是评审信号到位。

## 技术方案

（承接）三片补丁：1/3 给 table-less `->target()` 驱动新增 `->resolve_freq()` 回调（按 `CPUFREQ_RELATION_{L,H,C}` 在 limits 内规范化请求并文档化契约）；2/3 CPPC 实现该回调（预计算仿射转换并直接反转其整数舍入、limits 钳制后 snap 到支持频率、nominal 以下封顶）；3/3 让 schedutil 只在「resolved policy->{min,max} 变化仍 pending」时才强制同频回调（release/acquire 保序、失败恢复 pending）。规模 6 文件 +359/−50（含 `kernel/sched/cpufreq_schedutil.c`）。今天无代码变更。

## 版本演进与当前进展

- v1（09-29，`<20260929102957.2591657-1-christian.loehle@arm.com>`）：首发，当日无回帖。
- 10-01：Mario Limonciello `Reviewed-by`（`<8cdd2938-a7a2-4d20-bacd-7ab4f5cbe80f@kernel.org>`）；Peter Zijlstra 对 kernel/sched/ 部分无异议（`<20261001103444.GU4120091@noisy.programming.kicks-ass.net>`）。

## Maintainer 意见与讨论焦点

- **Peter Zijlstra**（sched 维护者）：对 `kernel/sched/cpufreq_schedutil.c` 的改动「No objection」，并明确预期由 rjw（Rafael）或其他 cpufreq 维护者收取——划清了 sched 与 cpufreq 两侧的责任边界。
- **Mario Limonciello**（amd-pstate 驱动维护者）：整系列 `Reviewed-by: Mario Limonciello (AMD) <superm1@kernel.org>`，无附加意见。
- 无 NAK、无修改要求；尚未见 Rafael/Viresh 表态。

## 合入评估

*likelihood=high*。方案自带端到端 benchmark 与调用量数据、跨 cpufreq core/CPPC/schedutil 的改动已获 sched 维护者放行（kernel/sched/ 部分）与 amd-pstate 维护者整系列 R-b；剩余动作是 cpufreq 通道（Rafael/Viresh）的正式收取。*blocking_issues*：Rafael Wysocki / Viresh Kumar 尚未表态。*next_action*：等 Rafael 或 Viresh 收取（Peter 已明确预期走 cpufreq 维护者通道）。

## 效果评估

本日无新数据。既有数据（09-29，ARM AGI CPU 61 级 + schedutil，`schbench -m 2 -t 31 -F 256 -n 5 -R 18000 -r 60 -w 20 -i 60` 16 轮）：median p99 3364→3280us（−2.5%）、mean of run p99 3664.2→3299.0us（−10.0%）、worst run p99 4360→3500us（−19.7%）、median throughput +0.2%；instrumented 跑法 `cppc_set_perf()` 调用 1,136,868→866,703（−23.8%）。

## 我可以参与的点

- `testing`：在其它 CPPC 平台或 amd-pstate frequency-based 路径复测 schbench p99 与 `set_perf()` 调用量下降，扩大数据面（收取前的数据补充仍有价值）。
- `review`：核对 `->resolve_freq()` 整数舍入反转与 `cpufreq_read_policy_limits()` 并发正确性（此前识别的审读点，尚无人覆盖）。

## 参考链接

- Mario 的 Reviewed-by: https://lore.kernel.org/all/8cdd2938-a7a2-4d20-bacd-7ab4f5cbe80f@kernel.org/
- Peter 的回复: https://lore.kernel.org/all/20261001103444.GU4120091@noisy.programming.kicks-ass.net/
- v1 cover: https://lore.kernel.org/all/20260929102957.2591657-1-christian.loehle@arm.com/

---
id: sched-20261001-006
date: '2026-10-01'
subject: 'cpufreq: Resolve CPPC frequencies to performance levels'
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: '<20260929102957.2591657-1-christian.loehle@arm.com>'
lore_url: 'https://lore.kernel.org/all/20260929102957.2591657-1-christian.loehle@arm.com/'
authors:
  - 'Christian Loehle'
maintainers_involved:
  - 'Peter Zijlstra'
  - 'Mario Limonciello'
current_version: v1
patch_series:
  - version: v1
    msgid: '<20260929102957.2591657-1-christian.loehle@arm.com>'
    date: '2026-09-29'
    summary: '新增 ->resolve_freq() 回调；CPPC 预计算仿射转换解析频率到 performance level；schedutil 在 limits 未变时跳过冗余回调'
    review_outcome: '10-01 Mario 整系列 Reviewed-by；Peter 对 kernel/sched/ 部分无异议、预期走 cpufreq 维护者通道'
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues:
    - 'Rafael Wysocki / Viresh Kumar（cpufreq 维护者）尚未表态收取'
  next_action: '等 Rafael 或 Viresh 经 cpufreq 通道收取'
contribution_opportunities:
  - kind: testing
    description: '在其它 CPPC/amd-pstate frequency 路径复测 schbench p99 与 set_perf 调用量下降'
  - kind: review
    description: '核对 resolve_freq 舍入反转与 limits 并发读的正确性'
generated_at: '2026-10-09T01:00:00'
source_email_count: 2
related_articles:
  - sched-20260929-010
tags:
  - cpufreq
---
