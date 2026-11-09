---
id: sched-20261109-001
date: '2026-11-09'
subject: 'sched/deadline: bandwidth accounting fixes and selftests'
subsystem: sched
type: fix
status: under_review
severity: high
thread_root_msgid: <20261108185406.1549770-1-mathieu.desnoyers@efficios.com>
lore_url: https://lore.kernel.org/all/20261108185406.1549770-1-mathieu.desnoyers@efficios.com/
authors:
- Mathieu Desnoyers
maintainers_involved:
- Juri Lelli
- Ingo Molnar
current_version: v5
patch_series:
- version: v5
  msgid: <20261108185406.1549770-1-mathieu.desnoyers@efficios.com>
  date: '2026-11-09'
  summary: 29 补丁（25 修复 + sched_debug + 3 自测），stable 可截取 1-25；吸收 Juri 被 Ingo 丢弃的 4
    个修复
  review_outcome: Juri 对 03/04/06 给 Reviewed-by，对 05 提出 Fixes 归属疑问，对 06 给 cosmetic
    意见
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues:
  - patch 05 除零 active CPU 的 Fixes 归属与是否拆分待定
  next_action: 作者按 Juri 意见出 v6，回应 patch 05 拆分与 patch 06 注释问题
contribution_opportunities:
- kind: review
  description: 核对 patch 05 的 Fixes 归属与是否拆成两个 fix（Juri 提出的开放问题）
- kind: testing
  description: 在 isolcpus=domain + CPU hotplug 场景回归 v5 的 25 修复与 3 自测
generated_at: '2026-11-10T09:00:00+08:00'
source_email_count: 20
related_articles:
- sched-20261105-001
- sched-20261106-001
- sched-20261107-002
- sched-20261108-003
tags:
- deadline
- cgroup
- rt_bandwidth
title: 'sched/deadline: bandwidth accounting fixes and selftests'
layout: article
---

## TL;DR

本文为增量更新，完整脉络见下。

- <a class="article-ref" href="/lkm/2026/11/05/sched-20261105-001-sched-deadline-bandwidth-accounting-fixes-and-selftests.html">sched-20261105-001</a>：Mathieu Desnoyers 的 v2 系列（21 补丁）在 Juri Lelli 此前 4 个 sched/urgent 修复之上再修 17 个 SCHED_DEADLINE 带宽记账 bug（其中 3 个可直接打死内核），带自测与 sched_debug。Juri 已对多数补丁给 Reviewed-by/Acked-by，Marek Szyprowski 实测修复了 CPU hotplug 崩溃并给 Tested-by；Ingo 要求「严格只含 -stable 可回退修复的子集」。
- <a class="article-ref" href="/lkm/2026/11/06/sched-20261106-001-sched-deadline-bandwidth-accounting-fixes-and-selftests.html">sched-20261106-001</a>：v3 发出，扩到 24 补丁，把 Juri 被 Ingo 丢弃的 4 个 sched/urgent 修复全部吸收，新增 patch 5/7/13/16 四个新修复。
- <a class="article-ref" href="/lkm/2026/11/07/sched-20261107-002-sched-deadline-bandwidth-accounting-fixes-and-selftests.html">sched-20261107-002</a>：v4 发出，扩到 26 补丁（22 修复 + sched_debug + 3 自测），新增 replenishment timer 跨 class 往返残留与 boosted 任务设 SCHED_DEADLINE 缺账两个修复。
- <a class="article-ref" href="/lkm/2026/11/08/sched-20261108-003-sched-deadline-bandwidth-accounting-fixes-and-selftests.html">sched-20261108-003</a>：作者逐条回应 sashiko-bot 对 9 个补丁的评审，并密集披露 v5 计划。
- <a class="article-ref" href="/lkm/2026/11/09/sched-20261109-001-sched-deadline-bandwidth-accounting-fixes-and-selftests.html">sched-20261109-001</a>（今天）：**v5 发出，扩到 29 补丁（25 个修复 + sched_debug + 3 自测）**，按 Ingo「修复在前」要求 stable 可直接截取 1-25。Juri Lelli 当天评审 patch 03/04/06 并给 Reviewed-by（另对 06 有 cosmetic 意见、对 05 质疑一处 Fixes 归属），Mathieu 承诺下一版采纳并补 `unlikely()`。

## 背景与问题

（承接 <a class="article-ref" href="/lkm/2026/11/05/sched-20261105-001-sched-deadline-bandwidth-accounting-fixes-and-selftests.html">sched-20261105-001</a> / 20261106-001 / 20261107-002 / 20261108-003）Juri Lelli 前一轮 4 个 SCHED_DEADLINE 带宽记账修复被 Ingo 从 tip/sched/urgent 移除——首个补丁在 Marek Szyprowski 的 CPU hotplug 测试上崩溃。Mathieu Desnoyers 系统梳理 dl_bw/total_bw/this_bw 记账边界缺陷，按 Ingo「修复在前、stable 可截取」一路推进到 v4（26 补丁）。

v5 的 cover 明确交代规模与后果分布：**25 个 bug**，其中 3 个可直接打死内核（patch 5/8/22）、2 个让 cpuset_mutex 不可用（patch 1/6）、其余多数让 root domain 的 total_bw 或 runqueue 的 this_bw 与真实任务不符——root domain 要么超额准入 deadline 任务、要么一个都不准入。系列基于 "locking/rtmutex: priority inheritance fixes and tests" 的 v2（patch 8 依赖其 patch 3）。patch 1 是 Andrea Parri 的，已获 Waiman、Kayra、Juri 评审，作者因 patch 6/15 建立其上而携带。Juri 被 Ingo 丢弃的 4 个修复去向：1/4→patch 16、2/4→patch 11（去二次释放、暂不带 Signed-off-by）、3/4→patch 2、4/4→patch 12（扩展）。Marek 确认 v2 已修复其崩溃的板子。

