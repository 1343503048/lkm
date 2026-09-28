---
id: sched-20260928-001
date: '2026-09-28'
subject: 'sched, steal_governor: Introduce preferred CPUs and steal-driven vCPU backoff'
subsystem: sched
type: feature
status: merged_tip
severity: none
thread_root_msgid: <20260928053728.797539-1-sshegde@linux.ibm.com>
lore_url: https://lore.kernel.org/all/20260928053728.797539-1-sshegde@linux.ibm.com/
authors:
- Shrikanth Hegde
maintainers_involved:
- Peter Zijlstra
current_version: v14
patch_series:
- version: v14
  msgid: <20260928053728.797539-1-sshegde@linux.ibm.com>
  date: '2026-09-28'
  summary: 落实 Peter 对 v13 的命名/结构/changelog/schedstat 四条意见后重发
  review_outcome: 当天 Peter Zijlstra 将 13 枚补丁全部应用到 tip/sched/core
upstream_commit: null
fixes_commit: null
merged_branch: tip/sched/core
merge_assessment:
  likelihood: merged
  blocking_issues: []
  next_action: 跟踪 post-merge 的 arch 接口与测试框架工作
contribution_opportunities:
- kind: testing
  description: 在 x86 KVM 上跑 pgbench/hackbench/sysbench 三列对照，替换已过期的 v2 数据
- kind: discussion
  description: 参与作者规划的 post-merge 工作（arch specific 接口、测试框架）
generated_at: '2026-09-29T01:00:00'
source_email_count: 20
related_articles:
- sched-20260925-010
- sched-20260909-010
tags:
- load_balance
- affinity
- topology
- sched_debug
title: 'sched, steal_governor: Introduce preferred CPUs and steal-driven vCPU backoff'
layout: article
---

## TL;DR

本文为增量更新，完整脉络见 related_articles。这是一个经历了 v1→v14 多轮迭代、从架构特定 RFC 演进而来的调度器机制 + 虚拟化驱动系列，用 guest 侧观察到的 steal time 量化 vCPU 超配争抢程度，据此动态折叠/展开 preferred CPU 集合，降低 lock-holder preemption、TLB/cache miss 等 vCPU 抢占代价。

- <a class="article-ref" href="/lkm/2026/09/09/sched-20260909-010-sched-steal-governor-introduce-preferred-cpus-and-steal-driv.html">sched-20260909-010</a>：v13（13 补丁）发出，封面请求 Peter/Ingo 考虑排入 sched/core、目标 7.4。
- <a class="article-ref" href="/lkm/2026/09/25/sched-20260925-010-sched-steal-governor-introduce-preferred-cpus-and-steal-driv.html">sched-20260925-010</a>：Peter Zijlstra 首次逐枚细读 06/08/09 三枚，提四条收尾性意见（命名、push stopper 结构对齐、changelog、schedstat 版本），Shrikanth 逐条接受。
- <a class="article-ref" href="/lkm/2026/09/28/sched-20260928-001-sched-steal-governor-introduce-preferred-cpus-and-steal-driv.html">sched-20260928-001</a>（今天）：v14 于 28 日 13:37（北京时间）发出，Peter Zijlstra 于约一小时后把全部 13 枚补丁应用到 tip/sched/core，系列**已合入**。

## 背景与问题

（承接 <a class="article-ref" href="/lkm/2026/09/09/sched-20260909-010-sched-steal-governor-introduce-preferred-cpus-and-steal-driv.html">sched-20260909-010</a> / <a class="article-ref" href="/lkm/2026/09/25/sched-20260925-010-sched-steal-governor-introduce-preferred-cpus-and-steal-driv.html">sched-20260925-010</a>）大规模机器上客户普遍做 vCPU 超配：给 VM 配很多 vCPU、背后是更小的共享 pCPU 池。多个 VM 同时高负载时 pCPU 池被争抢，hypervisor 为公平 preempt 某个 vCPU；若被 preempt 的 vCPU 正持锁或关中断，整体前进能力崩盘——除丢失的 CPU 时间外，还有锁持有者被抢占、TLB/cache miss、host 调度开销。已有缓解手段（CPU 热插拔/隔离 cpuset）是重量级管理操作、需重建拓扑且破坏用户态亲和性；显式任务亲和性几乎不可维护。于是需要一种快的、协作式的、内核内的退让机制，且不违反用户/任务亲和性契约。建模选择：用 guest 已看到的 steal time 作为争抢程度的量化。今天背景无新增，症结从「维护者评审」转向「已合入」。

