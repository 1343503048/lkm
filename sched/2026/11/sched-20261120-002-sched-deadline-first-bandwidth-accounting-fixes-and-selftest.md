# sched/deadline: first bandwidth accounting fixes and selftests

## TL;DR

本文为增量更新，完整脉络见下。

- sched-20261105-001：Mathieu Desnoyers 的 v2（21 补丁）修 17 个 SCHED_DEADLINE 带宽记账 bug，Ingo 要求「严格只含 -stable 可回退修复的子集」。
- sched-20261106-001 … 20261110-009：v3 → v4 → v5，Juri 持续评审。
- sched-20261118-001：v7 扩到 40 补丁，Juri 提出拆分地基子集先行合入。
- sched-20261119-001：拆分落地，本「first」系列一天内迭代 v1→v3（17 补丁=14 修复+1 sched_debug+2 selftests）。
- sched-20261120-002（今天）：**v4 因发信脚本问题 RESEND 后继续推到 v5（17 补丁）**。Juri 实测 v5 全绿（`deadline_switch_test` 5/5、`deadline_bw_test` 46/47、sched_ext selftests 40/40、`test_cpuset_prs.sh` 过、lockdep 无 splat），并表态「**starting to look good**」；对 0-lag 溢出 patch（10/17）给 Reviewed-by + 一个可读性 nit。地基子集距收取仅一步之遥。

## 背景与问题

（承接 sched-20261119-001）这是 Juri 提议拆分后、Mathieu 落地拆出的「地基」系列：14 个修复（v7 编号 1-8、10、13、14、16、20、37）+ 1 个 sched_debug + 2 个 selftests。其中 2 个可直接打死内核——patch 4（root domain active CPU 数为 0 的除零崩溃）与 patch 8（从被清零参数 refill boost 导致 owner CPU lockup）；patch 6 让 `sysrq-n` 遗留 `cpuset_mutex`；patch 7 让 throttled 任务切出再切回后永不运行；其余是 `total_bw`/`this_bw` 记错导致 root domain 超额接纳或一律拒收 deadline 任务。修复在前、`-stable` 可截取 patches 1-14。

## 技术方案

（承接 v1-v3 结构）14 修复 + sched_debug + 2 selftests。patch 11「Release the bandwidth of a task that leaves the class asleep」与 patch 12「Reject SCHED_DEADLINE on exited tasks」为 Juri 的修复、patch 14「Check the affinity of a deadline task under the runqueue lock」为 Andrea Parri 的修复，Mathieu 原样携带；Juri 被 Ingo drop 的 4 个修复里 3 个在此（1/4 留在第二系列）。patch 10「Fix an overflow of the 0-lag time with long periods」把 0-lag 时间改 128 位计算，避免长 period 晚数秒才释放带宽。

## 版本演进与当前进展

*current_version: v5（2026-11-20，`<cover.1795115075.git.mathieu.desnoyers@efficios.com>`，17 补丁）*。

- **v4**（`<cover.1795103339.git.mathieu.desnoyers@efficios.com>`）：拆分后 v3 之后的新版；因发信脚本问题（`<85b926c7-…@efficios.com>`「Issues with my patch send script. Will resend.」）RESEND 一次。
- **RESEND v4**（`<cover.1795105408.git.mathieu.desnoyers@efficios.com>`）：v4 重发。
- **v5**（`<cover.1795115075.git.mathieu.desnoyers@efficios.com>`）：按 Juri 对 v4 的意见修订（0-lag patch 10 收编与排序等）。

## Maintainer 意见与讨论焦点

- **Juri Lelli（sched/deadline 维护者）**：对 v5 给出当日最实质的实测背书——`deadline_switch_test` 5/5、`deadline_bw_test` 46/47（`move_cancelled` 无 RT_GROUP_SCHED 跳过）、sched_ext selftests 40/40（server 用例跑在 ext_server、hotplug_server 跳过）、`test_cpuset_prs.sh` 通过、lockdep 无 splat；据此让作者从 cover 删除「not tested with sched_ext」，并表态「I have the impression this is starting to look good」。对 10/17 给 Reviewed-by + 建议抽 helper、每处检查前写清比较对象、补 tip 括号规范的可读性 nit（「不必为它重发整个系列，单独更新这一个 patch 即可」）。
- **sashiko-bot（AI review 机器人，非维护者）**：对 v5 09/17 提示 2 个 Medium（PI deboost 后 donor runtime/deadline 未复位、`__dl_clear_params()` 未取消 `dl_timer`）。
- 无 NAK；Juri 的「starting to look good」是系列进入收取前夜的最强信号。

