---
id: sched-20261111-007
date: '2026-11-11'
subject: 'cgroup/cpuset: Keep the top scheduling domain populated'
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
  review_outcome: 采纳并修正 Ridong 的统一检查建议；待 Waiman 评审
upstream_commit: null
fixes_commit: 9b496a8bbed9
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues: []
  next_action: Waiman Long 评审 v4 后收取
contribution_opportunities:
- kind: testing
  description: 在 isolcpus=domain 机器上跑 ISOLCPUS_DOMAIN_TEST_MATRIX 验证无 GPF
- kind: review
  description: 复核非顶层 parent 用 effective_xcpus 而非 cpu_possible_mask 的正确性
generated_at: '2026-11-12T09:00:00+08:00'
source_email_count: 6
related_articles:
- sched-20261105-012
- sched-20261107-012
- sched-20261109-005
- sched-20261110-014
tags:
- cgroup
- topology
title: 'cgroup/cpuset: Keep the top scheduling domain populated'
layout: article
---

## TL;DR

本文为增量更新，完整脉络见下。

- <a class="article-ref" href="/lkm/2026/11/05/sched-20261105-012-cgroup-cpuset-keep-the-top-sched-domain-non-empty-on-cpu-hot.html">sched-20261105-012</a>：Guopeng Zhang 的 v2 三补丁系列修复 cpuset 分区操作与 CPU hotplug 把顶层调度域清空、进而触发 `build_sched_domains()` 告警与 `build_perf_domains()` 越界访问（GPF）的问题。刚发出，暂无维护者回复。
- <a class="article-ref" href="/lkm/2026/11/07/sched-20261107-012-cgroup-cpuset-keep-the-top-sched-domain-non-empty-on-cpu-hot.html">sched-20261107-012</a>：Waiman Long（cpuset/cgroup 维护者）评审 patch 1/3——认可代码改动，对自测脚本给四点意见。
- <a class="article-ref" href="/lkm/2026/11/09/sched-20261109-005-cgroup-cpuset-reject-updates-that-empty-the-top-sched-doma.html">sched-20261109-005</a>：Guopeng 逐条回应 Waiman 的 v2 意见，Waiman 撤回一条 misread 的评论。
- <a class="article-ref" href="/lkm/2026/11/10/sched-20261110-014-cgroup-cpuset-reject-updates-that-empty-the-top-sched-domain.html">sched-20261110-014</a>：v3 发出（Guopeng + Ridong Chen 共同署名），Ridong 建议把多处「同一检查、不同 mask」统一成一个 helper（`tasks_nocpu_error()` 显式接收要归还的 CPU）。
- <a class="article-ref" href="/lkm/2026/11/11/sched-20261111-007-cgroup-cpuset-keep-the-top-scheduling-domain-populated.html">sched-20261111-007</a>（今天）：**v4 发出**——采纳 Ridong 的统一检查建议，`tasks_nocpu_error()` 增加显式 `del_cpus`（归还的 CPU）参数、对所有 parent 复用；把「归还的 CPU」限定在 parent 当前的 exclusive grant 内；hotplug 保留 active housekeeping CPU 守卫；kernel 改动收进 patch 1、selftests 收进 patch 2，并新增「有任务本地 parent 下的 CPU 替换」回归。作者还当场回应 Ridong：对非顶层 parent 用 `parent->effective_xcpus` 而非 `cpu_possible_mask`（避免祖先更新把 parent 已不拥有的 CPU 也算作归还）。

## 背景与问题

（承接 <a class="article-ref" href="/lkm/2026/11/05/sched-20261105-012-cgroup-cpuset-keep-the-top-sched-domain-non-empty-on-cpu-hot.html">sched-20261105-012</a> / 20261107-012 / 20261109-005 / 20261110-014）boot-isolated CPU 仍留在 `top_cpuset.effective_cpus`、却被排除在调度域之外；只按 `effective_cpus` 分配 CPU 可能拿走顶层 cpuset 的全部 boot domain housekeeping CPU，得到空顶层调度域，进而 `build_sched_domains()` 告警 + `build_perf_domains()` 越界访问（GPF）。v4 在 32 核 `isolcpus=domain,10-31` 上给出确定性触发：`echo 0-9 > A/cpuset.cpus` 后 `echo root > A/cpuset.cpus.partition` 即 Oops。