## 技术方案

（承接 <a class="article-ref" href="/lkm/2026/09/09/sched-20260909-010-sched-steal-governor-introduce-preferred-cpus-and-steal-driv.html">sched-20260909-010</a> / <a class="article-ref" href="/lkm/2026/09/25/sched-20260925-010-sched-steal-governor-introduce-preferred-cpus-and-steal-driv.html">sched-20260925-010</a>）分两层，策略与机制切开。**Layer A（调度器机制 preferred CPUs）**：引入 CPU 状态 preferred，经 `cpu_preferred_mask` 暴露并严格维持为 `cpu_active_mask` 子集；三个介入点——唤醒 `is_cpu_allowed()` 检查、tick 侧 stopper 推送非 preferred CPU 上的当前任务、`sched_balance_rq` 把域 span 限制在 `cpu_preferred_mask` 内。硬约束：绝不破坏用户亲和性。**Layer B（策略引擎 `drivers/virt/steal_governor.c`）**：可加载驱动（`CONFIG_STEAL_GOVERNOR`），按 steal 比例低/高阈值（默认 1000ms 周期、200/500）在 vCPU 间折叠/展开。今天无新代码，v14 只落实 Peter 对 v13 的四条收尾意见，随后全部合入。

## 版本演进与当前进展

*current_version: v14*（已合入 tip/sched/core）。v14 于 28 日发出，落实 Peter 对 v13 的四条意见后，13 枚补丁当天即被 Peter 应用到 tip/sched/core（13 个 tip-bot2 合入通知，committer 均为 Peter Zijlstra）。这四条意见分别是：06/13 的 `task_can_migrate_to_preferred()` 改名与语义、08/13 的 push stopper 与 `__balance_push_cpu_stop()` 对齐并删除多余的 `!is_migration_disabled()`、09/13 的迁移统计 changelog 语义、以及输出格式变化相关的 schedstat 版本考虑。

## Maintainer 意见与讨论焦点

- **Peter Zijlstra**（维护者）：直接收取并合入——13 枚补丁均带其 Signed-off-by，说明设计层面（preferred CPU + steal governor 分层、不破坏亲和性硬约束、FAIR-only 范围）已被完全接受，此前 v13 的四条意见全部是收尾性细节，无一质疑机制设计。
- **Yury Norov**：多枚 Reviewed-by + 早期 rigorous review，是系列质量的主要推手（作者封面特别致谢）。
- **Frederic Weisbecker**：ack 了 01/13 的 cputime helper。无 NAK，无未解决分歧。

## 合入评估

*likelihood=merged*。13 枚补丁已全部进入 tip/sched/core，是当日调度子系统最主要的合入事件。*blocking_issues*：无——核心机制与驱动已落地。*next_action*：跟踪作者已规划的 post-merge 工作（面向 arch 的接口以获得额外性能、feature 测试框架），以及对 7.4 周期的后续跟进。

## 效果评估

v14 封面自述「在 PowerPC 上对真实负载表现良好，早期 KVM 测试在 s390/x86 上亦有提升」「对纯 CPU 时间类负载可能轻微回退」。28 日本身无新 benchmark 数据；此前 x86/s390 量化数据基于 v2（已过期），见 related_articles。

## 我可以参与的点

- `testing`：系列已合入但仍缺 post-merge 的跨架构量化数据，可在 x86 KVM 上跑 pgbench/hackbench/sysbench 三列对照，替换过期数据并回帖。
- `discussion`：作者明确规划的 post-merge 工作（arch specific 接口、测试框架）可参与讨论或提前动手。

## 参考链接

- v14 封面: https://lore.kernel.org/all/20260928053728.797539-1-sshegde@linux.ibm.com/
- 合入 commit（virt: Introduce steal governor driver）9a8e740ee9f6: https://git.kernel.org/tip/9a8e740ee9f69ec857ffa0c76cf1a01d1cb7360f
- 合入 commit（sched/fair: Load balance only among preferred CPUs）4ee29b029058: https://git.kernel.org/tip/4ee29b029058a8f06fbb91425e1d9351e8015b53
