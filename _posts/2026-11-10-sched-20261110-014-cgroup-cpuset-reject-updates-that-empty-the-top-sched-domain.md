---
id: sched-20261110-014
date: '2026-11-10'
subject: 'cgroup/cpuset: Reject updates that empty the top sched domain'
subsystem: sched
type: fix
status: under_review
severity: high
thread_root_msgid: <20261110050324.173461-2-guopeng.zhang@linux.dev>
lore_url: https://lore.kernel.org/all/20261110050324.173461-2-guopeng.zhang@linux.dev/
authors:
- Guopeng Zhang
- Ridong Chen
maintainers_involved:
- Waiman Long
current_version: v3
patch_series:
- version: v3
  msgid: <20261110050324.173461-1-guopeng.zhang@linux.dev>
  date: '2026-11-10'
  summary: 要求分区创建/更新与 hotplug 路径保留 active boot domain housekeeping CPU
  review_outcome: Ridong 建议统一 tasks_nocpu_error helper（附伪代码）
upstream_commit: null
fixes_commit: 9b496a8bbed9
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues:
  - v3 patch 3/3 是否按 Ridong 建议重构 helper
  - Waiman 对 v3 的确认
  next_action: 作者回应 Ridong 的 helper 建议，等 Waiman 确认 v3
contribution_opportunities:
- kind: review
  description: 评估 Ridong 的 tasks_nocpu_error(xcpus, del_cpus) 统一方案与现有 mask 语义是否等价
- kind: testing
  description: 在 32 核 isolcpus=domain 复现 v3 的 Oops 触发序列并验证修复
generated_at: '2026-11-11T09:00:00+08:00'
source_email_count: 3
related_articles:
- sched-20261105-012
- sched-20261107-012
- sched-20261109-005
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
- <a class="article-ref" href="/lkm/2026/11/07/sched-20261107-012-cgroup-cpuset-keep-the-top-sched-domain-non-empty-on-cpu-hot.html">sched-20261107-012</a>：Waiman Long（cpuset/cgroup 维护者）评审 patch 1/3——认可代码改动，对自测脚本给四点意见。
- <a class="article-ref" href="/lkm/2026/11/09/sched-20261109-005-cgroup-cpuset-reject-updates-that-empty-the-top-sched-doma.html">sched-20261109-005</a>：Guopeng 逐条回应 Waiman 的 v2 意见，Waiman 撤回一条 misread 的评论。
- <a class="article-ref" href="/lkm/2026/11/10/sched-20261110-014-cgroup-cpuset-reject-updates-that-empty-the-top-sched-domain.html">sched-20261110-014</a>（今天）：**v3 发出**（Guopeng + Ridong Chen 共同署名），并获 Ridong Chen 实质评审——建议把多处「同一检查、不同 mask」的统一成一个 helper（`tasks_nocpu_error()` 显式接收要归还的 CPU 参数）。

## 背景与问题

（承接 <a class="article-ref" href="/lkm/2026/11/05/sched-20261105-012-cgroup-cpuset-keep-the-top-sched-domain-non-empty-on-cpu-hot.html">sched-20261105-012</a> / 20261107-012 / 20261109-005）boot-isolated CPU 仍留在 `top_cpuset.effective_cpus`、却被排除在调度域之外；只按 `effective_cpus` 分配 CPU 可能拿走顶层 cpuset 的全部 boot domain housekeeping CPU，得到空顶层调度域，进而 `build_sched_domains()` 告警 + `build_perf_domains()` 越界访问（GPF）。v3 补丁在 32 核 `isolcpus=domain,10-31` 上给出确定性触发：`echo 0-9 > A/cpuset.cpus` 后 `echo root > A/cpuset.cpus.partition` 即 Oops。

## 技术方案

v3 的 patch 1/3 `Reject updates that empty the top sched domain`：要求本地与远程分区的创建与 CPU mask 更新都保留一个 active boot domain housekeeping CPU，并计入同一次更新归还的 CPU；自测脚本新增用例验证每次分区更新后顶层 cpuset 仍留有一个 active boot domain housekeeping CPU。`Fixes: 9b496a8bbed9`，Ridong Chen 共同署名。Ridong 对 patch 3/3 的评审提出重构建议——`tasks_nocpu_error()` 与 hotplug 路径多处「同一检查用不同 mask」，建议让它像 `top_cpuset_sd_nocpu()` 一样显式接收「要归还的 CPU」参数并对所有 parent 统一复用（附未测试的伪代码）。

## 版本演进与当前进展

*current_version: v3（2026-11-10 发出，`<20261110050324.173461-1-guopeng.zhang@linux.dev>`）*。v3 落地了 v2 评审的收尾（`==` 修正、条件/位置调整），并吸收 Ridong Chen 为共同作者。今日 Ridong 继续对 patch 3/3 提出 helper 统一的实质性重构意见。

## Maintainer 意见与讨论焦点

- **Ridong Chen（共同作者 / 审阅者）**：对 patch 3/3 建议把 `tasks_nocpu_error()` 改成显式接收归还 CPU 的辅助函数、统一多处重复检查（附伪代码）；另就署名邮箱建议用 `chenridong@xiaomi.com`。
- **Waiman Long（cpuset/cgroup 维护者）**：v2 已认可 patch 1/3 代码改动，v3 尚未见其对最新版表态。
- 无 NAK、无方向性异议；分歧仅在代码组织（统一 helper）。

## 合入评估

*likelihood=high*。代码改动已获 Waiman 认可、且该系列是 cpuset panic 那条 bug（<a class="article-ref" href="/lkm/2026/11/09/sched-20261109-003-bug-cpuset-empty-sched-domain-with-isolcpus-domain-panic-at.html">sched-20261109-003</a>）的修复归属；v3 已发出，剩余是 Ridong 的 helper 统一建议是否被接受。*blocking_issues*：① v3 的 patch 3/3 是否按 Ridong 建议重构 helper；② Waiman 对 v3 的确认。*next_action*：作者回应 Ridong 的 helper 建议（采纳或说明理由），等 Waiman 对 v3 确认。

## 效果评估

今日无新增性能/复现数据。修复价值为正确性（消除空顶层调度域导致的告警与 GPF/panic），v3 补丁给出了 32 核 `isolcpus=domain` 的确定性 Oops 复现。

## 我可以参与的点

- **review**：评估 Ridong 的 `tasks_nocpu_error(xcpus, del_cpus)` 统一方案与现有 mask 语义是否等价（作者尚未回应，属开放问题）。
- **testing**：在 32 核 `isolcpus=domain,10-31` 复现 v3 的 Oops 触发序列，验证打补丁后不再 panic 且分区更新后顶层 cpuset 仍保留 housekeeping CPU。

## 参考链接

- v3 patch 1/3: https://lore.kernel.org/all/20261110050324.173461-2-guopeng.zhang@linux.dev/
- Ridong 对 patch 3/3 的评审: https://lore.kernel.org/all/19708635-67de-45ab-9539-8d686caa7132@linux.dev/
