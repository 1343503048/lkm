---
id: sched-20261105-012
date: 2026-11-05
subject: 'cgroup/cpuset: Keep the top sched domain non-empty on CPU hotplug'
subsystem: sched
type: fix
status: under_review
severity: high
thread_root_msgid: <20261105130344.664336-1-guopeng.zhang@linux.dev>
lore_url: https://lore.kernel.org/all/20261105130344.664336-1-guopeng.zhang@linux.dev/
authors:
- Guopeng Zhang
maintainers_involved: []
current_version: v2
patch_series:
- version: v2
  msgid: <20261105130344.664336-1-guopeng.zhang@linux.dev>
  date: 2026-11-05
  summary: 3 补丁：分区更新与 hotplug 路径保证顶层调度域非空，防 build_perf_domains 越界。
  review_outcome: 刚发出，暂无 review。
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues: []
  next_action: 等待 cpuset/cgroup 维护者评审
contribution_opportunities:
- kind: testing
  description: 在 isolcpus=domain 平台复跑分区/offline 循环验证不 GPF
- kind: review
  description: 核对 top_cpuset_sd_nocpu 对子分区旧独占 CPU 的归属判定
generated_at: '2026-11-06T09:00:00+08:00'
source_email_count: 2
related_articles: []
tags:
- cgroup
- topology
title: 'cgroup/cpuset: Keep the top sched domain non-empty on CPU hotplug'
layout: article
---

## TL;DR

Guopeng Zhang 的 v2 三补丁系列（本文基于其 2/3 主题）修复 cpuset 分区操作与 CPU hotplug 把顶层调度域清空、进而触发 `build_sched_domains()` 告警与 `build_perf_domains()` 越界访问（`Oops: general protection fault`）的问题。通过要求分区创建/更新与 hotplug 路径都保留一个 active boot domain housekeeping CPU，并补测试用例。刚发出 v2，暂无维护者回复。

## 背景与问题

boot-isolated CPU 仍留在 `top_cpuset.effective_cpus` 中，却被 `generate_sched_domains()` 排除在调度域之外。若只检查 `effective_cpus` 来给分区分配 CPU，就可能把顶 cpuset 的所有 boot domain housekeeping CPU 都拿走，得到空的顶层调度域——`build_sched_domains()` 会告警，`build_perf_domains()` 会出现越界 CPU 访问（GPF）。root 与 isolated 分区、本地与远程都可能触发。示例（32 核、`isolcpus=domain,10-31`）：`echo 0-9 > A/cpuset.cpus; echo root > A/cpuset.cpus.partition` 即 GPF。

hotplug 路径（2/3）另有独立漏洞：本地分区带子分区时，`cpuset_hotplug_update_tasks()` 把分区自身 effective CPUs 传给 `tasks_nocpu_error()`，内嵌的 `top_cpuset_sd_nocpu()` 检查把不在该 mask 里的旧独占 CPU 误算作「归还给顶 cpuset」的 CPU——但这些 CPU 可能仍属子分区，实际并未归还，仍会空掉顶层域。

## 技术方案

- 1/3（Reject updates that empty the top sched domain）：要求本地与远程分区创建、CPU mask 更新都保留一个 active boot domain housekeeping CPU（计入同一次更新归还的 CPU），否则拒绝；并给 `test_cpuset_prs.sh` 补用例。
- 2/3（Keep the top sched domain non-empty on CPU hotplug）：修正 hotplug 路径里「归还 CPU」的误判（旧独占 CPU 属子分区时不算归还），并补上远程分区 hotplug 检查遗漏顶层域的情况。

## 版本演进与当前进展

*current_version: v2（2026-11-05 发出）*。v2 相对 v1 的 diff 未在当日缓存中获取到（仅 1/3、2/3 正文）；v2 补了 `test_cpuset_prs.sh` 测试用例。今日无回复。

## Maintainer 意见与讨论焦点

暂无任何维护者或 reviewer 回复，本日无讨论。

## 合入评估

*likelihood=medium*。修复针对真实可复现的 GPF，且带自测，但刚发出、无评审。*blocking_issues*：暂无（等待评审）。*next_action*：等待 cpuset/cgroup 维护者（Tejun Heo 等）评审；建议作者确认 v2 的 changelog 里给出 v1→v2 的改动说明。

## 效果评估

作者给出可复现的触发命令与 `Oops: general protection fault, RIP: build_perf_domains` 崩溃栈，但未提供修复后的回归/功能验证数据；测试用例已加入自测。

## 我可以参与的点

- testing：在带 `isolcpus=domain` 的平台上复跑分区创建/CPU offline 循环，验证 v2 两补丁后顶层调度域始终非空、不再 GPF。
- review：核对 `top_cpuset_sd_nocpu()` 对「子分区仍占用的旧独占 CPU」的归属判定是否正确。

## 参考链接

- lore thread（系列 cover）: https://lore.kernel.org/all/20261105130344.664336-1-guopeng.zhang@linux.dev/
- 2/3（hotplug 非空）: https://lore.kernel.org/all/20261105130344.664336-3-guopeng.zhang@linux.dev/
