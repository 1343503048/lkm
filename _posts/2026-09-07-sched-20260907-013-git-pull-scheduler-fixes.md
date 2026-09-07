---
id: sched-20260907-013
date: '2026-09-07'
subject: '[GIT PULL] scheduler fixes'
subsystem: sched
type: fix
status: merged_tip
severity: medium
thread_root_msgid: <ap1NEllrD8nMsFiB@gmail.com>
lore_url: https://lore.kernel.org/all/178871829440.1639575.4127304395444817583.pr-tracker-bot@kernel.org/
upstream_commit: 88405f0ad1d5c680afe3ea0ce9345fa9e1deaac8
fixes_commit: null
merged_branch: torvalds/linux.git（经 tip/sched/urgent 的 sched-urgent-2026-09-06）
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
  summary: Ingo 向 Linus 拉取 tip/sched/urgent（sched-urgent-2026-09-06，顶端 f0d243a96f2684ad771d678767d17972cf840bd7）：7
    个修复、6 位提交者、5 files +64/-22，含 fair 时间戳（Zhan Xusheng）、CFS bandwidth 两处 h_curr（Wanwu
    Li，Ingo 定性为 recent single-runqueue conversion 引入）、RT/DL push 跳过 migrate-disabled（Seiji
    Nishikawa）、无效 idle_stamp 下跳过 rq->avg_idle 更新（Shubhang Kaushik）、cache-aware 平衡避免制造
    misfit（Tim Chen）、x86 ITMT 不依赖 debugfs（Mario Limonciello）。逐条细节见前作 sched-20260906-004。
  review_outcome: 无讨论线程；本日 09-07 02:11 pr-tracker-bot 回执确认已合入 torvalds/linux.git，落地链接
    88405f0ad1d5c680afe3ea0ce9345fa9e1deaac8，从发出到进主线不足 7 小时。stable 回合情况未获取到。
merge_assessment:
  likelihood: merged
  blocking_issues:
  - 无：本批 7 条修复已全部进入 mainline，urgent 流程闭环
  - 落到哪个 -rc 序号、以及逐条是否进 stable 队列，本线程邮件中均未出现
  next_action: 按文件（尤其 kernel/sched/fair.c，60 行变更集中于此）逐条与内部分支比对是否已带；优先核对 throttle_cfs_rq()/distribute_cfs_runtime()
    的 h_curr 两片；跟踪 stable 回合队列
contribution_opportunities:
- kind: new_patch
  description: 回合自查——若内部分支已带 single-runqueue/h_curr 转换，核对 throttle_cfs_rq() 与 distribute_cfs_runtime()
    是否也已改用 cfs_rq->h_curr（cgroup cpu.max 节流与带宽重分配路径），避免只带转换不带修复
- kind: testing
  description: 在 RT/DL 任务被 cpuset 绑核并配合中断隔离的机器上，验证 push 候选跳过 migrate-disabled 任务前后的行为差异与延迟毛刺
- kind: testing
  description: 为两处 CFS bandwidth 修复补一组 cpu.max 配额压测的前后可复现数据（上游线程里没有任何实测）
source_email_count: 1
related_articles:
- sched-20260906-004
- sched-20260901-002
- sched-20260902-011
tags:
- cfs
- rt
- deadline
- cgroup
- x86
title: '[GIT PULL] scheduler fixes'
layout: article
---

## TL;DR

本文为增量更新，完整背景与修复清单见 sched-20260906-004（Ingo 09-06 13:22:58 +0200 发出的 `tip/sched/urgent` 拉取，7 个修复、6 位提交者、`5 files changed, +64/-22`）。本日只有一条进展：pr-tracker-bot 于 09-07 02:11 回执，确认该 pull **已合入 `torvalds/linux.git`**，bot 给出的落地链接是 `88405f0ad1d5c680afe3ea0ce9345fa9e1deaac8`——从发出到进主线不到 7 小时（13:22:58 +0200 发出，合并回执为 02:11:34 +08:00，即 20:11 +0200）。前作里那句「进入主线的确切时点未获取到」现在可以收口了。本篇不再重复 7 条修复的罗列，只讲进主线之后对下游意味着什么、以及回合价值排序。

## 背景与问题