## 技术方案

（承接 v2/v3/v4 的「可追溯、可幂等」记账思路）v5 无新机制性手段，主要是把此前披露的 v5 计划落地并重新编号。25 个修复按 cover 顺序：

- 除零 active CPU（现 patch 5）、cpuset_mutex 二次解锁（patch 1，Andrea Parri）、sysrq-n 持锁（patch 6）。
- `SCHED_FLAG_KEEP_PARAMS` 准入时序（patch 2/3）、boosted 任务改 policy（patch 4）、deadline boost 来源与参数复位（patch 8/9）、deboost 处重置 donor runtime（patch 10）。
- root domain 记账的「记录」改造：离开类睡眠任务释放带宽（patch 11）、拒绝 exited 任务设 SCHED_DEADLINE（patch 12）、rebuild 穿越 attach（patch 19）、记录记账所在 root domain 的 CPU（patch 16）、重建记账时取记录中的 CPU（patch 22）、带宽只在腾挪有空间时搬运（patch 18）等。
- patch 26 sched_debug 展示每 runqueue 的 deadline bandwidth；patch 27-29 三个自测（含 SCHED_DEADLINE 带宽记账、root domain rebuild 穿越、policy round trip）。

今日实质进展在评审而非新方案：Juri 对 patch 05（除零 active CPU）提出**Fix 归属疑问**——它并非「修复」 `4043f5498416`（那是一个正确但不完整的 fix，对象是 `d741f297bcea`），第二个 hunk 才是补全；Juri 问是否需要两个 fix 并存、或把该改动拆成两个（第二部分对无 dl-server 的旧内核不适用）。对 patch 06 仅 cosmetic（更描述性的注释 + `unlikely()`）。

## 版本演进与当前进展

*current_version: v5（2026-11-09，`<20261108185406.1549770-1-mathieu.desnoyers@efficios.com>`）*。v5 共 29 补丁（25 修复 + 1 sched_debug + 3 自测）。今日 Juri Lelli 评审：patch 03（`Do not admit bandwidth for parameters that are kept`）与 patch 04（`Let a task boosted by a deadline waiter change its policy`）给 Reviewed-by；patch 06（`Take cpuset_mutex for a deadline policy change only with pi`）给 Reviewed-by + 两条 cosmetic 意见；patch 05（除零 active CPU）提出 Fixes 归属与是否拆分的问题。Mathieu 回复：将照 Juri 原文采纳两条注释意见并给第二处补 `unlikely()`。

## Maintainer 意见与讨论焦点

- **Juri Lelli（sched/deadline 维护者）**：对 patch 03/04/06 给 Reviewed-by，方向明确认可。两个未解决点：① patch 05 的 `Fixes:` 标签是否该指向 `4043f5498416`（Juri 认为它只是不完整 fix），以及第二个 hunk（补全 `d741f297bcea` 的 fix）是否应拆成独立补丁以适配无 dl-server 的旧内核；② patch 06 的注释可读性与 `unlikely()`。无 NAK，无阻塞性分歧。
- **Ingo Molnar（sched maintainer）**：此前已确立「修复在前、stable 可截取」的框架，v5 已遵守（patch 1-25 为修复）。
- 争议点集中在 patch 05 的 Fixes 归属，属收尾级，不构成合入障碍。

## 合入评估

*likelihood=high*。Juri 对多数补丁已给 Reviewed-by，Marek 实测 Tested-by，Ingo 的「修复在前」要求已满足；剩余工作为 patch 05 的 Fixes/拆分确认与 patch 06 的 cosmetic 修订。*blocking_issues*：① patch 05 是否拆分为两补丁待 Juri/Ingo 定夺；② 仍有部分 patch（如 07-29 的多数）未获人类维护者逐条 Reviewed-by。*next_action*：作者按 Juri 意见出 v6（采纳注释 + `unlikely()`，回应 patch 05 拆分问题）。

## 效果评估

Marek Szyprowski 在先前版本实测确认修复了其在 -next 上复现的 CPU hotplug 崩溃并给 Tested-by（今日无新增性能数据）。3 个内核崩溃级 bug（除零 active CPU、boosted owner 无限循环、rebuild 撞隔离 CPU 的 BUG()）与 2 个 cpuset_mutex 不可用 bug 的修复价值来自正确性而非性能，cover 未给 benchmark。

## 我可以参与的点

- **review**：核对 patch 05（除零 active CPU）的 Fixes 归属与「是否拆成两个 fix」——这是 Juri 明确提出的开放问题，可给出自己的判断回帖。
- **testing**：在 `isolcpus=domain` 与 CPU hotplug 场景复跑 v5 的 25 个修复 + 3 个自测（尤其 patch 5/8/22 三个内核崩溃 bug 的回归），回帖报告结果。
- **review**：审查尚未被人类维护者逐条评审的 patch（07-29），尤其 root domain 记账重建路径的竞态。

## 参考链接

- lore thread: https://lore.kernel.org/all/20261108185406.1549770-1-mathieu.desnoyers@efficios.com/
- Juri 对 patch 05 的 Fixes 疑问: https://lore.kernel.org/all/avHY7oNeuvjsLT4I@jlelli-thinkpadt14gen4.remote.csb/
