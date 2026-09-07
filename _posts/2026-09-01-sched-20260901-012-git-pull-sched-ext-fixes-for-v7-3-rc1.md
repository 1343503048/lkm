---
id: sched-20260901-012
subject: '[GIT PULL] sched_ext: Fixes for v7.3-rc1'
date: '2026-09-01'
subsystem: sched
type: fix
status: merged_tip
severity: high
thread_root_msgid: <0f59915200a4239f27a624250c58dd6c@kernel.org>
lore_url: https://lore.kernel.org/all/0f59915200a4239f27a624250c58dd6c@kernel.org/
authors:
- Tejun Heo
maintainers_involved:
- Tejun Heo
- Linus Torvalds
current_version: v1
patch_series:
- version: v1
  msgid: <0f59915200a4239f27a624250c58dd6c@kernel.org>
  date: '2026-09-01'
  summary: sched_ext for v7.3-rc1 GIT PULL：dsq_move 所有权竞态导致的假性 abort、sleepable ops.cgroup_set_bandwidth()、示例调度器
    timer/vtime 修复、cgroup CPU 旋钮文档化、tools 头同步（12 commits）
  review_outcome: pull 线程内无 review；09-01 05:05 pr-tracker-bot 确认已合入 torvalds/linux.git
upstream_commit: bf1079577a116f0685e7025b9ee2547345ee1c63
fixes_commit: null
merged_branch: torvalds/linux.git (tag sched_ext-for-7.3-rc1-fixes)
merge_assessment:
  likelihood: merged
  blocking_issues: []
  next_action: 下游按 12 个 commit 逐片核对 stable/Cc 标签再决定回合范围
contribution_opportunities:
- kind: testing
  description: 在自家带 sched_ext 的分支上复现 scx_bpf_dsq_move() 所有权竞态导致的 spurious abort，确认是否需要提前收这个修复
- kind: discussion
  description: cpu.max/cpu.idle 语义已明确为 scheduler-dependent，补充混部场景（CFS 与 BPF 调度器并存）下的行为差异文档与验证
- kind: extend
  description: sleepable cgroup_set_bandwidth() 的 capability marker 在 scx 工具侧尚无使用示例，可在
    scx repo 补用例
source_email_count: 2
related_articles:
- sched-20260901-008
- sched-20260901-009
- sched-20260901-017
- sched-20260818-003
tags:
- sched_ext
- cgroup
generated_at: '2026-09-07'
title: '[GIT PULL] sched_ext: Fixes for v7.3-rc1'
layout: article
---

## TL;DR

Tejun Heo 08-31 发出的 sched_ext v7.3-rc1 修复 pull request，在 09-01 05:05 被 Linus 收下（合入 `torvalds/linux.git`，merge commit `bf1079577a116f0685e7025b9ee2547345ee1c63`）。12 个 commit、12 个文件 +597/-58，核心是 `scx_bpf_dsq_move()` 的所有权检查竞态（会导致 BPF 调度器被假性 abort）、`ops.cgroup_set_bandwidth()` 允许 sleepable，以及 cgroup CPU 旋钮（`cpu.max`/`cpu.idle`）的 BPF 回调语义文档化。这是 sched_ext 进 7.3 后的第一批稳定集，任何带 sched_ext 的分支都应对照收。

## 背景与问题

7.3 的 sched_ext 引入了大量新面（层级子调度、DSQ move 迭代器、cgroup 旋钮回调），rc1 阶段集中暴露三类问题：

- **正确性**：`scx_bpf_dsq_move()` 里判断任务归属的检查跑在队列锁之外，与任务退出或迁往另一个 sub-scheduler 并发， spuriously 触发 scheduler abort——对生产上跑 BPF 调度器的人来说是最刺眼的一类。
- **能力缺口**：cgroup 带宽变更回调本应允许睡眠（要拿 `cgroup_threadgroup_rwsem` 一类可睡眠资源），但 load 时会被判定非法而拒绝加载，作者无法写出正确的 `ops.cgroup_set_bandwidth()` 实现。
- **示例调度器与记账**：`scx_central` 忽略 timer 重挂失败、`scx_flatcg` 在 cgroup 迁移时丢失 vtime credit、`scx_qmap` 不检查 `bpf_timer_start()` 返回值。
- **文档/工具头**：`tools/sched_ext` 的 `common.bpf.h`/`compat.bpf.h` 与 scx repo 漂移，cgroup-v2 与 sched-ext 文档缺 BPF 回调侧说明。

## 技术方案

Tejun 在 pull 正文里给的就是这几条取舍：

> The task ownership check in the dispatch queue move operation raced against the task exiting or moving to a different sub-scheduler, spuriously triggering scheduler aborts. Fix by moving the check under the queue lock.

即把归属检查移进 DSQ 队列锁内，用锁的既有边界而不是新加一层引用计数来消除竞态。带宽回调一侧是允许 sleepable 实现 + **新增一个 capability marker** 让 userspace 能探测调度器是否支持（老调度器不至于因为不支持 sleepable 回调而加载失败）。文档一侧值得单独看：`Documentation/admin-guide/cgroup-v2.rst` 补了 `cpu.max`/`cpu.idle` 对应的 BPF 回调，Tao Cui 的 `docs/sched_ext: document that cgroup CPU knobs are scheduler-dependent` 明确了「同一个 cgroup 旋钮在不同 BPF 调度器下语义可以不同」——这条对容器侧行为预期有实际影响。

