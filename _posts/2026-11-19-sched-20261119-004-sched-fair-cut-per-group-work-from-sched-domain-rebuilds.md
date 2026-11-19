---
id: sched-20261119-004
date: '2026-11-19'
subject: 'sched/fair: Cut per-group work from sched domain rebuilds'
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: <20261118-bug-sched-fair-offline-active-v2-0-b6ede596c6a6@linux.dev>
lore_url: https://lore.kernel.org/all/20261118-bug-sched-fair-offline-active-v2-0-b6ede596c6a6@linux.dev/
authors:
- Qiliang Yuan
maintainers_involved: []
current_version: v2
patch_series:
- version: v1
  msgid: <20261111-bug-sched-fair-offline-active-v1-0-4f54523c5a70@linux.dev>
  date: '2026-11-11'
  summary: 针对重建时 per-CPU 全量 task group walk 的优化
  review_outcome: 承接 Dietmar 对 f60a631ab9ed 的 offline 侧评审
- version: v2
  msgid: <20261118-bug-sched-fair-offline-active-v2-0-b6ede596c6a6@linux.dev>
  date: '2026-11-18'
  summary: 回调加 hotplug 布尔参，状态未变时跳过 fair walk；补 benchmark
  review_outcome: Li kunyu 质疑 hotplug 参数未被实现消费
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
  - hotplug 参数使用语义待澄清
  - 待维护者评审
  next_action: 作者澄清 hotplug 参数用途，等待维护者评审 v2
contribution_opportunities:
- kind: review
  description: 核对 patch 2/3 是否消费 hotplug 参数、分区重建场景是否安全
- kind: testing
  description: 大规模 cgroup + 频繁 hot-add vCPU 复测重建耗时与功能回归
generated_at: '2026-11-20T09:00:00+08:00'
source_email_count: 4
related_articles:
- sched-20261112-003
tags:
- cfs
- load_balance
- topology
- cgroup
title: 'sched/fair: Cut per-group work from sched domain rebuilds'
layout: article
---

## TL;DR

本文为增量更新，完整脉络见下。

- <a class="article-ref" href="/lkm/2026/11/12/sched-20261112-003-sched-fair-cut-per-group-work-from-sched-domain-rebuilds.html">sched-20261112-003</a>：Qiliang Yuan 的 v1 针对「sched domain 重建时 `rq_offline_fair()`/`rq_online_fair()` 对每个 CPU 遍历全部 task group」的 O(nr_cpus × nr_task_groups) 开销做优化，Dietmar Eggemann 在 f60a631ab9ed 评审时就点出 offline 侧问题；作者同事报出 AI agent harness 主机上千个 cpu cgroup、VM 运行中 hot-add vCPU 的痛点场景。
- <a class="article-ref" href="/lkm/2026/11/19/sched-20261119-004-sched-fair-cut-per-group-work-from-sched-domain-rebuilds.html">sched-20261119-004</a>（今天）：**v2 发出**——patch 1 给 `rq_online()/rq_offline()` 回调加 `hotplug` 布尔参、告知 CPU 是否真的改变状态；patch 2/3 据此在「CPU 状态未变」时跳过 fair 侧两次全量 walk。4000 cgroup/32 CPU 实测 partition root -92%、cpu offline -67%、cpu online -64%。Li kunyu 评审质疑：新加的 `hotplug` 参数在 `rq_online_fair()` 等实现里看似未被使用。

## 背景与问题

（承接 <a class="article-ref" href="/lkm/2026/11/12/sched-20261112-003-sched-fair-cut-per-group-work-from-sched-domain-rebuilds.html">sched-20261112-003</a>）sched domain 重建（CPU hotplug 或 cpuset 分区变更）通过 `rq_attach_root()` 把每个 active CPU 移到新 root domain，每颗 CPU 都要在持有 rq lock、关中断的情况下跑 `rq_offline_fair()` + `rq_online_fair()` 遍历所有 task group，重建开销 O(nr_cpus × nr_task_groups)。运行 AI agent harness 的主机常承载上千个 cpu cgroup，其 VM 又在运行中 hot-add vCPU，重建路径放大后成为可观测的卡顿源。

## 技术方案

- **patch 1**：给 `rq_online()/rq_offline()` 回调增加一个布尔参数，告知「CPU 是否真的改变状态」（区分「hotplug 真正下线/上线」与「仅重挂 root domain」）。
- **patch 2**：`rq_offline_fair()` 对保持 active 的 CPU 跳过工作。
- **patch 3**：`rq_online_fair()` 同理，并避免对未变化的 root domain 重复同步 `runtime_enabled`。
- 效果（作者实测，4000 cpu cgroup / 32 CPU VM / rt_group_sched=0，20 次分区切换 + 16 次 hotplug 的中位数，三内核同轮对比）：`partition root` 14.86→1.20 ms（-92%）、`cpu offline` 49.99→16.49 ms（-67%）、`cpu online` 36.10→12.87 ms（-64%）；`rq_attach_root()` 单次（关中断执行）中位数/p90/max 同步下降。

## 版本演进与当前进展

*current_version: v2（2026-11-18，`<20261118-bug-sched-fair-offline-active-v2-0-b6ede596c6a6@linux.dev>`，3 补丁）*。v1 → v2：补全 cover 动机与 benchmark 数据、把「状态是否改变」显式化为回调布尔参数。今日收到 Li kunyu 的评审质疑（见下）。

## Maintainer 意见与讨论焦点

- **Li kunyu（社区评审）**：指出 `set_rq_online/set_rq_offline` 与各 class 回调都加了 `hotplug` 参数，但 `rq_online_fair(struct rq *rq, bool hotplug)` 等实现里该参数看似未被使用，问「是当前未用、还是为将来用例预留在回调层」。
- 调度维护者（Peter/Ingo）当日未直接表态；Dietmar Eggemann 在上一轮（f60a631ab9ed 评审）已点出 offline 侧问题，本系列正是承接其建议。
- 无 NAK；当前焦点是 `hotplug` 参数在 fair 实现中的实际消费是否充分。

## 合入评估

*likelihood=medium*。方向清晰、收益数据扎实（三项操作 -64%~-92%），但 `hotplug` 参数「声明了却看似没用」的评审质疑需作者澄清（可能是 patch 2/3 实际消费、或评审者只看了声明层）。*blocking_issues*：`hotplug` 参数使用语义待澄清；待调度维护者评审。*next_action*：作者回应 Li kunyu 的参数用途，并等待维护者评审 v2。

## 效果评估

作者给出量化数据（承接「技术方案」）：partition root -92%、cpu offline -67%、cpu online -64%，且 `rq_attach_root()`（关中断路径）中位/p90/max 均下降。为作者自测，未见第三方独立复现。

## 我可以参与的点

- **review**：核对 patch 2/3 是否真的消费 `hotplug` 参数、以及「状态未变即跳过」在 cpuset 分区重建（非 hotplug）场景下是否安全。
- **testing**：在大规模 cgroup（>1000）+ 频繁 hot-add vCPU 的 VM 上复测 v2 的重建耗时，验证无功能回归。

## 参考链接

- lore thread（v2 cover）: https://lore.kernel.org/all/20261118-bug-sched-fair-offline-active-v2-0-b6ede596c6a6@linux.dev/
- Li kunyu 评审: https://lore.kernel.org/all/6fd92ba8-2249-b5e1-772d-cc598c91bad5@open-hieco.net/
