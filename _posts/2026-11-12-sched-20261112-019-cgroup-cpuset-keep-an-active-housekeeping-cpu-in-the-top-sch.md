---
id: sched-20261112-019
date: '2026-11-12'
subject: 'cgroup/cpuset: Keep an active housekeeping CPU in the top sched domain'
subsystem: sched
type: fix
status: under_review
severity: high
thread_root_msgid: <20261111134250.16852-1-guopeng.zhang@linux.dev>
lore_url: https://lore.kernel.org/all/20261111134250.16852-1-guopeng.zhang@linux.dev/
authors:
- Guopeng Zhang
- Ridong Chen
maintainers_involved: []
current_version: v4
patch_series:
- version: v4
  msgid: <20261111134250.16852-1-guopeng.zhang@linux.dev>
  date: '2026-11-11'
  summary: 统一 CPU 可用性检查、归还 CPU 限定在 parent exclusive grant、hotplug 守卫
  review_outcome: Ridong 认可能接受边角守卫；待 Waiman 评审
upstream_commit: null
fixes_commit: 9b496a8bbed9
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues: []
  next_action: 作者加 Ridong 守卫出下一版，Waiman 评审后收取
contribution_opportunities:
- kind: testing
  description: 跑 ISOLCPUS_DOMAIN_TEST_MATRIX 验证含 parent 非有效分区边角在内无 GPF 且 prs_err 语义正确
- kind: review
  description: 复核非顶层 parent 用 effective_xcpus 而非 cpu_possible_mask 的正确性
generated_at: '2026-11-13T09:00:00+08:00'
source_email_count: 2
related_articles:
- sched-20261105-012
- sched-20261107-012
- sched-20261109-005
- sched-20261110-014
- sched-20261111-007
tags:
- cgroup
- topology
title: 'cgroup/cpuset: Keep an active housekeeping CPU in the top sched domain'
layout: article
---

## TL;DR

本文为增量更新，完整脉络见下。

- <a class="article-ref" href="/lkm/2026/11/05/sched-20261105-012-cgroup-cpuset-keep-the-top-sched-domain-non-empty-on-cpu-hot.html">sched-20261105-012</a> / 20261107-012 / 20261109-005 / 20261110-014：Guopeng Zhang（+Ridong Chen）修 cpuset 分区与 hotplug 把顶层调度域清空、触发 `build_sched_domains()` 告警与 `build_perf_domains()` 越界（GPF）的系列，v2→v3 逐轮吸收 Waiman 与 Ridong 的意见。
- <a class="article-ref" href="/lkm/2026/11/11/sched-20261111-007-cgroup-cpuset-keep-the-top-scheduling-domain-populated.html">sched-20261111-007</a>：v4 发出，采纳 Ridong 的统一检查（`tasks_nocpu_error()` 加 `del_cpus` 参数）。
- <a class="article-ref" href="/lkm/2026/11/12/sched-20261112-019-cgroup-cpuset-keep-an-active-housekeeping-cpu-in-the-top-sch.html">sched-20261112-019</a>（今天）：**Ridong 评审 v4 patch 1/2，认可 mask 选择**，但发现一个边角——`validate_partition()` 对「parent 非有效分区」的 invalid child 调用时，`prs_err` 会从 `PERR_INVPARENT` 错报成 `PERR_NOCPUS`；**Guopeng 实测了该 guard 并确认采纳**，同时说明在起点稍有不同的场景下复现并验证了行为保持不变。

## 背景与问题

（承接 <a class="article-ref" href="/lkm/2026/11/05/sched-20261105-012-cgroup-cpuset-keep-the-top-sched-domain-non-empty-on-cpu-hot.html">sched-20261105-012</a> … 20261111-007）boot-isolated CPU 仍留在 `top_cpuset.effective_cpus` 却被排除在调度域之外；只按 `effective_cpus` 分配可能拿走顶层 cpuset 的全部 boot domain housekeeping CPU，得到空顶层调度域，进而 `build_sched_domains()` 告警 + `build_perf_domains()` 越界访问（GPF）。v4 在 32 核 `isolcpus=domain,10-31` 上给出确定性触发。

## 技术方案

（承接 v4 patch 1/2）`tasks_nocpu_error()` 增加 `del_cpus` 参数统一复用、归还 CPU 限定在 parent exclusive grant、顶层保留一个 active `HK_TYPE_DOMAIN_BOOT` CPU。今日 Ridong 认可 mask 选择（`HK_TYPE_DOMAIN_BOOT` 对 top_cpuset 正确、限 local parent 的 `effective_xcpus` 正确丢弃 stale CPU），但补一个边角：`validate_partition()` 也会对「parent 非有效分区」的 invalid child 调此检查，若 parent 无 `cpuset.cpus.exclusive` 且 `effective_xcpus` 已被 `reset_partition_data()` 清空，循环空转后仍因 parent populated 返回 true，把 child 的 `prs_err` 从 `PERR_INVPARENT` 错报为 `PERR_NOCPUS`。Ridong 给出 `else if (!is_partition_valid(parent) || !partition_is_populated(parent))` 的守卫。Guopeng 实测采纳。

## 版本演进与当前进展

*current_version: v4（2026-11-11，`<20261111134250.16852-1-guopeng.zhang@linux.dev>`）*。今日无新版本；作者确认会加 Ridong 的守卫，并澄清「起点不同场景」下的 `PERR_INVCPUS`/`PERR_INVPARENT` 行为与 base 一致（Ridong 描述的用例中 base 与 v4 都返回 `PERR_INVCPUS`，`validate_partition()` 在进 `tasks_nocpu_error()` 前就返回了）。

## Maintainer 意见与讨论焦点

- **Ridong Chen（co-developer / 评审者）**：认可 v4 mask 选择，提出 `prs_err` 错报（PERR_INVPARENT→PERR_NOCPUS）的边角并给出守卫。
- **Guopeng Zhang（作者）**：实测并采纳守卫，说明其在略有不同条件下的复现与行为验证。
- 无 NAK、无未解决分歧（v4 加守卫后即收敛）。核心 cpuset/cgroup 维护者 Waiman 仍未在 v4 上表态。

## 合入评估

*likelihood=medium*。系列经多轮迭代已收敛，Ridong 的边角守卫确认采纳；但 Waiman 尚未对 v4 表态，且涉及隔离 CPU 语义这类易踩边角的改动。*blocking_issues*：无实质阻塞，待采纳守卫后的下一版 + Waiman 评审。*next_action*：作者加 Ridong 守卫出下一版，Waiman Long 评审后收取。

## 效果评估

作者此前给出确定性复现（32 核 `isolcpus=domain,10-31` 三步触发 GPF），属崩溃级正确性修复；无性能数据。

## 我可以参与的点

- **testing**：在带 `isolcpus=domain` 的机器上跑 `ISOLCPUS_DOMAIN_TEST_MATRIX`，验证含 Ridong 边角（parent 非有效分区）在内的各组合下 `prs_err` 语义正确、无 GPF。
- **review**：复核「对非顶层 parent 用 `effective_xcpus` 而非 `cpu_possible_mask`」在祖先更新场景下的正确性。

## 参考链接

- lore thread: https://lore.kernel.org/all/20261111134250.16852-1-guopeng.zhang@linux.dev/
- Ridong 的边角指出: https://lore.kernel.org/all/8b256809-79b1-4438-ae3e-4cceb32cd7c2@linux.dev/
- Guopeng 的回应: https://lore.kernel.org/all/be68fe2a-b0e8-470c-be47-26780a254d53@linux.dev/