改动面：`kernel/sched/ext/ext.c` (+47/-…)、`kernel/sched/ext/internal.h`、`tools/sched_ext/include/scx/*`（新增 `enums_abi.autogen.h` 223 行）、三个示例调度器与两份文档。

## 版本演进与当前进展

- 基线：`fab183d632628381b466a41479489541ac0e29a0`（`sched_ext: Merge branch 'for-7.3-arena-args' into for-7.3`，08-17）。
- 顶端：`068e5a0bc57e57d24cbf38def29cc5fb4db9a0df`（`sched_ext: Fix missing @slice and @vtime descriptions in finish_dispatch() kernel-doc`，08-31 07:28）。
- tag：`sched_ext-for-7.3-rc1-fixes`，仓库 `git.kernel.org/pub/scm/linux/kernel/git/tj/sched_ext.git`。
- 08-31 10:03 (-1000) 发出 → 09-01 04:03 出现在列表 → **09-01 05:05 pr-tracker-bot 确认已进 `torvalds/linux.git`**。

commit 构成：Wanwu Li 4（示例调度器 timer/vtime/注释）、Tejun Heo 3（2 次工具头同步 + dsq_move 竞态修复）、Liang Luo 3（文档 + kernel-doc）、Changwoo Min 1（sleepable `cgroup_set_bandwidth()`）、Tao Cui 1（文档）。

## Maintainer 意见与讨论焦点

pull 线程本身当日只有 Tejun 的发起与 pr-tracker 的机械回执，**没有任何 review 意见**——这是 pull request 的正常形态，讨论都发生在被收进来的各补丁自己的线程里。当日可见的相关维护者动作是 Tejun 对其中若干补丁的直接表态（同一批邮件里能看到）：

- `sched_ext: Fix several comment issues`／`Fix timer pinning and return value in scx_central`／`Fix missing @slice and @vtime descriptions...`：Tejun 09-01 凌晨逐条回帖 "Applied to sched_ext/for-7.3-fixes"，并说明把 `scx_central` 描述里的 `-EINVAL` 归因从 `central_init()` 改到 `start_central_timer()`（自 `d6edb15ad92c` 起它就在后者），以及把首个注释块重新折行到 80 列。
- `sched_ext: don't deliver duplicate ops.cgroup_set_idle() for same value`（本日另文，见 sched-20260901-008）与 vtime 排序系列（sched-20260901-009）仍在迭代，**没有**进入本 pull。
- 未解决项：Tejun 明确「以后走 sched_ext 的 pull」的内容仍有排在 7.4 的（例如把初始 `cpu.idle` 传入 `scx_cgroup_init_args` 的清理片，见 sched-20260901-017），rc1 只收 fixes。

## 合入评估

`likelihood = merged`。已经落进 mainline（v7.3-rc1 窗口），无阻塞项。对下游只有两条判断：一是这批是 rc1 级修复，任何带 7.3 sched_ext 的分支都应无条件跟随；二是 `Cc: stable` 属性不在本 pull 正文里体现，需要逐片看各自的标签再决定是否往 6.x 回合。

## 效果评估

pull 正文与 diffstat 之外**无任何性能数据**，这也不需要一个——修复目标是消除假性 abort 与回调能力缺口。可量化信息只有构成：12 commits / 12 files / +597 / -58，其中约 470 行是 `tools/sched_ext` 头文件同步与文档，内核侧实际逻辑改动集中在 `ext.c` 与 `internal.h`（合计约 +72/-…）。

## 我可以参与的点

- **当作回合清单**：把这 12 个 commit 作为自家 7.3 基线的必收集合，尤其 `scx_bpf_dsq_move()` 竞态修复——若自家 BPF 调度器有跨 DSQ 移动任务 + 任务可被 cpuset 迁移/退出并发的场景，这个假性 abort 是能用现有代码复现的，值得在自家分支上验一次再决定是否提前回合。
- **cgroup 语义对齐**：`cpu.max`/`cpu.idle` 现在是「scheduler-dependent」的，若内部同时跑 CFS 与 BPF 调度器，容器 CPU 限额的行为差异需要写进自家使用文档并在混部场景里验证。
- **留意漏网项**：sleepable `cgroup_set_bandwidth()` 只是「允许」，配套的用户态探测 marker 怎么在 scx 工具里用起来仍是开放面，可以在 scx repo 侧补用例。

## 参考链接

- lore thread（pull request）: https://lore.kernel.org/all/0f59915200a4239f27a624250c58dd6c@kernel.org/
- pr-tracker 合入回执: https://lore.kernel.org/all/178821033071.773084.18341134789285724214.pr-tracker-bot@kernel.org/
- mainline merge commit: https://git.kernel.org/torvalds/c/bf1079577a116f0685e7025b9ee2547345ee1c63
- 仓库与 tag: https://git.kernel.org/pub/scm/linux/kernel/git/tj/sched_ext.git (tags/sched_ext-for-7.3-rc1-fixes)
- tip-bot commit: 不适用（走 sched_ext tree，非 tip）
- stable backport: 未获取到（本 pull 未体现 stable 标签信息）
