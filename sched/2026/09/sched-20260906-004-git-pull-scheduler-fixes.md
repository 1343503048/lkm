# [GIT PULL] scheduler fixes

## TL;DR

Ingo 于 09-06 19:22 向 Linus 发出 `sched/urgent` 拉取（分支 `sched-urgent-2026-09-06`，顶端 `f0d243a96f2684ad771d678767d17972cf840bd7`），共 **7 个修复、6 位提交者**，覆盖 fair 时间戳、CFS bandwidth 两处由 single-runqueue 转换引入的缺陷、RT/DL push 候选误选 migrate-disabled 任务、无效 `idle_stamp` 下的 `rq->avg_idle` 更新、hybrid cache-aware 平衡制造 misfit、x86 ITMT 对 debugfs 的依赖。`+64/-22`、5 个文件，其中 `kernel/sched/fair.c` 占 60 行。

## 背景与问题

这是一次常规的 urgent 修复汇总，但内容与 cgroup/cpuset 关系紧密。按 Ingo 的条目列表与 shortlog：

- Zhan Xusheng：`sched/fair: Use update_curr_eevdf() for the remaining root cfs_rq callers` —— `pick_task_fair()` 与 `yield_task_fair()` 的时间戳 bug。
- Wanwu Li ×2：`sched/fair: Use cfs_rq->h_curr in throttle_cfs_rq()`、`sched/fair: Use cfs_rq->h_curr in distribute_cfs_runtime()` —— Ingo 明确写出这两处是 **最近的 single-runqueue 转换引入的** throttling bug 与 bandwidth 计算 bug。
- Seiji Nishikawa：`sched/rt,dl: Skip migrate-disabled tasks when picking a push candidate`。
- Shubhang Kaushik (Ampere)：`sched/core: Skip rq->avg_idle update without a valid idle_stamp`。
- Tim Chen：`sched/fair: Avoid creating misfits during cache-aware balancing`。
- Mario Limonciello：`x86/itmt: Don't make ITMT enablement depend on debugfs`。

## 技术方案

均为针对性小修：fair 类补齐剩余的 root `cfs_rq` 调用点改用 `update_curr_eevdf()`；bandwidth 路径改用转换后的 `cfs_rq->h_curr`；RT/DL 的 push 候选筛选增加 migrate-disabled 跳过；`avg_idle` 更新前先确认 `idle_stamp` 有效。无架构性改动。改动文件为 `arch/x86/kernel/itmt.c`(8)、`kernel/sched/core.c`(10)、`kernel/sched/deadline.c`(4)、`kernel/sched/fair.c`(60)、`kernel/sched/rt.c`(4)。

## 版本演进与当前进展

`tip/sched/urgent` 已含全部 7 个 commit，Ingo 以正式 pull request 发给 Linus。本次邮件中没有 Linus 的合并确认，也没有 tip-bot 回执，因此进入主线的确切时点未获取到（此类 urgent 拉取按惯例会在近期合并窗口被拉取）。

## Maintainer 意见与讨论焦点

拉取请求本身没有讨论线程；意见体现在 Ingo 对内容的归类措辞上——他把其中两条明确定性为「caused by the recent single-runqueue conversion」的回归（Wanwu Li），而不是普通 bug。这等于维护者承认该转换的收尾工作不完整：throttle 与带宽重分配这两个 `cgroup cpu.max` 的核心路径都在漏改的调用点里。其余条目为独立修复。本邮件中未出现 Peter Zijlstra 的署名或任何说明，正文只署 Ingo 一人。

## 合入评估

`likelihood=merged`。依据：这是发给 Linus 的正式 pull request，分支内容与顶端 commit 均已确定，urgent 拉取通常会被直接合并。卡点：无。需要注意的两点判断依据：一是合并动作本身本日尚未出现在邮件里（未获取到）；二是是否走 `Cc: stable` 由 Linus/维护者决定，本邮件中未见 stable 标记，逐个 commit 的 `Fixes:` 情况需到 tip 树里看。

## 效果评估

邮件中未提供效果数据（pull request 无 benchmark）。可量化的只有规模与分布：`5 files changed, 64 insertions(+), 22 deletions(-)`，其中 `kernel/sched/fair.c` 60 行变更集中了 fair 时间戳、bandwidth 与 misfit 三类修复。收益属正确性一类：EEVDF 时间戳不再漏更新、`cpu.max` 节流与带宽重分配不再走错 `cfs_rq`、migrate-disabled 任务不再被 RT/DL push、空闲统计不再被无效 `idle_stamp` 污染。

