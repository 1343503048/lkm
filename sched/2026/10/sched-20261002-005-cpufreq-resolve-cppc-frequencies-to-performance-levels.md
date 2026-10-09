# cpufreq: Resolve CPPC frequencies to performance levels

> **subject**：`cpufreq: Resolve CPPC frequencies to performance levels`

## TL;DR

本文为增量更新，完整脉络见 related_articles。

- sched-20260929-010：Christian Loehle 的 3 补丁系列——table-less 的 cppc-cpufreq 缺少「频率→性能级」解析，不同 kHz 请求 miss schedutil 频率缓存却写同一个 Desired Performance 值；新增 `->resolve_freq()` 回调、CPPC 预计算仿射转换、schedutil limits 未变时跳过冗余回调。实测 schbench mean p99 降 10%、`cppc_set_perf()` 调用降 23.8%。
- sched-20261001-006：Mario Limonciello 给整系列 `Reviewed-by`；Peter Zijlstra 对 kernel/sched/ 部分「No objection」，预期走 cpufreq 维护者通道。
- sched-20261002-005（今天）：Qualcomm 的 Zhongqiu Han 加入评审——1/3 直接 `Reviewed-by`；2/3 指出一个真实的转换不一致：`cppc_perf_to_khz()` 先在 MHz 粒度取整再缩放到 kHz，新映射先缩放，两者最多可差 999 kHz，而 `cppc_cpufreq_perf_limits()` 里 max_freq 仍用旧转换、`data->nominal_khz` 用新转换，质疑 boost 关闭时 `max_freq <= nominal_khz` 的测试是否仍可靠；3/3 指出 `policy->update_limits` 是 bool，需要 1 字节 `xchg()`，但 sparc 等架构不支持。作者当日未回复。

## 背景与问题

（承接 sched-20260929-010）基于频率表的 cpufreq 驱动会把请求解析到频率表条目；table-less 的 cppc-cpufreq 缺这一步——内核返回请求的 kHz 本身，即使固件只暴露少数 performance level（ARM AGI CPU 仅 61 级），不同请求 miss schedutil 缓存却写同一个 Desired Performance 值，造成大量冗余 `cppc_set_perf()` 调用。今天的新增问题是评审发现了系列内部的两处不一致：

1. **两套 perf↔kHz 转换并存且结果不同**：旧 `cppc_perf_to_khz()` 把 offset 在 MHz 粒度取整后再放大到 kHz；2/3 新预计算的映射先做 kHz 级缩放。同一 perf 值经两条路径可得到相差最多 999 kHz 的频率。
2. **`cppc_cpufreq_perf_limits()` 混用两套转换**：`max_freq` 操作数取自 `cpuinfo.max_freq`（旧转换），`data->nominal_khz` 用新转换。boost 关闭时 `max_freq <= data->nominal_khz` 的钳制测试建立在两套数值可比的假设上——若测试意外为假，`policy_max_perf` 会变成 `highest_perf`，max_perf 落在 nominal_perf 之上。

3/3 的问题：跳过「未变化 resolved limits」需要原子消费 pending 标志，`policy->update_limits` 是 bool → 需要 1 字节 `xchg()`；sparc 的 `__arch_xchg()` 只支持 2/4/8 字节，不支持所有架构。

## 技术方案

（承接）三片补丁：1/3 给 table-less `->target()` 驱动新增 `->resolve_freq()` 回调（按 `CPUFREQ_RELATION_{L,H,C}` 规范化请求）；2/3 CPPC 实现该回调（预计算仿射转换并反转整数舍入、limits 钳制后 snap、nominal 以下封顶）；3/3 schedutil 只在 resolved limits 变化仍 pending 时强制同频回调（release/acquire 保序、失败恢复 pending）。

今天 Zhongqiu Han 的评审意见（待作者回应）：
- 1/3 `Reviewed-by: Zhongqiu Han <zhongqiu.han@oss.qualcomm.com>`，无保留。
- 2/3：统一两套转换（或至少在 `cppc_cpufreq_perf_limits()` 内部用同一来源），否则「with boost off, could the max_freq <= data->nominal_khz test still be relied upon?」。
- 3/3：1 字节 `xchg()` 的可移植性问题——暗示需要换成 int/wider 类型或别的同步原语。

## 版本演进与当前进展

- v1（09-29，`<20260929102957.2591657-1-christian.loehle@arm.com>`）：首发。
- 10-01：Mario R-b、Peter 对 kernel/sched/ 无异议（sched-20261001-006）。
- 10-02（今天）：Zhongqiu Han 三连回帖——`<d718da43-0efa-49ea-9081-8d395ee013e6@oss.qualcomm.com>`（1/3 R-b）、`<0a4a28b8-0b26-41df-bd55-c809177a9909@oss.qualcomm.com>`（2/3 转换不一致）、`<4e218e26-19ac-4c05-94a8-c156952f4da0@oss.qualcomm.com>`（3/3 1 字节 xchg）。作者当日未回复。

