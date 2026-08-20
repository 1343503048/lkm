---
subject: 'sched/fair: Let sync wakeups target the waker''s core'
id: sched-20260806-009
date: '2026-08-06'
title: 'sched/fair: Let sync wakeups target the waker''s core'
series: Let sync wakeups target the waker's core
type: feature
status: under_review
severity: none
merge_likelihood: medium
tags:
- cfs
- load_balance
- topology
- wake_affine
authors:
- K Prateek Nayak <kprateeknayak@amd.com>
- Madadi Vineeth Reddy <vineethr@linux.ibm.com>
- Kayra Cizmeci <kayra@dominiek.com>
reviewers:
- Kayra Cizmeci <kayra@dominiek.com>
- Madadi Vineeth Reddy <vineethr@linux.ibm.com>
related_articles:
- sched-20260805-006
- sched-20260804-006
emails:
- uid-24638@qq-imap
- uid-23737@qq-imap
layout: article
---

# sched/fair: sync wakeup 落到 waker 所在 core（Kayra 实测 x86 数据）

## 摘要

Prateek 的「sync wakeup 优先落到 waker 所在 core 的空闲兄弟」系列（延续 08-05-006）在 08-06 收到 **Kayra Cizmeci 的实测数据**（x86-64）：

- **schbench**（-t 2 -m 3 -r 30 -s 30000 --sched-prio）：WRK 延迟 +1.5%、p99 +1.5%、p99.9 +3.6%。
- **hackbench**（32 process/pipe，20 次）：CPU cycles **-1.4%**（改善）、cache-misses **+4.6%**（退化）、cache-references -0.36%；单次运行 -1.9% cycles / +5.3% cache-misses；hackbench 整体 **+2.8% 运行时间（退化）**。
- Kayra 原型与 Prateek 系列差别：对 `cpu_likely_is_preferred()` 的兄弟也做 WF_SYNC 处理，并保留部分原始逻辑（与主线 patch 不完全一致），提示性能结果需以最终系列口径复测。

Madadi（IBM）在 23737 等邮件里继续参与讨论 sync wakeup 的 SMT 兄弟选择对 ppc64 的影响。

## 技术细节

Prateek 系列在 `select_idle_sibling()` 的 `WF_SYNC` 分支优先 `waker_cpu` 所在 core 的空闲兄弟（延续 08-05-006 代码）。Kayra 数据是社区「拿真实数字回应 Peter 缺数据质疑」的首次实证：代价是 cache-misses 上升（把 wakee 塞进 waker core 制造 SMT 共享资源争用），收益是 cycles 略降。

## 影响与风险

- 影响面：sync wakeup 目标 CPU 选择，影响协作型负载（pipe/IPC）唤醒延迟与 SMT 共享资源争用。
- 风险：中。`core` 粒度定义（SMT vs LLC）仍待最终澄清（Peter 早前质疑），且 hackbench 实测净退化（+2.8% 时间）意味着**并非对所有负载都是净收益**——需更多 workload 与多平台数据。
- 数据状态：本日首次出现量化数据（Kayra x86），但偏 hackbench 退化，尚不足以说服合入。

## 评价

是 08-04-006 / 08-05-006 的延续与实证化。方向有吸引力但**数据呈现混合信号**（cycles 微降、cache-misses/cache 退化），且核心定义未冻结。合入可能性中等，建议 Prateek 在更多平台/负载上复测并以「最终系列口径」统一数据后再推进。
