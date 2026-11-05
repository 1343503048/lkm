# cpufreq: Fix global boost state updates

## TL;DR

Christian Loehle 的 v2 两补丁修复 cpufreq 全局 boost 状态的两个缺陷：更新失败时保持原 boost 状态（不回退也不误置）、以及串行化并发的全局 boost 写。v2 按 Zhongqiu Han 意见拆成两个补丁并各带 Fixes，已获 Pengjie Zhang、Sumit Gupta、Zhongqiu Han 的 Reviewed-by；仅剩 Sumit 提出的「`cpufreq_boost_trigger_state()`/`cpufreq_online()` 未持 policy 锁、可能与 per-policy 写者（如 ospm_nominal_freq）竞态」一点待澄清。

## 背景与问题

cpufreq 的全局 `boost` sysfs（`/sys/devices/system/cpu/cpufreq/boost`）在更新失败时会残留不一致的状态（原补丁发现更新失败后 boost 状态被破坏）；同时并发的全局 boost 写彼此竞争、没有串行化，可能导致最终状态与最后一次写入不一致。v1 单补丁混合了「回退」与「串行化」两件事，Zhongqiu Han 建议拆开并分别补 `Fixes` 标签。

## 技术方案

- patch 1（Preserve global boost state on failed updates）：更新失败时保持原全局 boost 状态。
- patch 2（Serialize global boost updates）：给全局 boost 更新加锁/串行化，消除并发写竞态。

## 版本演进与当前进展

*current_version: v2（2026-11-05）*。v1（11-04 单补丁）→ v2 拆成两补丁、各带 Fixes，并继承 Pengjie Zhang 的 Reviewed-by。今日 Sumit Gupta、Zhongqiu Han 分别评审。

## Maintainer 意见与讨论焦点

无 cpufreq 维护者（Rafael）直接回本线程，但多位驱动作者/资深 reviewer 表态：patch 1 获 Pengjie Zhang、Sumit Gupta、Zhongqiu Han 三个 Reviewed-by；patch 2 获 Zhongqiu Han Reviewed-by（附小意见：扩展 commit message 描述竞态），但 Sumit Gupta 提出开放问题——per-policy boost 属性在持有 `policy->rwsem` 时调 `policy_set_boost()`，而 `cpufreq_boost_trigger_state()` 与 `cpufreq_online()` 未持锁，仍可能与 ospm_nominal_freq 等 per-policy 写者竞态，建议让前者像 `cpufreq_suspend()` 一样用 `scoped_guard(cpufreq_policy_write)` 取锁。Zhongqiu 请 Sumit 核对一个后续补丁（be3739f8-e668...@arm.com）是否覆盖该问题。

## 合入评估

*likelihood=medium*。方向与实现获多方 Reviewed-by，但 patch 2 的 policy 锁竞态问题（Sumit 提出）尚未闭环。*blocking_issues*：`cpufreq_boost_trigger_state()`/`cpufreq_online()` 未持 policy 锁的竞态是否由本系列或后续补丁覆盖。*next_action*：作者回应 Sumit 的锁竞态问题，确认是否并入本系列或由后续补丁承接。

## 效果评估

无性能数据；这是状态一致性与竞态修复，未涉及效果测量。

## 我可以参与的点

- review：核对 `cpufreq_boost_trigger_state()` 与 per-policy 写者（ospm_nominal_freq）的竞态窗口，确认 Sumit 提出的 policy 锁方案是否完备。
- testing：在多驱动平台上做并发 boost sysfs 写 + 失败注入，验证状态始终一致。

## 参考链接

- lore thread（v2 cover）: https://lore.kernel.org/all/20261105090311.1026648-1-christian.loehle@arm.com/
- v1: https://lore.kernel.org/r/20261104161657.546370-1-christian.loehle@arm.com

---
id: sched-20261105-017
date: 2026-11-05
subject: "cpufreq: Fix global boost state updates"
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: "<20261105090311.1026648-1-christian.loehle@arm.com>"
lore_url: "https://lore.kernel.org/all/20261105090311.1026648-1-christian.loehle@arm.com/"
authors: [Christian Loehle]
maintainers_involved: []
current_version: v2
patch_series:
  - version: v1
    msgid: "<20261104161657.546370-1-christian.loehle@arm.com>"
    date: 2026-11-04
    summary: "单补丁：失败时保持 boost 状态 + 串行化并发写。"
    review_outcome: "Zhongqiu 建议拆分并补 Fixes。"
  - version: v2
    msgid: "<20261105090311.1026648-1-christian.loehle@arm.com>"
    date: 2026-11-05
    summary: "拆成 2 补丁（回退/串行化），继承 Pengjie Reviewed-by。"
    review_outcome: "Sumit/Zhongqiu Reviewed-by；Sumit 提 policy 锁竞态开放问题。"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
    - "cpufreq_boost_trigger_state/cpufreq_online 未持 policy 锁的竞态未闭环"
  next_action: "作者回应 Sumit 的锁竞态问题，确认归属本系列或后续补丁"
contribution_opportunities:
  - kind: review
    description: "核对 boost_trigger_state 与 per-policy 写者的竞态窗口"
  - kind: testing
    description: "并发 boost sysfs 写 + 失败注入验证状态一致性"
generated_at: "2026-11-06T09:00:00+08:00"
source_email_count: 7
related_articles: []
tags: [cpufreq]
---