## 我可以参与的点

- 回合自查（与本用户工作最直接相关）：若 OLK-6.6 已带 single-runqueue/`h_curr` 那一层转换，务必同时带上 Wanwu Li 的 `throttle_cfs_rq()` 与 `distribute_cfs_runtime()` 两片——它们直接影响 cgroup `cpu.max` 的节流与带宽重分配正确性；只回合转换而漏这两片会表现为「偶发过度节流 / 带宽配额算错」，很难从现象定位到根因。
- cpuset 场景复核：`sched/rt,dl: Skip migrate-disabled tasks when picking a push candidate` 值得在「RT/DL 任务被 cpuset 绑核 + 中断隔离」的机器上验证上游行为，并确认自己分支在挑 push 候选时是否同样缺这层 migrate-disabled 筛选。
- 观察 `rq->avg_idle` 一片：该项会影响 wakeup 路径的 idle 判定与 `select_task_rq` 决策，若有调度延迟回归排查，可以顺手确认回合后 `idle_stamp` 有效性检查是否生效。
- 跟踪本 pull 合入后的 stable 回合队列（本日邮件中无 stable 迹象）。

## 参考链接

- pull request: https://lore.kernel.org/all/ap1NEllrD8nMsFiB@gmail.com/
- tip-bot commit: f0d243a96f2684ad771d678767d17972cf840bd7（`sched-urgent-2026-09-06` 顶端，取自 pull 正文）
- stable backport: 未获取到

---
id: sched-20260906-004
date: '2026-09-06'
subject: '[GIT PULL] scheduler fixes'
subsystem: sched
type: discussion
status: merged_tip
severity: medium
thread_root_msgid: <ap1NEllrD8nMsFiB@gmail.com>
lore_url: https://lore.kernel.org/all/ap1NEllrD8nMsFiB@gmail.com/
upstream_commit: f0d243a96f2684ad771d678767d17972cf840bd7
fixes_commit: null
merged_branch: tip/sched/urgent
current_version: v1
generated_at: '2026-09-07'
authors:
- Ingo Molnar
maintainers_involved:
- Ingo Molnar
patch_series:
- version: v1
  msgid: <ap1NEllrD8nMsFiB@gmail.com>
  date: '2026-09-06'
  summary: 'Ingo 向 Linus 拉取 tip/sched/urgent（分支 sched-urgent-2026-09-06，顶端 f0d243a96f2684ad771d678767d17972cf840bd7），7 个修复：Zhan Xusheng - sched/fair: Use update_curr_eevdf() for the remaining root cfs_rq callers；Wanwu Li - sched/fair: Use cfs_rq->h_curr in throttle_cfs_rq() 与 Use cfs_rq->h_curr in distribute_cfs_runtime()（均标注由 recent single-runqueue conversion 引起）；Seiji Nishikawa - sched/rt,dl: Skip migrate-disabled tasks when picking a push candidate；Shubhang Kaushik - sched/core: Skip rq->avg_idle update without a valid idle_stamp；Tim Chen - sched/fair: Avoid creating misfits during cache-aware balancing；Mario Limonciello - x86/itmt: Don''t make ITMT enablement depend on debugfs。diffstat 5 files, +64/-22。'
  review_outcome: 正式 pull request，无讨论线程；tip 侧内容已定，本日邮件中未见 Linus 合并确认
merge_assessment:
  likelihood: merged
  blocking_issues:
  - 无技术卡点；本邮件中未获取到 Linus 的合并确认与 stable 标记，进主线时点与是否回合 stable 待跟踪
  next_action: 确认该 pull 被合入哪个 -rc，并跟踪 sched/urgent 各 commit 的 stable 回合队列；优先自查 single-runqueue 转换 + h_curr 两片在自有分支的完整性
contribution_opportunities:
- kind: new_patch
  description: 若分支已带 single-runqueue/h_curr 转换，核对 throttle_cfs_rq() 与 distribute_cfs_runtime() 是否也已改用 cfs_rq->h_curr（cgroup cpu.max 节流与带宽重分配路径）
- kind: testing
  description: 在 RT/DL 任务被 cpuset 绑核并配合中断隔离的机器上，验证 push 候选跳过 migrate-disabled 任务前后的行为差异
source_email_count: 1
related_articles: []
tags:
- sched/fair
- rt
- deadline
- sched/core
---
