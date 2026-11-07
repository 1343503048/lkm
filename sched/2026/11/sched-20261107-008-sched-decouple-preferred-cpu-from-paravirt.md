# sched: Decouple PREFERRED_CPU from PARAVIRT

## TL;DR

本文为增量更新，完整脉络见下。

- sched-20261102-004：Yury Norov 的 6 补丁「可写 preferred mask sysfs 接口」系列被 Peter Zijlstra 明确 NAK，但其中 patch 1（把 PREFERRED_CPU 从 PARAVIRT 解耦）获 s390 侧认可，Peter 给出 `HAVE_CPUTIME_STEAL` 替代方案，Kconfig 解耦可独立推进。
- sched-20261103-018：Ilya 与 Shrikanth 对齐解耦方案，定论 `HAVE_CPUTIME_STEAL` 是最佳。
- sched-20261106-008：Mete Durlu（IBM）正式发出独立补丁实施该方案——新增 `HAVE_CPUTIME_STEAL` 配置标志，把 PREFERRED_CPU 依赖从 PARAVIRT 换成 `SMP && HAVE_CPUTIME_STEAL`，s390 与 powerpc-pseries 直接 select。已获 Yury Reviewed-by、Peter Suggested-by。
- sched-20261107-008（今天）：**Shrikanth Hegde（IBM）给 Reviewed-by**。补丁再添一名架构侧背书，方向无异议，仍等待收取。

## 背景与问题

（承接 sched-20261102-004 / 20261103-018 / 20261106-008）`PREFERRED_CPU`（steal governor 专用）不依赖 PARAVIRT 的任何特性，却被 PARAVIRT 门控——IBM s390 LPAR 走自己的 steal time 记账、为启用 PREFERRED_CPU 而引入 PARAVIRT 纯属多余。今日无新问题浮现，仅评审背书累积。

## 技术方案

（承接 20261103-018 已对齐结论）引入 `HAVE_CPUTIME_STEAL` 配置标志，把 PREFERRED_CPU 的 `depends on SMP && PARAVIRT` 改为 `SMP && HAVE_CPUTIME_STEAL`；`HAVE_CPUTIME_STEAL` 默认 `default y if HAVE_PV_STEAL_CLOCK_GEN`，s390 与 powerpc-pseries 直接 `select HAVE_CPUTIME_STEAL`。共 5 文件 +12/-2 行。今日无技术变更。

## 版本演进与当前进展

*current_version: v1（2026-11-06 发出）*。今日 Shrikanth Hegde 给 Reviewed-by，无新版本。

## Maintainer 意见与讨论焦点

无争议。已累积：Yury Norov 的 Reviewed-by、Peter Zijlstra 的 Suggested-by（方案提出者）、今日 Shrikanth Hegde 的 Reviewed-by。无 NAK。

## 合入评估

*likelihood=high*。方案经多人对齐、有三个方向的背书（作者 Yury 审、维护者 Peter 建议、架构侧 Shrikanth 审）、改动小且仅影响配置门控。*blocking_issues*：无明显阻塞。*next_action*：等 Peter Zijlstra 经 sched tip 树收取，并确认 s390/powerpc 侧无异议。

## 效果评估

无运行时效果数据（纯 Kconfig 门控改动）。收益是架构使能层面：s390/powerpc 无需 PARAVIRT 即可启用 PREFERRED_CPU。

## 我可以参与的点

当前阶段暂无明显参与空间：补丁已过审、待收取，可持续观察是否需补其它架构的 `HAVE_CPUTIME_STEAL` 适配。

## 参考链接

- lore thread（Shrikanth Reviewed-by）: https://lore.kernel.org/all/e425d6bd-9aea-4d50-b0fc-1793e20739c4@linux.ibm.com/
- lore thread（补丁）: https://lore.kernel.org/all/20261106-preferredcpu-v1-1-3f0ca4944f8b@linux.ibm.com/

---
id: sched-20261107-008
date: '2026-11-07'
subject: "sched: Decouple PREFERRED_CPU from PARAVIRT"
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: "<20261106-preferredcpu-v1-1-3f0ca4944f8b@linux.ibm.com>"
lore_url: "https://lore.kernel.org/all/e425d6bd-9aea-4d50-b0fc-1793e20739c4@linux.ibm.com/"
authors: [Mete Durlu]
maintainers_involved: [Peter Zijlstra, Yury Norov, Shrikanth Hegde]
current_version: v1
patch_series:
  - version: v1
    msgid: "<20261106-preferredcpu-v1-1-3f0ca4944f8b@linux.ibm.com>"
    date: '2026-11-06'
    summary: "新增 HAVE_CPUTIME_STEAL，把 PREFERRED_CPU 依赖从 PARAVIRT 解耦"
    review_outcome: "Yury Reviewed-by、Peter Suggested-by；今日 Shrikanth Hegde Reviewed-by"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: []
  next_action: "等 Peter Zijlstra 经 sched tip 树收取"
contribution_opportunities: []
generated_at: "2026-11-08T09:00:00+08:00"
source_email_count: 1
related_articles: [sched-20261102-004, sched-20261103-018, sched-20261106-008]
tags: [affinity]
---