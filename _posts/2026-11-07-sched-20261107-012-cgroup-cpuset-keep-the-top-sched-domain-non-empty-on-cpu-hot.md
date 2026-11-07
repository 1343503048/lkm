---
id: sched-20261107-012
date: '2026-11-07'
subject: 'cgroup/cpuset: Keep the top sched domain non-empty on CPU hotplug'
subsystem: sched
type: fix
status: under_review
severity: high
thread_root_msgid: <20261105130344.664336-1-guopeng.zhang@linux.dev>
lore_url: https://lore.kernel.org/all/ccdab485-e1d1-4055-bb0b-f8f712fc0a9b@redhat.com/
authors:
- Guopeng Zhang
maintainers_involved:
- Waiman Long
current_version: v2
patch_series:
- version: v2
  msgid: <20261105130344.664336-1-guopeng.zhang@linux.dev>
  date: '2026-11-05'
  summary: 3 补丁：分区更新与 hotplug 路径保证顶层调度域非空，防 build_perf_domains 越界
  review_outcome: Waiman 评审 1/3 认可核心改动，给自测脚本四点收尾意见
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
  - 自测脚本四点意见待作者修
  - patch 2/3、3/3 尚无评审
  next_action: 作者按 Waiman 意见修订自测脚本，等 2/3、3/3 评审
contribution_opportunities:
- kind: testing
  description: isolcpus=domain 平台复跑分区创建/CPU offline 循环验证不再 GPF
- kind: review
  description: 核对 patch 2/3 的 top_cpuset_sd_nocpu 归属判定
generated_at: '2026-11-08T09:00:00+08:00'
source_email_count: 1
related_articles:
- sched-20261105-012
tags:
- cgroup
- topology
title: 'cgroup/cpuset: Keep the top sched domain non-empty on CPU hotplug'
layout: article
---

## TL;DR

本文为增量更新，完整脉络见下。

- <a class="article-ref" href="/lkm/2026/11/05/sched-20261105-012-cgroup-cpuset-keep-the-top-sched-domain-non-empty-on-cpu-hot.html">sched-20261105-012</a>：Guopeng Zhang 的 v2 三补丁系列修复 cpuset 分区操作与 CPU hotplug 把顶层调度域清空、进而触发 `build_sched_domains()` 告警与 `build_perf_domains()` 越界访问（GPF）的问题。刚发出 v2，暂无维护者回复。
- <a class="article-ref" href="/lkm/2026/11/07/sched-20261107-012-cgroup-cpuset-keep-the-top-sched-domain-non-empty-on-cpu-hot.html">sched-20261107-012</a>（今天）：**Waiman Long（cpuset/cgroup 维护者）评审 patch 1/3（Reject updates that empty the top sched domain）**——认可代码改动本身（「The code change above looks good to me」），但对自测脚本给出四点意见：test 脚本里 `==` 误写成 `=`、对「不该有 nohz_full CPU」的断言理由不充分（domain isolated 与 nohz_full CPU 不必 exclusive）、新测试代码应挪到 ISOLCPUS 段之后复用 `BOOT_ISOLCPUS` 变量、新 test matrix 应与其它 matrix 归在一起。属自测收尾级意见，方向无异议。

## 背景与问题

（承接 <a class="article-ref" href="/lkm/2026/11/05/sched-20261105-012-cgroup-cpuset-keep-the-top-sched-domain-non-empty-on-cpu-hot.html">sched-20261105-012</a>）boot-isolated CPU 仍留在 `top_cpuset.effective_cpus` 却被 `generate_sched_domains()` 排除；若只查 `effective_cpus` 给分区分配 CPU，可能把顶 cpuset 所有 boot domain housekeeping CPU 都拿走，得到空顶层调度域，触发 GPF。patch 1/3 要求分区创建/更新保留一个 active boot domain housekeeping CPU 并补 `test_cpuset_prs.sh` 用例。

今日 Waiman 的评审聚焦于 patch 1/3 附带的自测脚本质量，非核心逻辑。

## 技术方案

（承接）1/3 要求本地与远程分区创建、CPU mask 更新都保留一个 active boot domain housekeeping CPU，否则拒绝。今日无技术变更，为自测脚本的评审意见：

- `==` 写成 `=`（test 脚本笔误）。
- 「不该有 nohz_full CPU」断言的理由需补充：domain isolated CPU 与 nohz_full CPU 不必是 exclusive 关系。
- 新测试代码挪到 ISOLCPUS 段之后，复用已读入 `BOOT_ISOLCPUS` 的 `/sys/devices/system/cpu/isolated` 值，避免再读一次 sysfs。
- 新 test matrix 与既有 test matrix 归并放置。

## 版本演进与当前进展

*current_version: v2（2026-11-05 发出）*。今日 Waiman Long 评审 patch 1/3，无新版本。

## Maintainer 意见与讨论焦点

Waiman Long（cpuset/cgroup 维护者）：「The code change above looks good to me」——认可核心改动；随后给出四点自测收尾意见（`==`、nohz_full 断言理由、ISOLCPUS 复用、matrix 归并）。无 NAK，无对核心逻辑的异议。

## 合入评估

*likelihood=medium*。核心改动获维护者认可，剩余是自测脚本收尾；但仍只有 1/3 被评审，2/3（hotplug 非空）、3/3 尚未有维护者意见。*blocking_issues*：① 自测脚本四点意见待作者修；② patch 2/3、3/3 尚无评审。*next_action*：作者按 Waiman 意见修订自测脚本，并等待 2/3、3/3 的评审。

## 效果评估

作者此前给出可复现触发命令与 `Oops: general protection fault, RIP: build_perf_domains` 崩溃栈，但无修复后回归验证数据。今日为自测脚本评审，无新数据。

## 我可以参与的点

- **testing**：在带 `isolcpus=domain` 平台复跑分区创建/CPU offline 循环，验证 v2 三补丁后顶层调度域始终非空、不再 GPF。
- **review**：核对 `top_cpuset_sd_nocpu()` 对「子分区仍占用的旧独占 CPU」的归属判定（patch 2/3 的 hotplug 路径），这是尚未有人评审的部分。

## 参考链接

- lore thread（Waiman 对 1/3 的评审）: https://lore.kernel.org/all/ccdab485-e1d1-4055-bb0b-f8f712fc0a9b@redhat.com/
- lore thread（系列 cover）: https://lore.kernel.org/all/20261105130344.664336-1-guopeng.zhang@linux.dev/
