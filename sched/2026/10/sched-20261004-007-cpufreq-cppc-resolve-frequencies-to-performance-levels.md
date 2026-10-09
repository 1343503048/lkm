# cpufreq: CPPC: Resolve frequencies to performance levels

## TL;DR

本文为增量更新，完整脉络见 related_articles。

- sched-20260929-010：Christian Loehle（ARM）3 补丁系列——table-less 的 cppc-cpufreq 缺「频率→性能级」解析，不同 kHz 请求 miss schedutil 频率缓存却写同一个 Desired Performance 值；新增 `->resolve_freq()` 回调、CPPC 预计算仿射转换、schedutil limits 未变时跳过冗余回调。实测 schbench mean p99 降 10%、`cppc_set_perf()` 调用降 23.8%。
- sched-20261001-006：Mario Limonciello 给整系列 `Reviewed-by`；Peter Zijlstra 对 kernel/sched/ 部分「No objection」，预期走 cpufreq 维护者通道。
- sched-20261002-005：Qualcomm 的 Zhongqiu Han 加入评审——1/3 直接 `Reviewed-by`；2/3 指出转换不一致（`cppc_perf_to_khz()` MHz 粒度取整 vs 新映射先缩放，最多差 999 kHz；`max_freq` 用旧转换、`nominal_khz` 用新转换，boost 关闭时 `max_freq <= nominal_khz` 判据可靠性存疑）；3/3 指出需要 1 字节 `xchg()` 而 sparc 不支持。
- sched-20261004-007（今天）：**评审者 Zhongqiu Han 撤回自己的 2/3 质疑**——「Please ignore this comment. I misread cppc_perf_to_khz(). Sorry about that.」其「取整顺序不一致」的论证基于对 `cppc_perf_to_khz()` 的误读；2/3 的反对面收窄，系列回到「整系列 R-b + sched/ 部分 no objection、剩 3/3 的 xchg 硬约束」的状态。

## 背景与问题

（承接 sched-20261002-005）cppc-cpufreq 无频率表时，`cppc_perf_to_khz()`/`cppc_khz_to_perf()` 的仿射转换含 MHz 粒度取整；不同 kHz 请求可能解析到同一性能级，miss schedutil 频率缓存却写同一 Desired Performance 值。2/3 预计算转换并暴露 `resolve_freq()`。Zhongqiu Han 10-02 对「新旧两套转换混用是否产生 999 kHz 级不一致」的质疑，今日被其本人以误读为由撤回。

## 技术方案

（承接）3 补丁框架不变：

1. `cpufreq: Add a driver frequency resolution callback`——`->resolve_freq()` 驱动回调。
2. `cpufreq: CPPC: Resolve frequencies to performance levels`——CPPC 预计算仿射转换 + `resolve_freq()` 实现；今天的自纠不改变补丁方向，仅收窄论证范围。
3. `cpufreq: Skip updates for unchanged resolved limits`——`policy->update_limits` 判断跳过冗余 `cppc_set_perf()`；1 字节 `xchg()` 的 sparc 支持问题仍在。

## 版本演进与当前进展

- v1（09-29，`<20260929102957.2591657-1-christian.loehle@arm.com>`）→ Mario 整系列 R-b、Peter no objection（10-01）→ Zhongqiu Han 三点评审（10-02）→ 10-04 其撤回 2/3 意见（`<c6948769-1050-4211-b93c-b72f51c32dd4@oss.qualcomm.com>`）。作者对 3/3 xchg 问题尚未回复。

## Maintainer 意见与讨论焦点

- **Zhongqiu Han**（评审者）：1/3 R-b 维持；2/3 质疑撤回（误读）；3/3 的 1 字节 `xchg()` 在 sparc 等架构不支持的问题仍成立。
- Mario Limonciello（amd-pstate/cpufreq 维护者圈）整系列 R-b；Rafael Wysocki 的最终收取待定。

## 合入评估

*likelihood=high*。整系列已有 R-b + sched/ 部分 no objection；今天评审者撤回 2/3 质疑后，唯一明确遗留是 3/3 的 1 字节 `xchg()` 可移植性——属可修的实现细节而非方向问题。*blocking_issues*：3/3 的 xchg 改写（换 cmpxchg 或改宽度）待作者处理。*next_action*：作者回应 3/3 后出 v2，走 cpufreq 通道收取。

## 效果评估

（承接 v1 数据）schbench mean p99 −10%、`cppc_set_perf()` 调用 −23.8%。今天无新数据，仅评审自纠。

## 我可以参与的点

- `review`：在 sparc64 上验证 3/3 的 1 字节 `xchg()` 替代方案（cmpxchg 循环或改用 int 宽度 + 位运算），回帖给实现建议——系列剩余的唯一明确硬伤。

## 参考链接

- lore（系列 cover）: https://lore.kernel.org/all/20260929102957.2591657-1-christian.loehle@arm.com/
- lore（2/3 补丁）: https://lore.kernel.org/all/20260929102957.2591657-3-christian.loehle@arm.com/
- lore（Zhongqiu Han 撤回）: https://lore.kernel.org/all/c6948769-1050-4211-b93c-b72f51c32dd4@oss.qualcomm.com/

---
id: sched-20261004-007
date: '2026-10-04'
subject: 'cpufreq: CPPC: Resolve frequencies to performance levels'
subsystem: cpufreq
type: fix
status: under_review
severity: medium
thread_root_msgid: '<20260929102957.2591657-1-christian.loehle@arm.com>'
lore_url: 'https://lore.kernel.org/all/20260929102957.2591657-3-christian.loehle@arm.com/'
authors:
  - 'Christian Loehle'
maintainers_involved:
  - 'Mario Limonciello'
  - 'Peter Zijlstra'
current_version: v1
patch_series:
  - version: v1
    msgid: '<20260929102957.2591657-1-christian.loehle@arm.com>'
    date: '2026-09-29'
    summary: 'resolve_freq() 回调 + CPPC 预计算仿射转换 + schedutil 跳过冗余回调'
    review_outcome: 'Mario 整系列 R-b；Peter no objection；10-04 Zhongqiu Han 撤回 2/3 质疑'
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues:
    - '3/3 的 1 字节 xchg() 在 sparc 等架构不支持，待改写'
  next_action: '作者回应 3/3 后出 v2，走 cpufreq 通道收取'
contribution_opportunities:
  - kind: review
    description: 'sparc64 上验证 1 字节 xchg() 替代方案并回帖'
generated_at: '2026-10-05T01:00:00'
source_email_count: 1
related_articles:
  - sched-20260929-010
  - sched-20261001-006
  - sched-20261002-005
tags:
  - cpufreq
  - cppc
---
