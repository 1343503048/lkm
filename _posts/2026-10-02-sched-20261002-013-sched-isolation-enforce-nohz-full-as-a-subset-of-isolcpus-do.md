---
id: sched-20261002-013
date: '2026-10-02'
subject: 'sched/isolation: Enforce nohz_full as a subset of isolcpus=domain at boot'
subsystem: sched
type: feature
status: under_review
severity: low
thread_root_msgid: <20261002-wujing-dhm-v5-1-78a6996d87ad@gmail.com>
lore_url: https://lore.kernel.org/all/20261002-wujing-dhm-v5-1-78a6996d87ad@gmail.com/
authors:
- Qiliang Yuan
maintainers_involved: []
current_version: v5
patch_series:
- version: v5
  msgid: <20261002-wujing-dhm-v5-1-78a6996d87ad@gmail.com>
  date: '2026-10-02'
  summary: 12 补丁 v5：nohz_full⊆isolcpus=domain boot 校验 + 运行时 housekeeping 掩码更新 + RCU
    读者保护
  review_outcome: 当日无回帖
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues:
  - 无 review
  - 运行时更新的用例与设计未曝光（cover 不在缓存）
  next_action: 等 isolation/sched 维护者评审
contribution_opportunities:
- kind: testing
  description: 构造违例与合法乱序 boot 参数组合验证 01/12 行为
- kind: review
  description: 核对 03/12 RCU 读者对 housekeeping_cpumask() 全部调用点的覆盖
generated_at: '2026-10-03T01:00:00'
source_email_count: 3
related_articles: []
tags:
- isolation
- nohz
title: 'sched/isolation: Enforce nohz_full as a subset of isolcpus=domain at boot'
layout: article
---

> **subject**：`sched/isolation: Enforce nohz_full as a subset of isolcpus=domain at boot`

## TL;DR

Qiliang Yuan 的 12 补丁 v5（v1-v4 未在既往分析窗口覆盖；当日缓存收到的补丁为 01-03/12）：`kernel/sched/isolation.c` 的隔离语义修复与运行时可变 housekeeping 掩码。01/12 修 boot 配置矛盾——`nohz_full=`（或 `isolcpus=nohz`）与 `isolcpus=domain` 独立解析时，没有任何机制阻止一个 CPU 既被 tick 抑制又留在普通调度域里（隔离意图自败）；改为在 `housekeeping_init()`（所有 `__setup()` 解析完后）一次性校验「KERNEL_NOISE ⊆ DOMAIN」不变式，违例时告警并禁用 nohz_full（等价于没传）。02/12 引入运行时 housekeeping 掩码更新 + boot 快照；03/12 给运行时可变掩码的读者加 RCU 保护。当日无回帖。

## 背景与问题

1. **boot 配置矛盾无校验**：`HK_TYPE_KERNEL_NOISE`（nohz_full/isolcpus=nohz）与 `HK_TYPE_DOMAIN`（isolcpus=domain）由两条独立 boot 参数配置。分开传参、或只传 nohz_full 不传 isolcpus=domain 时，一个 CPU 可以 tick 被停、却仍被普通 SMP 均衡与调度视为可用域成员——「tick-suppressed 的 CPU 必须始终被排除在普通调度域外」的不变式被静默破坏，隔离失效。校验若在 `__setup()` 解析时逐条做则依赖参数顺序（先见 nohz_full= 时 isolcpus=domain 还没解析，会误杀合法组合）。
2. **housekeeping 掩码运行时不可变**（02/12 的动机，从补丁标题推断）：boot 后无法调整隔离集合；系列引入运行时更新 + 保留 boot 时的快照语义。
3. **运行时可变掩码的并发读**（03/13 的动机）：掩码一旦可运行时变更，无保护的读者会撕裂/悬空，需要 RCU 化。

## 技术方案

当日缓存三片（系列 cover `<20261002-wujing-dhm-v5-0-78a6996d87ad@gmail.com>` 未进缓存）：

1. **01/12 Enforce nohz_full as a subset of isolcpus=domain at boot**（+36 行，Documentation+isolation.c）：
   - 在 `housekeeping_init()` 里做子集校验（`__setup()` 全部解析完成后，与命令行顺序无关）；
   - 违例处理选「禁用 HK_TYPE_KERNEL_NOISE + pr_warn」而非 panic 或留置不一致（终态等价于没传 nohz_full=）；
   - 关键时序细节：`housekeeping_cpumask()` 只有在 `housekeeping_overridden` static key 使能后才解引用真实 per-type 掩码（此前恒返回 `cpu_possible_mask`）——必须先使能 static key 再校验，否则两边都在比 `cpu_possible_mask`、校验恒空转。补丁为此加了说明注释。
   - kernel-parameters.txt 两个参数的说明补上该约束。
2. **02/12 Add runtime housekeeping mask updates with boot snapshots**：引入运行时更新接口与 boot 快照（正文 15KB，含数据结构重构）。
3. **03/12 RCU-protect runtime-mutable housekeeping cpumask readers**：读者走 RCU（10KB）。

## 版本演进与当前进展

- v1-v4：既往版本（含「wujing-dhm」系列前缀）未进入既往分析窗口，演进细节不可得。
- v5（10-02，`<20261002-wujing-dhm-v5-{1,2,3}-78a6996d87ad@gmail.com>` 等）：当日发出，无任何回帖。

## Maintainer 意见与讨论焦点

当日无回帖、无维护者（Peter/Frederic 等 isolation 相关维护者）表态。可预见的焦点（无人提出）：01/12 的「禁用 nohz_full」失败策略 vs 拒绝启动的取舍；02-03/12 运行时可变掩码与既有 `housekeeping_cpumask()` 快路径（static key + per-type 掩码）的兼容成本；12 补丁整体的动机叙事（cover 不在缓存，运行时更新的用户是谁）。

## 合入评估

*likelihood=unknown*。01/12 的不变式校验方向正确、实现细节（static key 先行使能）显示出对 housekeeping 机制的准确理解；但系列主体（运行时可变掩码，02-12/12）动机不明（cover 缺失）、无 review、v5 已迭代多轮说明仍在打磨。*blocking_issues*：无 review；运行时更新的用例与设计未曝光。*next_action*：等 isolation/sched 维护者（Peter、Frederic）对 01/12 与系列整体的评审。

## 效果评估

无性能数据。01/12 属 boot 期正确性校验（违例场景可由人工构造 boot 参数复现，但当日无测试报告）。

## 我可以参与的点

- `testing`：构造违例组合（`nohz_full=2-3 isolcpus=domain=2`）验证 01/12 的告警与回退行为，再验证合法乱序组合（`isolcpus=domain` 在 `nohz_full=` 之后出现）不被误杀——这是补丁注释里明说的设计目标。
- `review`：核对 03/12 的 RCU 读者覆盖面——`housekeeping_cpumask()` 的调用点分散（tick/nohz/cpuset 等多处），漏一处即撕裂读。

## 参考链接

- v5 01/12: https://lore.kernel.org/all/20261002-wujing-dhm-v5-1-78a6996d87ad@gmail.com/
- v5 02/12: https://lore.kernel.org/all/20261002-wujing-dhm-v5-2-78a6996d87ad@gmail.com/
- v5 03/12: https://lore.kernel.org/all/20261002-wujing-dhm-v5-3-78a6996d87ad@gmail.com/
