# sched/deadline: Keep departing bandwidth across a root domain rebuild

## TL;DR

本文为增量更新，完整脉络见下。

- sched-20261105-001：Mathieu Desnoyers 的 v2 系列（21 补丁）在 Juri Lelli 此前 4 个 sched/urgent 修复之上再修 17 个 SCHED_DEADLINE 带宽记账 bug（其中 3 个可直接打死内核），带自测与 sched_debug。Juri 已对多数补丁给 Reviewed-by/Acked-by；Ingo 要求「严格只含 -stable 可回退修复的子集」。
- sched-20261106-001：v3 发出，扩到 24 补丁，吸收 Juri 被 Ingo 丢弃的 4 个 sched/urgent 修复。
- sched-20261107-002：v4 发出，扩到 26 补丁。
- sched-20261108-003：作者逐条回应 sashiko-bot 对 9 个补丁的评审，并披露 v5 计划。
- sched-20261109-001：v5 发出（29 补丁，25 修复 + sched_debug + 3 自测）。Juri 评审 patch 03/04/06 给 Reviewed-by。
- sched-20261110-009：Juri 评审 patch 07/08/09——07/09 给 Acked-by，08（deadline boost）Juri 提出两个 stop-gap 备选并质疑整套 PI 机制。
- sched-20261111-006（今天）：**Juri 评审 patch 11–16/29**——12/14 给 Reviewed-by；11/29 建议用 `task_non_contending()` 收敛 if-else（Mathieu 采纳进 v6）；13/29 深入讲解 `dl_bw_gen` 并给出「任务离开→迁移→被 PI 提升→deboost」会让带宽从错误的 root domain 扣除的确定性场景，且提出「单链表按 home CPU 重建」的替代方案；15/29 提醒 Android suspend/resume 回归历史并请 Android 侧确认。Mathieu 逐条回应并确认 v6 计划。

## 背景与问题

（承接 sched-20261105-001 / 20261106-001 / 20261107-002 / 20261108-003 / 20261109-001 / 20261110-009）Juri Lelli 前一轮 4 个 SCHED_DEADLINE 带宽记账修复被 Ingo 从 tip/sched/urgent 移除，Mathieu Desnoyers 系统梳理 dl_bw/total_bw/this_bw 记账边界缺陷，按 Ingo「修复在前、stable 可截取」推到 v5（29 补丁）。今日评审焦点转向「root domain 重建时 departing bandwidth 的归属」这组最微妙、带 cpuset 纠缠的补丁（patch 13/15/16）。

## 技术方案

今日围绕四个补丁：

- **11/29 `Release the bandwidth of a task that leaves the class asleep`**：Juri 建议把 open-coded 的 if-else 收敛成 `task_non_contending()` 等价形式（`sub_rq_bw()` 须在清参数之前）。Mathieu 认可「sub_rq_bw() 必须在清参数（dl_bw 置 0）之前」，v6 采纳 Juri 版本；后四个改到同一分支的补丁在 v6 里只改 `task_non_contending()`。
- **13/29 `Keep departing bandwidth across a root domain rebuild`**：Juri 用注释讲清 `dl_bw_gen` 的三态（Current/One behind/Older，只比较相等、计数回绕无害），并给出确定性反例——任务离开 DL 类休眠（带宽 X 记在 rd(A)）→ 迁移到 rd(B) → 被 DL waiter PI 提升回来（`dl_task_undepart()` 清掉 `dl_departed_cpu`）→ deboost 时 `dl_task_release_bw(p, task_cpu(p))` 从 rd(B) 扣掉 X，而 X 其实在 rd(A)。Mathieu 确认该场景在 patch 13 处确实发生且当时无测试（rd(B) total_bw 变负、rd(A) 残留 X），v6 让「被 boost 取走任务时保留记录的 CPU」使系列可 bisect，并新增 `pi_departed_moved` 自测。
- **15/29 `Rebuild the root domains' accounting from the task list`**：Juri 提醒被移除的计数是当年 Qais 报告 Android 10-20ms suspend/resume 回归后加的、且旧 fix 只在「无 DL」系统上验证过；新 walk 丢掉了占主导的 per-task pi_lock，可能没问题，但因带 `Cc: stable`、最终会到 Android，建议先让 Android 侧确认，或加一个「是否存在 DL 任务」的全局 bail。Mathieu 认可并在 13/29 回复中给出了实测数据（见效果评估）。
- **16/29 `Record the root domain holding a task's bandwidth`**：Juri 指出该计数不在 `dl_departed_lock` 保护内（但后续补丁会修），并讨论 1024ns/2s 这种 dl_bw 为 0 的边角是否需要强制最小 1。

## 版本演进与当前进展