## 合入评估

*likelihood=high*。拆分后的地基子集规模可控、Juri 已给实测背书并明确「starting to look good」，0-lag patch 也获 Reviewed-by；符合 Ingo「修复在前、stable 可截取」的偏好。*blocking_issues*：① 0-lag patch 的可读性重构（抽 helper）待作者出更新版；② sashiko-bot 的 2 个 Medium 需确认是否已被覆盖；③ 等 Ingo/Peter 对「starting to look good」的回应。*next_action*：Mathieu 出 patch 10 的更新版，Juri 复审后由 Ingo 收取 patches 1-14。

## 效果评估

正确性修复，无性能基准。可观测数字：25 个 guest 用例全过；Juri 实测 46/47 通过；v7.4-rc2 上 6 个 `deadline_bw_test` 用例失败（对应修复）。均为作者/维护者自测。

## 我可以参与的点

- **review**：核对 v5 相对 v4 的修订（尤其 patch 10 收编与编号顺延）无遗漏，并判断 sashiko-bot 的 Medium 提示是否已被相邻补丁覆盖。
- **testing**：在 PREEMPT_RT / CONFIG_CPUSETS=n / isolcpus=domain 组合上复跑 `deadline_bw_test`/`deadline_switch_test`，重点验证 patch 4（除零）、patch 6（sysrq-n）、patch 8（owner lockup）三个高危修复。

## 参考链接

- lore thread（v5 cover）: https://lore.kernel.org/all/cover.1795115075.git.mathieu.desnoyers@efficios.com/
- Juri 的 v5 实测: https://lore.kernel.org/all/awBFi0bwFt5KoEq-@jlelli-thinkpadt14gen4.remote.csb/

---
id: sched-20261120-002
date: '2026-11-20'
subject: "sched/deadline: first bandwidth accounting fixes and selftests"
subsystem: sched
type: fix
status: under_review
severity: critical
thread_root_msgid: "<cover.1795115075.git.mathieu.desnoyers@efficios.com>"
lore_url: "https://lore.kernel.org/all/cover.1795115075.git.mathieu.desnoyers@efficios.com/"
authors: [Mathieu Desnoyers, Juri Lelli, Andrea Parri]
maintainers_involved: [Juri Lelli]
current_version: v5
patch_series:
  - version: v4
    msgid: "<cover.1795103339.git.mathieu.desnoyers@efficios.com>"
    date: '2026-11-20'
    summary: "拆分后新一版；发信脚本问题导致 RESEND"
    review_outcome: "作者自述发信脚本故障，重发"
  - version: v5
    msgid: "<cover.1795115075.git.mathieu.desnoyers@efficios.com>"
    date: '2026-11-20'
    summary: "按 Juri 对 v4 意见修订（0-lag patch 10 收编与排序）"
    review_outcome: "Juri 实测全绿并表态 starting to look good；0-lag patch 获 Reviewed-by"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: ["0-lag patch 可读性重构待出更新版", "sashiko-bot 2 个 Medium 待确认覆盖"]
  next_action: "Mathieu 出 patch 10 更新版，Juri 复审后由 Ingo 收取 patches 1-14"
contribution_opportunities:
  - kind: review
    description: "核对 v5 相对 v4 修订无遗漏，判断 sashiko-bot Medium 是否被覆盖"
  - kind: testing
    description: "PREEMPT_RT/CONFIG_CPUSETS=n/isolcpus 组合复跑 self测试验证 patch 4/6/8"
generated_at: "2026-11-21T09:00:00+08:00"
source_email_count: 216
related_articles: [sched-20261105-001, sched-20261106-001, sched-20261107-002, sched-20261108-003, sched-20261109-001, sched-20261110-009, sched-20261118-001, sched-20261119-001]
tags: [deadline, dl_server, cgroup]
---