7 条修复各自的问题描述、作者与归属（fair 时间戳、CFS bandwidth 两处由 single-runqueue 转换引入的 `h_curr` 缺陷、RT/DL push 候选误选 migrate-disabled 任务、无效 `idle_stamp` 下的 `rq->avg_idle` 更新、hybrid cache-aware 平衡制造 misfit、x86 ITMT 对 debugfs 的依赖）见 [[sched-20260906-004]]。本日邮件本身没有新内容，它是合并回执，因此「背景」在这里应当换成：**这批修复此前只存在于 `tip/sched/urgent`，现在存在于 mainline 的祖先图里**，这个身份变化才是下游需要关心的事件。

关键差别有三点：一是 stable 流程的输入条件变了（进入 Linus 树后，带 `Fixes:` 的提交才会被 stable 维护者纳入回合候选）；二是任何以 mainline 为基准 rebase 的内部分支（OLK 这类）从下一个同步点开始会**自动带上这 7 条**，与手工回合的分支则会分叉出「别人已修我们没有」的差异；三是 `tip/sched/urgent` 被拉空后，sched 侧下一波变更（PREEMPT_DYNAMIC 简化、steal governor 排队、cache-aware 系列）的 rebase 基线会整体上移。

## 技术方案

无代码变化。本日邮件正文全文即 bot 的合并确认：

> The pull request you sent on Sun, 6 Sep 2026 13:22:58 +0200:
> has been merged into torvalds/linux.git:
> https://git.kernel.org/torvalds/c/88405f0ad1d5c680afe3ea0ce9345fa9e1deaac8

按 pr-tracker-bot 的惯例，该 sha 是这次 pull 在 `torvalds/linux.git` 里的落地点（bot 未在正文中区分它是合并提交还是分支顶端提交；前作记录的分支顶端是 `f0d243a96f2684ad771d678767d17972cf840bd7`）。落到哪个 `-rc` 本日邮件中未给出。

## 版本演进与当前进展

- 09-06 19:22:58（+08:00）/ 13:22:58（+0200）Ingo Molnar 发出 `[GIT PULL] scheduler fixes`（分支 `sched-urgent-2026-09-06`）。
- 09-07 02:11 pr-tracker-bot 确认已合入 `torvalds/linux.git`，链接 `88405f0ad1d5c680afe3ea0ce9345fa9e1deaac8`。**本轮 urgent 修复闭环完成。**
- 同日 06:40 Tejun Heo 另把一条 sched_ext 自测侧的 qmap 修复应用到 `sched_ext/for-7.3-fixes`（见 [[sched-20260907-010]]），那是与本次 pull 并行的另一条 fixes 流，不在此 pull 内。
- 本批 7 条各自的 stable 回合状态：未获取到（本日与 pull 正文都没有 `Cc: stable` 相关信息）。

## Maintainer 意见与讨论焦点

拉取与合并都无人回帖讨论，线程里只有 Ingo 的请求和 bot 的回执，这本身就是这类 urgent pull 的正常形态——Linus 侧不发表意见即合并。可以从中读到的两点信号：

- **响应速度**：不到 7 小时即被拉取，说明 Ingo 对这批内容的判断是「无需等待、直接进当前 -rc」，其中两条被 Ingo 亲自定性为 *caused by the recent single-runqueue conversion* 的回归（Wanwu Li 的 `throttle_cfs_rq()` / `distribute_cfs_runtime()`）显然是主要驱动因素——维护者承认该转换收尾不完整，而这条路径正是 `cgroup cpu.max` 的节流与带宽重分配。
- **`sched/urgent` 与 `sched_ext/for-7.3-fixes` 两条 fixes 流同日推进**，说明 7.3 后期的调度器修复是「核心路径走 Ingo、sched_ext 走 Tejun」的分流格局，下游要同时盯两个分支，只看 `tip/sched/urgent` 会漏掉 sched_ext 侧。

## 合入评估

`likelihood=merged`（已成事实）：`status=merged_tip`，落地 `torvalds/linux.git`，sha `88405f0ad1d5c680afe3ea0ce9345fa9e1deaac8`（取自本日 bot 正文）。

`severity=medium` 的判断依据不变（前作口径）：这批里没有 crash/hang 级别的单点，但 bandwidth 节流与 EEVDF 时间戳两处直接影响 cgroup CPU 配额的正确性，影响面是「静默的错误行为」而非「可观测的故障」，对生产环境的严重度不应按 low 处理。

