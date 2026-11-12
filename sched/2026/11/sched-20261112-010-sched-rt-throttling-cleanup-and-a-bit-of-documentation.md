# sched: RT throttling cleanup and a bit of documentation

## TL;DR

本文为增量更新，完整脉络见下。

- sched-20261111-001：Sebastian Andrzej Siewior 发 v2 七补丁系列梳理 RT throttling 历史包袱（标记 RT_GROUP_SCHED broken、DL 准入控制迁 sysfs、新增 per-CPU fair_server sysfs、rcutorture 迁移、文档更新）。Paul E. McKenney 认可但指出系列仍带一个 divide-by-zero 问题，Randy Dunlap 提了文档 nit。
- sched-20261112-010（今天）：**Juri Lelli 追问该系列是否与 Mathieu Desnoyers 的 dl_server 修复（patch 06/29）重叠**；**Sebastian 解释其 rcutorture dl_server 处理**（把更新延迟到跑在 CPU 上的线程、`cpu_online()` 改 `cpu_active()`、仍会 abort 未上线 CPU，替代方案是 RCU_TORTURE 内建时跳过 `sched_init_dl_servers()`）；**Randy Dunlap 对 1/7（Mark RT_GROUP_SCHED broken）给 LGTM**。

## 背景与问题

（承接 sched-20261111-001）RT throttling 早被 fair_server（SCHED_DEADLINE server）接管，`-1` 不再真正关闭 RT throttling；DL 准入控制与 RT 共用 proc 文件且 RT_GROUP_SCHED 启用时被卡死；RT_GROUP_SCHED 在 cgroup v2 下无法给任务组分配 runtime、发行版普遍默认关闭。今日焦点转向 rcutorture 与 `sched_init_dl_servers()` 的交互——这是 Paul 报告的 divide-by-zero 与 Mathieu 的 dl_server 修复共同指向的区域。

## 技术方案

（承接七补丁）今日围绕 rcutorture 补丁的技术细节：Sebastian 解释他把 dl_server 相关更新延迟到「跑在 CPU 上的线程」执行，并把 `cpu_online()` 检查换成 `cpu_active()`——但仍会在 CPU 未上线时 abort；另一个替代是「RCU_TORTURE 内建时直接跳过 `sched_init_dl_servers()`」。并给出边角提示：`maxcpus=2` 启动 4 CPU 系统时 CPU 2/3 处于 offline，`sched_init_dl_servers()` 不会初始化它们（可手动上线）。

## 版本演进与当前进展

*current_version: v2（2026-11-10，`<20261110-sched_dl-v2-0-cc9399f7aeb1@linutronix.de>`）*。今日无新版本，为评审收口：Randy 对 1/7 LGTM，作者就 rcutorture dl_server 处理回应 Juri 的交叉引用问题。

## Maintainer 意见与讨论焦点

- **Juri Lelli（deadline 维护者）**：把本系列与 Mathieu Desnoyers 的 DL 带宽记账系列（v5，`20261108185406.1549770-6-mathieu.desnoyers@efficios.com`）关联起来，问「这是否修复了那个问题」——即 rcutorture 对 fair_server 的关闭是否与 Mathieu 修的 dl_server 相关缺陷重叠。
- **Sebastian Andrzej Siewior（作者）**：回应其 rcutorture 处理方式（cpu_active 检查 + abort + 可选跳过），解释了 `maxcpus` 场景下 `sched_init_dl_servers()` 不初始化 offline CPU 的语义。
- **Randy Dunlap**：对 1/7 `Mark RT_GROUP_SCHED broken` 给「LGTM」。
- 无 NAK。仍悬而未决的是 Paul 报告的 divide-by-zero 是否已在 v2 中解决（今日讨论间接触及但未明确确认）。

## 合入评估

*likelihood=medium*。1/7 已获 Randy LGTM，方向持续获认可，但 Paul 的 divide-by-zero 与 Juri 的 dl_server 交叉引用都指向 rcutorture/fair_server 交互仍需进一步厘清。*blocking_issues*：Paul 报告的 rcutorture divide-by-zero 是否修复仍未明确确认；与 Mathieu dl_server 修复的关系待澄清。*next_action*：作者确认 v2 是否修复 divide-by-zero 并回复 Paul/Juri；明确与 Mathieu 系列的边界。

## 效果评估

暂无性能数据。本系列为 ABI 语义整理（procfs→sysfs、标记 broken），作者此前说明动机是「改了却不生效」的误导性接口，无 benchmark。

## 我可以参与的点

- **testing**：复现 Paul 报告的 divide-by-zero（rcutorture 场景禁用/重建 fair_server 或写 DL 准入控制），确认 v2 是否修复并在线程回帖。
- **discussion**：厘清 Sebastian 的 rcutorture dl_server 处理与 Mathieu 的 DL 带宽记账修复（patch 06/29）是否针对同一根因，避免两系列重复或遗漏。

## 参考链接

- lore thread: https://lore.kernel.org/all/20261110-sched_dl-v2-0-cc9399f7aeb1@linutronix.de/
- Juri 的交叉引用: https://lore.kernel.org/all/avXUstjABxdTZaxM@jlelli-thinkpadt14gen4.remote.csb/
- Sebastian 对 rcutorture 处理的解释: https://lore.kernel.org/all/20261112152446.r1FzXVCR@linutronix.de/

---
id: sched-20261112-010
date: '2026-11-12'
subject: "sched: RT throttling cleanup and a bit of documentation"
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: "<20261110-sched_dl-v2-0-cc9399f7aeb1@linutronix.de>"
lore_url: "https://lore.kernel.org/all/20261110-sched_dl-v2-0-cc9399f7aeb1@linutronix.de/"
authors: [Sebastian Andrzej Siewior]
maintainers_involved: [Paul E. McKenney, Randy Dunlap, Juri Lelli]
current_version: v2
patch_series:
  - version: v1
    msgid: "<20261105164724.yxONBd03@linutronix.de>"
    date: '2026-11-05'
    summary: "从 RFC 改为正式系列，先标记 RT_GROUP_SCHED broken 再解耦 DL 接口"
    review_outcome: "Tejun 与 Peter Zijlstra 要求先标记 broken"
  - version: v2
    msgid: "<20261110-sched_dl-v2-0-cc9399f7aeb1@linutronix.de>"
    date: '2026-11-10'
    summary: "新增 sysfs per-CPU fair_server 旋钮、DL 准入控制迁 sysfs、rcutorture 迁移"
    review_outcome: "Randy LGTM 1/7；Juri 交叉引用 Mathieu dl_server 修复；divide-by-zero 待确认"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues: ["Paul 报告的 rcutorture divide-by-zero 是否修复未确认", "与 Mathieu dl_server 修复的关系待澄清"]
  next_action: "确认 divide-by-zero 是否修复并回复 Paul/Juri"
contribution_opportunities:
  - kind: testing
    description: "复现 Paul 的 divide-by-zero 并验证 v2 是否修复"
  - kind: discussion
    description: "厘清 rcutorture dl_server 处理与 Mathieu DL 修复是否同根因"
generated_at: "2026-11-13T09:00:00+08:00"
source_email_count: 3
related_articles: [sched-20261111-001]
tags: [rt, dl_server, rt_bandwidth, cgroup]
---