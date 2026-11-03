# sched: decouple PREFERRED_CPU from PARAVIRT in Kconfig.preempt

## TL;DR

本文为增量更新，完整脉络见 related_articles。

- sched-20261102-004：Yury Norov 的 6 补丁系列（可写 preferred mask sysfs 接口）被 Peter Zijlstra 明确 NAK（"This isn't happening"），但其中 patch 1（把 PREFERRED_CPU 从 PARAVIRT 解耦）获 s390 侧 Ilya/Shrikanth 认可，Peter 另给出 `HAVE_CPUTIME_STEAL` 替代方案，该 Kconfig 解耦可独立推进。
- sched-20261103-018（今天）：Ilya 与 Shrikanth 继续对齐解耦方案——Shrikanth 提出可用 `CONFIG_HAVE_PV_STEAL_CLOCK_GEN`；Ilya 反驳非优化 static call 即将落地、不理想，定论 `HAVE_CPUTIME_STEAL` 是最佳（既不要求 PARAVIRT，又不规定他架构如何实现 steal time 记账）。

## 背景与问题

（承接 sched-20261102-004）首选 CPU mask 只供 steal governor 在 vCPU 抢占时动态缩减 vCPU 需求；patch 1 想放宽 PREFERRED_CPU 对 PARAVIRT 的依赖——动机是 IBM s390 LPAR 硬件辅助虚拟化不启用 PARAVIRT，而 preferred cpumask 并不依赖 PARAVIRT 门控的任何特性。

## 技术方案

（承接）Peter 已给出 `HAVE_CPUTIME_STEAL`（s390 直接 select、PPC pseries 经 PPC_SPLPAR select）的表达方式。今日进一步澄清为何它优于其它候选。

## 版本演进与当前进展

*current_version: v1（patch 1/6，msgid 未在昨日缓存；今日仍 v1）*。今日为 s390 侧两位开发者的方案选择讨论。

## Maintainer 意见与讨论焦点

Shrikanth Hegde 建议「或可用 `CONFIG_HAVE_PV_STEAL_CLOCK_GEN`（定义 dummy 实现、不改方法），这样 PARAVIRT_TIME_ACCOUNTING 大多仅靠 kconfig 改动即可；但需架构实现 static call，不确定 s390 是否具备」。Ilya Leoshkevich 反驳：非优化 static call 很快落地（引用 heiko linux-s390 系列），此路不理想；并自行收回 CFI-gated static call 的念头；结论 `HAVE_CPUTIME_STEAL` 最好——「允许在不做 steal time 记账的系统上禁用 PREFERRED_CPU 与 STEAL_GOVERNOR，又不像 PARAVIRT/PARAVIRT_TIME_ACCOUNTING/HAVE_PV_STEAL_CLOCK_GEN 那样规定其它架构如何实现 steal time」。无反对者，方案共识已形成。

## 合入评估

*likelihood=unknown*。就 Kconfig 解耦达成了技术共识（HAVE_CPUTIME_STEAL），但该 patch 属于已被整体 NAK 的系列中「幸存的子 patch」，需作者单独重投。*next_action*：作者把 patch 1 单独抽出、按 HAVE_CPUTIME_STEAL 方案改后重投。

## 效果评估

无性能数据；纯 Kconfig/配置可维护性改进。

## 我可以参与的点

- new_patch：按达成的 HAVE_CPUTIME_STEAL 方案把 patch 1 单独抽出重投（回合到自家分支也属 new_patch）。
- review：核对 HAVE_CPUTIME_STEAL 在 s390/PPC pseries 之外的架构上是否误伤 PREFERRED_CPU 使用者。

## 参考链接

- lore thread（今日 Ilya 回帖）: https://lore.kernel.org/all/aecd7142-ee54-4cf9-80aa-3546cc2661e3@linux.ibm.com/

---
id: sched-20261103-018
date: 2026-11-03
subject: "sched: decouple PREFERRED_CPU from PARAVIRT in Kconfig.preempt"
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: null
lore_url: "https://lore.kernel.org/all/aecd7142-ee54-4cf9-80aa-3546cc2661e3@linux.ibm.com/"
authors: [Yury Norov]
maintainers_involved: []
current_version: v1
patch_series:
  - version: v1
    msgid: null
    date: 2026-11-02
    summary: "把 PREFERRED_CPU 从 PARAVIRT 解耦为独立可配选项（HAVE_CPUTIME_STEAL 方案）。"
    review_outcome: "s390 侧 Ilya/Shrikanth 达成 HAVE_CPUTIME_STEAL 共识；Peter NAK 了整体系列方向。"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues: ["属于已被整体 NAK 的系列，需单独重投"]
  next_action: "按 HAVE_CPUTIME_STEAL 方案单独抽出 patch 1 重投。"
contribution_opportunities:
  - kind: new_patch
    description: "按 HAVE_CPUTIME_STEAL 方案单独抽出并重投 Kconfig 解耦补丁。"
  - kind: review
    description: "核对 HAVE_CPUTIME_STEAL 在 s390/PPC 之外架构的影响。"
generated_at: "2026-11-04T09:00:00+08:00"
source_email_count: 3
related_articles: [sched-20261102-004]
tags: [affinity]
---