*current_version: v5（2026-11-08，`<20261108185406.1549770-1-mathieu.desnoyers@efficios.com>`）*。v6 已明确计划：11/29 采纳 Juri 版本、13/29 保留「boost 取走任务时的 CPU 记录」+ 新增 `pi_departed_moved` 自测、`dl_clear_root_domains()` 计数函数更名。统一单链表替代方案（见下）被否决，不进 v6。

## Maintainer 意见与讨论焦点

- **Juri Lelli（deadline 维护者）**：对 12/14 给 Reviewed-by；13/29 提出统一单链表替代方案（「把 rebuild 从重构变成 re-partition，`dl_bw_gen` 与 cpuset walk 都去掉」）作为「落地后再议」的后继方向。
- **Mathieu Desnoyers（作者）**：实做并测试了单链表方案——rebuild 本身快 8 倍（extra_bw 从每任务更新改为每 root domain 更新一次），但最长关中断段随 deadline 任务数增长（1000 任务 0.12ms、10000 任务 0.9ms），对实时类不是进步，故 v6 不用，可作为 RFC 另发。
- 无 NAK。分歧集中在「是否值得为消除 per-task 记账复杂度而牺牲中断延迟」这一架构权衡上。

## 合入评估

*likelihood=high*。多数补丁已获 Juri Reviewed-by/Acked-by，v6 计划明确、作者响应积极。*blocking_issues*：15/29 需 Android 侧对 suspend/resume 回归的确认（Juri 明确要求）；Ingo 此前要求的「stable 可截取子集」如何切分仍需落实。*next_action*：作者发 v6，并等 Android 侧（Qais/相关）对 15/29 的表态。

## 效果评估

Mathieu 给出单链表替代方案的实测（64-vCPU guest、睡眠 deadline 任务）：rebuild 最长关中断段——今天（cpuset walk）1000 任务 0.75ms/10000 任务 7.4ms；单链表 0.12ms/0.9ms（rebuild 快 8 倍，但关中断时间随任务数线性增长）。该数据用于论证「替代方案不可取」，不是补丁收益。系列本身的正确性收益无量化数据（修复的是记账错误，部分可致内核 panic）。

## 我可以参与的点

- **testing**：在 Android 或等效的「suspend/resume + SCHED_DEADLINE」环境复测 15/29，确认新 walk 不再引入 10-20ms 的 suspend/resume 回归（这正是 Juri 点名要的确认）。
- **review**：复核 13/29 的 `dl_bw_gen` 三态注释与 Mathieu 提出的「单链表」RFC（作者说可另发），评估是否值得以中断延迟换取记账简化。

## 参考链接

- lore thread: https://lore.kernel.org/all/20261108185406.1549770-1-mathieu.desnoyers@efficios.com/
- Juri 对 13/29 的评审: https://lore.kernel.org/all/avRmoK08LoIeySBL@jlelli-thinkpadt14gen4.remote.csb/
- Mathieu 对 13/29 的回复: https://lore.kernel.org/all/c3e7054a-486c-4e5a-a646-eee42e815ce4@efficios.com/

---
id: sched-20261111-006
date: '2026-11-11'
subject: "sched/deadline: Keep departing bandwidth across a root domain rebuild"
subsystem: sched
type: fix
status: under_review
severity: critical
thread_root_msgid: "<20261108185406.1549770-1-mathieu.desnoyers@efficios.com>"
lore_url: "https://lore.kernel.org/all/20261108185406.1549770-1-mathieu.desnoyers@efficios.com/"
authors: [Mathieu Desnoyers]
maintainers_involved: [Juri Lelli]
current_version: v5
patch_series:
  - version: v5
    msgid: "<20261108185406.1549770-1-mathieu.desnoyers@efficios.com>"
    date: '2026-11-08'
    summary: "29 补丁：25 个 DL 带宽记账修复 + sched_debug + 3 自测"
    review_outcome: "Juri 对 12/14 给 Reviewed-by，11/13/15/16 有实质反馈；v6 计划明确"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: ["15/29 需 Android 侧确认 suspend/resume 无回归", "Ingo 要求的 stable 可截取子集切分待落实"]
  next_action: "作者发 v6，等待 Android 侧对 15/29 的表态"
contribution_opportunities:
  - kind: testing
    description: "在 Android/等效环境复测 15/29 的 suspend/resume 是否回归"
  - kind: review
    description: "评估 13/29 单链表替代方案（以中断延迟换记账简化）是否值得作为 RFC 推进"
generated_at: "2026-11-12T09:00:00+08:00"
source_email_count: 8
related_articles: [sched-20261105-001, sched-20261106-001, sched-20261107-002, sched-20261108-003, sched-20261109-001, sched-20261110-009]
tags: [deadline, cgroup]
---
