---
id: sched-20261109-005
date: '2026-11-09'
subject: 'cgroup/cpuset: Reject updates that empty the top sched domain'
subsystem: sched
type: fix
status: under_review
severity: high
thread_root_msgid: <0ae6fffe-d492-4e85-b464-fafdc4c2b064@linux.dev>
lore_url: https://lore.kernel.org/all/0ae6fffe-d492-4e85-b464-fafdc4c2b064@linux.dev/
authors:
- Guopeng Zhang
maintainers_involved:
- Waiman Long
current_version: v2
patch_series:
- version: v2
  msgid: <20261105130344.664336-1-guopeng.zhang@linux.dev>
  date: '2026-11-05'
  summary: 3 补丁：分区创建/更新与 hotplug 路径保留一个 active boot domain housekeeping CPU
  review_outcome: Waiman 认可代码改动，对自测脚本给四点意见；Guopeng 逐条回应并推进 v3
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues:
  - v3 尚未发出；test matrix 归组疑问待澄清
  next_action: 作者出 v3（含 == 修正与条件/位置调整）并双场景验证
contribution_opportunities:
- kind: review
  description: 就新 test matrix 是否合并进现有 matrix 给出建议
- kind: testing
  description: 在 32 核 isolcpus=domain 及 nohz_full 场景验证 v3 后无 GPF
generated_at: '2026-11-10T09:00:00+08:00'
source_email_count: 2
related_articles:
- sched-20261105-012
- sched-20261107-012
tags:
- cgroup
- topology
- affinity
title: 'cgroup/cpuset: Reject updates that empty the top sched domain'
layout: article
---

## TL;DR

本文为增量更新，完整脉络见下。

- <a class="article-ref" href="/lkm/2026/11/05/sched-20261105-012-cgroup-cpuset-keep-the-top-sched-domain-non-empty-on-cpu-hot.html">sched-20261105-012</a>：Guopeng Zhang 的 v2 三补丁系列修复 cpuset 分区操作与 CPU hotplug 把顶层调度域清空、进而触发 `build_sched_domains()` 告警与 `build_perf_domains()` 越界访问（GPF）的问题。刚发出，暂无维护者回复。
- <a class="article-ref" href="/lkm/2026/11/07/sched-20261107-012-cgroup-cpuset-keep-the-top-sched-domain-non-empty-on-cpu-hot.html">sched-20261107-012</a>：Waiman Long（cpuset/cgroup 维护者）评审 patch 1/3（Reject updates that empty the top sched domain）——认可代码改动，对自测脚本给四点意见（`==` 误写、nohz_full 断言理由、测试代码位置、test matrix 归组）。
- <a class="article-ref" href="/lkm/2026/11/09/sched-20261109-005-cgroup-cpuset-reject-updates-that-empty-the-top-sched-doma.html">sched-20261109-005</a>（今天）：**Guopeng 逐条回应 Waiman 的 v2 意见**（`==` 改用、调整条件并补 domain isolation + nohz_full 双测、测试选择代码挪到 ISOLCPUS 段复用 BOOT_ISOLCPUS）；Waiman 撤回其中一条评论（自承「misread the context of the hunk」）。

## 背景与问题

（承接 <a class="article-ref" href="/lkm/2026/11/05/sched-20261105-012-cgroup-cpuset-keep-the-top-sched-domain-non-empty-on-cpu-hot.html">sched-20261105-012</a> / 20261107-012）boot-isolated CPU 仍留在 `top_cpuset.effective_cpus` 却被排除在调度域之外；若只按 `effective_cpus` 给分区分配 CPU，就可能把顶层 cpuset 的所有 boot domain housekeeping CPU 拿走，得到空顶层调度域，进而 `build_sched_domains()` 告警 + `build_perf_domains()` 越界访问（GPF）。本系列通过要求分区创建/更新与 hotplug 路径都保留一个 active boot domain housekeeping CPU 来修复。这也是 20261109-003（cpuset panic）那条 [BUG] 线的修复归属系列。

## 技术方案

今日无新代码，为 v2 评审的收尾：Guopeng 确认 v3 将——① 自测脚本里 `=` 改为 `==`（Waiman 指出的笔误）；② 调整条件并同时验证 domain isolation 与 nohz_full 两种使能；③ 把测试选择代码移到 ISOLCPUS 段之后、复用 `BOOT_ISOLCPUS` 变量。对于 Waiman 关于 test matrix 位置的疑问，Guopeng 表示不清楚「是挪定义位置还是合并进现有 matrix」，仍在澄清中。Waiman 当日撤回一条对某个 hunk 的评论，自承看错了上下文。

## 版本演进与当前进展

*current_version: v2（2026-11-05 发出，3 补丁）*。今日：Guopeng 逐条回应 Waiman 的 v2 评审（`==`、条件、测试位置），并推进 v3 计划；Waiman 撤回一条评论。无新版本补丁发出。

## Maintainer 意见与讨论焦点

- **Waiman Long（cpuset/cgroup 维护者）**：v2 已认可 patch 1/3 代码改动（「The code change above looks good to me」）；今日撤回一条 misread 的评论。剩余意见集中在自测脚本收尾（`==` 笔误、断言理由、代码位置、matrix 归组），无方向性异议。
- **Guopeng Zhang（作者）**：逐条响应，对 matrix 归组问题尚在澄清。

## 合入评估

*likelihood=high*。代码改动已获维护者认可，剩余为自测脚本收尾；且该系列是 20261109-003（cpuset panic）那条 bug 的修复归属，Waiman/Mathieu 都已背书。*blocking_issues*：① v3 尚未发出；② test matrix 归组疑问待澄清。*next_action*：作者出 v3（含 `==` 修正与条件/位置调整），并在 domain isolation + nohz_full 双场景验证。

## 效果评估

今日无新增性能/复现数据。修复价值为正确性（消除空顶层调度域导致的告警与 GPF/panic），相关 panic 场景由 Mathieu 在 20261109-003 线程确认。

## 我可以参与的点

- **review**：就「新 test matrix 是否合并进现有 ISOLCPUS/NOHZ_FULL matrix」给出建议（Guopeng 正在澄清、未定）。
- **testing**：在 32 核 `isolcpus=domain` 及 nohz_full 场景验证 v3 后空顶层调度域不再出现、无 GPF。

## 参考链接

- Guopeng 的回应: https://lore.kernel.org/all/0ae6fffe-d492-4e85-b464-fafdc4c2b064@linux.dev/
- Waiman 撤回评论: https://lore.kernel.org/all/e575df2d-71dd-4844-83b7-d29bed349992@redhat.com/