## Maintainer 意见与讨论焦点

- **Zhongqiu Han**（Qualcomm，评审者，非 cpufreq MAINTAINERS 成员）：1/3 无保留通过；2/3/3/3 均为具体技术质疑（数值不一致的依赖、原子操作可移植性），语气是「求证是否可靠」而非反对方向。
- **Mario Limonciello / Peter Zijlstra**（前一日表态）：R-b 与 sched 侧放行不受今日意见影响，但 2/3 的转换不一致若成立，可能动摇 Mario 的整系列 R-b（2/3 是核心补丁）。
- 无 NAK；两个 open 问题都指向「系列内部一致性」，属可修复范畴。

## 合入评估

*likelihood=medium*（从 high 下调）。昨天三方绿灯后今天出现两处实质技术质疑——尤其 2/3 的「两套转换混用、钳制测试可能失效」直击核心补丁的正确性；若作者确认成立需改动转换统一，R-b 需重审。*blocking_issues*：2/3 转换不一致（999 kHz 差 + 钳制测试依赖）待作者澄清/修复；3/3 的 1 字节 xchg 可移植性待改型；Rafael/Viresh 仍未表态。*next_action*：Christian 回应两处质疑（统一转换来源、换同步原语或说明无问题），Mario 复核后等 cpufreq 维护者收取。

## 效果评估

本日无新数据。既有数据（09-29，ARM AGI CPU 61 级 + schedutil，schbench 16 轮）：median p99 −2.5%、mean of run p99 −10.0%、worst run p99 −19.7%、`cppc_set_perf()` 调用 −23.8%。Zhongqiu 的质疑不影响该数据的真实性（解析去重收益独立于钳制测试）。

## 我可以参与的点

- `review`：独立核算 `cppc_perf_to_khz()` 与 2/3 新映射在典型 CPPC 平台（如 61 级、nominal 2.6GHz）上的具体偏差分布，验证「最多 999 kHz」并给出统一方案的取舍（改旧函数会改变用户可见的 cpuinfo 值）。
- `review`：3/3 的 pending 标志改宽类型（int/unsigned long）对 cacheline 的影响 vs 换 `cmpxchg`/原子 bitop 的方案比较。

## 参考链接

- Zhongqiu Han 对 2/3 的质疑: https://lore.kernel.org/all/0a4a28b8-0b26-41df-bd55-c809177a9909@oss.qualcomm.com/
- Zhongqiu Han 对 3/3 的质疑: https://lore.kernel.org/all/4e218e26-19ac-4c05-94a8-c156952f4da0@oss.qualcomm.com/
- v1 cover: https://lore.kernel.org/all/20260929102957.2591657-1-christian.loehle@arm.com/

---
id: sched-20261002-005
date: '2026-10-02'
subject: 'cpufreq: Resolve CPPC frequencies to performance levels'
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: '<20260929102957.2591657-1-christian.loehle@arm.com>'
lore_url: 'https://lore.kernel.org/all/0a4a28b8-0b26-41df-bd55-c809177a9909@oss.qualcomm.com/'
authors:
  - 'Christian Loehle'
maintainers_involved: []
current_version: v1
patch_series:
  - version: v1
    msgid: '<20260929102957.2591657-1-christian.loehle@arm.com>'
    date: '2026-09-29'
    summary: 'resolve_freq() 回调 + CPPC 仿射转换 + schedutil 跳过冗余回调'
    review_outcome: '10-01 Mario R-b/Peter 放行；10-02 Zhongqiu Han 1/3 R-b + 2/3、3/3 两处技术质疑'
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
    - '2/3 两套 perf↔kHz 转换混用（最多差 999 kHz），钳制测试依赖待澄清'
    - '3/3 需要 1 字节 xchg() 但 sparc 等架构不支持'
    - 'Rafael/Viresh 未表态'
  next_action: 'Christian 回应两处质疑并视需要改转换统一与同步原语'
contribution_opportunities:
  - kind: review
    description: '独立核算两套转换的偏差分布并给出统一方案取舍'
  - kind: review
    description: '比较 pending 标志改宽类型 vs 换原子 bitop 的方案'
generated_at: '2026-10-03T01:00:00'
source_email_count: 3
related_articles:
  - sched-20260929-010
  - sched-20261001-006
tags:
  - cpufreq
  - cppc
---