对下游的实际含义（这才是本篇的重点判断）：
1. **不必再手工「等待」这批修复**——它们已在 mainline 祖先图里；内部分支若长期不同步 mainline，就要自己逐条确认是否已带。
2. **回合优先级重排**（按对本用户 cpuset/cgroup 方向的价值）：最高是 Wanwu Li 的两片 `h_curr`（只要分支带了 single-runqueue 转换而没带这两片，就会表现为偶发过度节流 / 带宽配额算错，且现象难以反向定位到根因）；其次是 Zhan Xusheng 的 `update_curr_eevdf()` 剩余 root `cfs_rq` 调用点（影响 EEVDF 时间戳一致性，与公平性/延迟抖动直接相关）；再次是 Seiji Nishikawa 的 RT/DL push 跳过 migrate-disabled（绑核 + 中断隔离机型的正确性）；`rq->avg_idle` 与 hybrid misfit 两条属于性能面，按需评估；x86 ITMT 一条只在带 intel 超线程 ITMT 的机型上相关，且我们若无 debugfs 依赖问题则优先级最低。
3. **rebase 冲突面**：`kernel/sched/fair.c` 一处就占了 60 行变更，凡是内部在 fair.c 上有大量补丁的分支，这批修复的回合都容易起冲突，建议按文件而不是按 commit 逐个核对。

## 效果评估

pull request 无 benchmark（前作同口径）。可量化的信息本日只增加了「合并事实 + 时延」两项：`+64/-22`、5 个文件、6 位提交者的内容在不到 7 小时内完成从 tip 到 mainline 的流转。收益仍是正确性一类：EEVDF 时间戳不再漏更新、`cpu.max` 节流与带宽重分配不再走错 `cfs_rq`、migrate-disabled 任务不再被 RT/DL push、空闲统计不再被无效 `idle_stamp` 污染、cache-aware 平衡不再制造 misfit、ITMT 不再依赖 debugfs。

## 我可以参与的点

- **回合自查（最直接）**：把这次 pull 的 7 条与自己分支做一次逐条 diff。做法上建议直接用 `git log --oneline <自家基线>..88405f0ad1d5 -- kernel/sched/fair.c` 这类范围比对找同名 commit，而不是靠 cherry-pick 撞冲突。若分支已带 single-runqueue/`h_curr` 转换，优先确认 `throttle_cfs_rq()` 与 `distribute_cfs_runtime()` 两处是否也已改用 `cfs_rq->h_curr`。
- **cpuset/绑核场景的验证**：`sched/rt,dl: Skip migrate-disabled tasks when picking a push candidate` 值得在「RT/DL 任务被 cpuset 绑核 + 中断隔离」的机器上做一次前后行为对比（关注 push IPI 是否还会挑中不可迁移任务、以及由此带来的延迟毛刺）。这类验证上游一般拿不到——绑定在真实隔离拓扑上的数据是我们的增量。
- **给 cpu.max 场景补一组端到端数据**：两处 bandwidth 修复是这次 pull 里与我们最相关的部分，但线程里没有任何人在真实配额压测下给出前后对比。若在自家环境能给出「修复前偶发过度节流的可复现窗口」，无论对上游论证还是内部立项都更有说服力。
- **顺带确认 stable 队列**：本批是否已进入 stable 回合本日邮件中无迹象；如果需要给自己的长期分支做映射，值得逐个 commit 去 `Fixes:` 标签与 stable 队列里核对，这属于上游不会替我们做、但内部回合必须回答的事。

## 参考链接

- 相关文章/系列：
  - [[sched-20260906-004]] 前作：7 条修复的逐条内容与归属、diffstat、`sched-urgent-2026-09-06` 顶端 sha。
  - [[sched-20260901-002]] 其中一条修复（`h_curr` bandwidth 路径）的补丁级分析。
  - [[sched-20260902-011]] 其中一条修复（无效 `idle_stamp` 下跳过 `rq->avg_idle` 更新）的补丁级分析。
- pull request（09-06，Ingo Molnar）: https://lore.kernel.org/all/ap1NEllrD8nMsFiB@gmail.com/
- 本日 pr-tracker-bot 合并回执: https://lore.kernel.org/all/178871829440.1639575.4127304395444817583.pr-tracker-bot@kernel.org/
- mainline 落地: https://git.kernel.org/torvalds/c/88405f0ad1d5c680afe3ea0ce9345fa9e1deaac8
- stable backport: 未获取到