## 技术方案

v4 的 patch 1/2 `Keep an active housekeeping CPU in the top sched domain`（`kernel/cgroup/cpuset.c` +70/-15）：

- `tasks_nocpu_error()` 增加 `del_cpus`（本次更新归还给 parent 的 CPU）参数，对所有 parent 统一复用，替代 v3 里「同一检查用不同 mask」的多处散落逻辑。
- 归还的 CPU 限定在 parent 当前的 exclusive grant 内——作者在回复 Ridong 时特意修正：对非顶层 parent 用 `parent->effective_xcpus` 而非 `cpu_possible_mask`，否则祖先更新可能把 parent 已不拥有的 CPU 也算作归还，让 child 误判为仍有效。
- 顶层 cpuset 必须保留一个 active `HK_TYPE_DOMAIN_BOOT` CPU；其它 populated parent 在其当前 exclusive grant 内检查。
- CPU hotplug 传空 `del_cpus`，仅当分区能归还一个 active boot domain housekeeping CPU 时才为恢复顶层域而 invalidate 该分区；仍会 invalidate 自身无 active CPU 的 populated 分区。

patch 2/2 为 selftests（`test_cpuset_prs.sh` +71），新增 `ISOLCPUS_DOMAIN_TEST_MATRIX` 覆盖本地/远程分区更新、恢复、CPU 替换与 hotplug。

`Fixes: 9b496a8bbed9` 与 `Fixes: 0c7f293efc87`，Ridong Chen 共同署名（`Co-developed-by`）。

## 版本演进与当前进展

*current_version: v4（2026-11-11，`<20261111134250.16852-1-guopeng.zhang@linux.dev>`）*。v4 相对 v3：统一 CPU 可用性检查（采纳 Ridong）、归还 CPU 限定在 parent exclusive grant、hotplug 保留 housekeeping 守卫、kernel 与 selftest 分离成两封、新增「populated 本地 parent 下 CPU 替换」回归、更新 Ridong 邮箱。作者当日还对 Ridong 的 v3 建议代码做了一处实质修正（`effective_xcpus` 而非 `cpu_possible_mask`）。

## Maintainer 意见与讨论焦点

- **Ridong Chen（co-developer / 评审者）**：v3 提出「统一检查」重构方向，v4 已采纳；作者对其建议代码做了 `effective_xcpus` vs `cpu_possible_mask` 的修正并回帖说明理由。
- 当日无 Waiman Long 等 cpuset 维护者的新表态。无 NAK、无未解决分歧（v4 已回应上一轮全部意见）。

## 合入评估

*likelihood=medium*。系列经四轮迭代已收敛（v4 采纳并修正了 Ridong 的全部建议），但核心 cpuset/cgroup 维护者 Waiman 尚未在 v4 上表态，且涉及隔离 CPU 语义这类易踩边角的改动。*blocking_issues*：无实质阻塞，待 Waiman 对 v4 的评审。*next_action*：Waiman Long 评审 v4，确认 `tasks_nocpu_error()` 的统一检查与 hotplug 守卫无误后收取。

## 效果评估

作者给出确定性复现（32 核 `isolcpus=domain,10-31` 上三步即触发 GPF），属崩溃级正确性修复；无性能数据。

## 我可以参与的点

- **testing**：在带 `isolcpus=domain` 的机器上跑 v4 新增的 `ISOLCPUS_DOMAIN_TEST_MATRIX`，验证各分区更新/hotplug 组合下顶层调度域始终非空且无 GPF。
- **review**：复核「对非顶层 parent 用 `effective_xcpus` 而非 `cpu_possible_mask`」的修正是否在祖先更新场景下严格正确。

## 参考链接

- lore thread: https://lore.kernel.org/all/20261111134250.16852-1-guopeng.zhang@linux.dev/
- v3: https://lore.kernel.org/all/20261110050324.173461-1-guopeng.zhang@linux.dev/
- 作者对 Ridong 建议的修正: https://lore.kernel.org/all/b90235a0-4ac6-49e9-bb2e-fad23c4ab15a@linux.dev/
