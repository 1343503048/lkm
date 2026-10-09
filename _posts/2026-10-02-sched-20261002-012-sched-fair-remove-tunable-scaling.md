---
id: sched-20261002-012
date: '2026-10-02'
subject: 'sched/fair: Remove tunable scaling'
subsystem: sched
type: discussion
status: rfc
severity: none
thread_root_msgid: <20261002124538.79658-1-torvic9@mailbox.org>
lore_url: https://lore.kernel.org/all/20261002124538.79658-1-torvic9@mailbox.org/
authors:
- Tor Vic
maintainers_involved: []
current_version: v1
patch_series:
- version: v1
  msgid: <20261002124538.79658-1-torvic9@mailbox.org>
  date: '2026-10-02'
  summary: 2 补丁 RFC：删 none/linear 缩放；进而删整个缩放机制、固定 2ms base slice
  review_outcome: 当日无回帖
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: low
  blocking_issues:
  - 无任何 review
  - 2ms 取值无数据支撑
  - sysctl ABI 变化未讨论
  next_action: 等 sched 维护者表态
contribution_opportunities:
- kind: testing
  description: 三档 CPU 数机器对比 log 缩放 vs 固定 2ms 的延迟与切换率
- kind: discussion
  description: 梳理 tunable_scaling 用户面与 ABI 影响
generated_at: '2026-10-03T01:00:00'
source_email_count: 3
related_articles: []
tags:
- fair
- sysctl
title: 'sched/fair: Remove tunable scaling'
layout: article
---

> **subject**：`sched/fair: Remove tunable scaling`

## TL;DR

Tor Vic（社区贡献者，自述「not a developer」）的 2 补丁 RFC：删除 2.6.33 时代引入的调度器可调参数缩放机制。1/2 先删基本无人用的 `none`/`linear` 缩放（保留默认的 logarithmic），debugfs 直设 `sched_base_slice` 仍可用；2/2 更进一步删掉整个缩放机制、把 `sched_base_slice` 固定为 2ms——当前 log2 缩放下实际取值 0.7/1.4/2.1/2.8ms（按 1/2-3/4-7/8+ CPU 分档），2ms 居中。基线 7.3-rc5、2C/4T Skylake 上 build+boot 测试。RFC 探路性质（「I don't know whether these changes are actually wanted by the sched people」），删代码可观（5 文件 +3/−141）。当日无回帖。

## 背景与问题

`sched_base_slice` 等 fair 可调参数自 Linux 2.6.33 起带缩放机制：按 CPU 数对数分档放大 base slice（1 CPU→0.7ms、2-3→1.4ms、4-7→2.1ms、8+→2.8ms，2.6.x 时代遗留的多核适配启发式）。维护成本：`kernel/sched/debug.c` 里 52 行 sysctl 处理、`fair.c` 里 79 行的缩放计算与三档模式（none/linear/logarithmic）分支。作者论点：(a) `none`/`linear` 档几乎无人使用且用处有限（要改粒度可直设 debugfs 的 `sched_base_slice`）；(b) log 档的四档取值跨度本身不大（0.7~2.8ms），一个固定的 2ms 默认即可覆盖典型场景——他在自己的消费级 x86_64 机器上就用 2ms。base_slice 数值历史上多次调整（最近一次 2025 年 commit 2ae891b82695）。

## 技术方案

两片（`<20261002124538.79658-{1,2,3}-torvic9@mailbox.org>`，5 文件 +3/−141）：

1. **1/2 Remove the 'none' and 'linear' scaling of tunables**：删 `sysctl_sched_tunable_scaling` 的两档枚举与分支，默认固定为 logarithmic；`include/linux/sched/sysctl.h`/`core.c`/`debug.c`/`fair.c`/`sched.h` 相应收缩。
2. **2/2 Remove sched_base_slice scaling altogether**：整个 `calc_delta_fair` 侧的 base slice 缩放计算删除，`sched_base_slice` 固定 2ms（「a value which has been chosen somewhat arbitrarily」）；作者明说 2ms 的选择开放讨论。

适用基线 7.3-rc5；2C/4T Skylake build+boot 测试通过，无性能数据。

## 版本演进与当前进展

v1（RFC）刚发出。当日无回帖。作者标注 RFC 的原因：「I don't know whether these changes are actually wanted by the sched people - and because I'm not a developer」。

## Maintainer 意见与讨论焦点

当日无回帖、无维护者表态。可预见的焦点（尚无人提出）：

- 2ms 固定值对 8+ CPU 大机器意味着 base slice 从 2.8ms 收窄到 2ms——调度粒度变细、上下文切换增多的影响需要数据；
- 缩放机制删除后，`sysctl_sched_tunable_scaling` 用户可见接口消失（debugfs/sysctl ABI 变化）；
- 历史上 Peter/Vincent 对 base slice 的取值有明确观点（2025 年调整即 Peter 所为），固定值方案是否合其意未知。

## 合入评估

*likelihood=low*。RFC、零评审、无性能数据、改动调度核心默认行为（大机器 slice 收窄）且动 sysctl ABI；作者自认非开发者、以探路为目的。删代码的整洁性论点成立，但需要维护者背书 + 各 CPU 档位的延迟数据才可能推进。*blocking_issues*：无任何 review；2ms 取值无数据支撑；ABI 变化未讨论。*next_action*：等 sched 维护者表态是否有兴趣；若无回应大概率止步 RFC。

## 效果评估

无性能数据（build+boot 测试之外零验证）。0.7→2.8ms 的现状与 2ms 固定值之间的延迟分布差异未测。

## 我可以参与的点

- `testing`：在 1 CPU / 4 CPU / 64+ CPU 三档机器上对比 log 缩放 vs 固定 2ms 的 hackbench/schbench 延迟与上下文切换率——RFC 最缺的就是「删了缩放会怎样」的数据；有数据即可替作者把 RFC 升级为正式提案。
- `discussion`：梳理 `sysctl_sched_tunable_scaling` 的实际用户面（发行版默认值、文档引用），评估删除的 ABI 影响。

## 参考链接

- RFC cover: https://lore.kernel.org/all/20261002124538.79658-1-torvic9@mailbox.org/
- 2/2（整体删除）: https://lore.kernel.org/all/20261002124538.79658-3-torvic9@mailbox.org/
