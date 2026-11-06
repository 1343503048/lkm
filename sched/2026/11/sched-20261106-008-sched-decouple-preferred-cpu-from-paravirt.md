# sched: Decouple PREFERRED_CPU from PARAVIRT

## TL;DR

本文为增量更新，完整脉络见下。

- sched-20261102-004：Yury Norov 的 6 补丁「可写 preferred mask sysfs 接口」系列被 Peter Zijlstra 明确 NAK，但其中 patch 1（把 PREFERRED_CPU 从 PARAVIRT 解耦）获 s390 侧认可，Peter 给出 `HAVE_CPUTIME_STEAL` 替代方案，Kconfig 解耦可独立推进。
- sched-20261103-018：Ilya 与 Shrikanth 对齐解耦方案，定论 `HAVE_CPUTIME_STEAL` 是最佳（既不要求 PARAVIRT，又不规定他架构如何实现 steal time 记账）。
- sched-20261106-008（今天）：Mete Durlu（IBM）正式发出独立补丁实施该方案——新增 `HAVE_CPUTIME_STEAL` 配置标志，把 `PREFERRED_CPU` 的依赖从 `PARAVIRT` 换成 `SMP && HAVE_CPUTIME_STEAL`，并让 s390 与 powerpc-pseries 直接 select 该标志。**已获 Yury Norov 的 Reviewed-by、Peter Zijlstra 的 Suggested-by**，方向无异议，等待收取。

## 背景与问题

（承接 20261102-004/20261103-018）`PREFERRED_CPU`（steal governor 专用）本身不依赖 PARAVIRT 引入的任何特性，却被 PARAVIRT 门控——任何想启用 PREFERRED_CPU 的架构都得连带启用 PARAVIRT 并补齐其 stub。典型痛点是 IBM s390 LPAR：硬件辅助虚拟化下不走 PARAVIRT、用自己的 steal time 记账机制，为启用 PREFERRED_CPU 而引入 PARAVIRT 纯属多余。

## 技术方案

（承接 20261103-018 已对齐的结论）引入 `HAVE_CPUTIME_STEAL` 配置标志，表示「架构已有 steal time 测量能力、无需 PARAVIRT」；把 `PREFERRED_CPU` 的 `depends on SMP && PARAVIRT` 改为 `SMP && HAVE_CPUTIME_STEAL`；`HAVE_CPUTIME_STEAL` 默认 `default y if HAVE_PV_STEAL_CLOCK_GEN`（PARAVIRT 侧经此继承），s390 与 powerpc-pseries 直接 `select HAVE_CPUTIME_STEAL`。`STEAL_GOVERNOR` 依赖同步从 `PARAVIRT && SMP` 改为 `SMP && HAVE_CPUTIME_STEAL`。共 5 个文件 +12/-2 行。

## 版本演进与当前进展

*current_version: v1（2026-11-06 发出）*。这是 Yury Norov 原始 patch 1 的独立落地版（Yury 的原系列整体被 NAK，但此解耦被保留并单独立项），由 Mete Durlu 基于 Yury 的补丁重发，已带 Yury 的 Reviewed-by 与 Peter 的 Suggested-by。

## Maintainer 意见与讨论焦点

无争议。Yury Norov 已给 Reviewed-by；Peter Zijlstra 是方案提出者（Suggested-by）。此前 Ilya/Shrikanth 已对齐 `HAVE_CPUTIME_STEAL` 为最优解，无 NAK。

## 合入评估

*likelihood=high*。方案经多人对齐、有 Reviewed-by 与 Suggested-by 背书、改动小（Kconfig 12 行）且仅影响配置门控。*blocking_issues*：无明显阻塞。*next_action*：等 Peter Zijlstra 收取（或经 sched tip 树合入），并确认 s390/powerpc 侧无异议。

## 效果评估

无运行时效果数据（纯 Kconfig 门控改动）。收益是架构使能层面的：s390/powerpc 无需 PARAVIRT 即可启用 PREFERRED_CPU。

## 我可以参与的点

当前阶段暂无明显参与空间：补丁已过审、待收取，可持续观察是否需补其它架构的 `HAVE_CPUTIME_STEAL` 适配。

## 参考链接

- lore thread: https://lore.kernel.org/all/20261106-preferredcpu-v1-1-3f0ca4944f8b@linux.ibm.com/
- Yury 原补丁引用（来自补丁正文）: https://lore.kernel.org/all/20261101192203.6979-2-ynorov@nvidia.com/

---
id: sched-20261106-008
date: 2026-11-06
subject: "sched: Decouple PREFERRED_CPU from PARAVIRT"
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: "<20261106-preferredcpu-v1-1-3f0ca4944f8b@linux.ibm.com>"
lore_url: "https://lore.kernel.org/all/20261106-preferredcpu-v1-1-3f0ca4944f8b@linux.ibm.com/"
authors: [Mete Durlu]
maintainers_involved: [Yury Norov]
current_version: v1
patch_series:
  - version: v1
    msgid: "<20261106-preferredcpu-v1-1-3f0ca4944f8b@linux.ibm.com>"
    date: 2026-11-06
    summary: "新增 HAVE_CPUTIME_STEAL，把 PREFERRED_CPU 从 PARAVIRT 解耦。"
    review_outcome: "Yury Reviewed-by、Peter Suggested-by，无异议。"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: []
  next_action: "等 Peter Zijlstra 收取并确认 s390/powerpc 侧无异议"
contribution_opportunities: []
generated_at: "2026-11-07T09:00:00+08:00"
source_email_count: 1
related_articles: [sched-20261102-004, sched-20261103-018]
tags: [affinity]
---