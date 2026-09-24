---
id: sched-20260923-013
subject: 'tools/sched_ext: Add SCX_OPS_OPEN_OPTS for schedulers using open opts'
date: '2026-09-23'
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: <20260923035613.20099-1-zhaofuyu@vivo.com>
lore_url: https://lore.kernel.org/all/20260923035613.20099-1-zhaofuyu@vivo.com/
authors:
- Fuyu Zhao
maintainers_involved:
- Tejun Heo
current_version: v2
patch_series:
- version: v1
  msgid: <20260922031618.2858-1-zhaofuyu@vivo.com>
  date: '2026-09-22'
  summary: 新增 SCX_OPS_OPEN_OPTS 宏，保留兼容检查同时允许传 open opts
  review_outcome: Tejun 建议 SCX_OPS_OPEN 以 0 opts 调 SCX_OPS_OPEN_OPTS
- version: v2
  msgid: <20260923035613.20099-1-zhaofuyu@vivo.com>
  date: '2026-09-22'
  summary: SCX_OPS_OPEN 以 0 opts 调 SCX_OPS_OPEN_OPTS，收敛单份展开
  review_outcome: 采纳 Tejun 建议，待复审
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues: []
  next_action: Tejun 复审 v2 后收取
contribution_opportunities:
- kind: testing
  description: 在用到 open opts 的调度器上验证兼容检查与打开行为
- kind: review
  description: 确认 SCX_OPS_OPEN 以 0 opts 调用与原实现等价、无回归
generated_at: '2026-09-24T09:00:00'
source_email_count: 2
related_articles:
- sched-20260922-006
tags:
- sched_ext
title: 'tools/sched_ext: Add SCX_OPS_OPEN_OPTS for schedulers using open opts'
layout: article
---

## TL;DR
- <a class="article-ref" href="/lkm/2026/09/22/sched-20260922-006-tools-sched-ext-add-scx-ops-open-opts-for-schedulers-using-o.html">sched-20260922-006</a>：Fuyu Zhao 为 sched_ext 工具链新增 `SCX_OPS_OPEN_OPTS()` 宏，让调度器在打开 BPF skeleton 时能传入自定义 `bpf_object_open_opts`，同时保留 `SCX_OPS_OPEN()` 的兼容性检查。此前直接用 bpftool 生成的 `*_open_opts()` 会绕过 `SCX_OPS_OPEN()` 的兼容校验。Tejun Heo 回帖建议 `SCX_OPS_OPEN()` 直接以 0 为 opts 调 `SCX_OPS_OPEN_OPTS()` 来减少重复。
- <a class="article-ref" href="/lkm/2026/09/23/sched-20260923-013-tools-sched-ext-add-scx-ops-open-opts-for-schedulers-using-o.html">sched-20260923-013</a>（今天）：Fuyu Zhao 发出 v2，按 Tejun Heo 建议让 `SCX_OPS_OPEN()` 内部以 0 为 opts 调 `SCX_OPS_OPEN_OPTS()`，收敛为单份展开，消除两份宏实现的重复。实现已落地，待 Tejun 复审。

## 背景与问题
- <a class="article-ref" href="/lkm/2026/09/22/sched-20260922-006-tools-sched-ext-add-scx-ops-open-opts-for-schedulers-using-o.html">sched-20260922-006</a>：`sched_ext` 调度器用 `SCX_OPS_OPEN()` 宏打开 BPF skeleton，内部做 kernel 版本兼容性检查（`hotplug_seq` 注入、`dump()` 字段存在性、`cgroup_set_bandwidth` 等）。有些调度器需要向 `bpf_object__open` 传额外 open opts，但 bpftool 生成的 `*_open_opts()` 接口会完全绕过 `SCX_OPS_OPEN()` 的兼容处理。
- <a class="article-ref" href="/lkm/2026/09/23/sched-20260923-013-tools-sched-ext-add-scx-ops-open-opts-for-schedulers-using-o.html">sched-20260923-013</a>（今天）：背景无新增，沿用 v1 的问题定义。

## 技术方案
- <a class="article-ref" href="/lkm/2026/09/22/sched-20260922-006-tools-sched-ext-add-scx-ops-open-opts-for-schedulers-using-o.html">sched-20260922-006</a>：把 `__SCX_OPS_OPEN` 重构为接受一个 open 表达式（`__open_expr`），新增 `SCX_OPS_OPEN_OPTS(__ops_name, __scx_name, __opts)` 宏——内部仍走同一套兼容检查（`dump()` 检查、`hotplug_seq`、`SCX_ENUM_INIT`、`cgroup_set_bandwidth` 告警），只是把 skeleton 打开动作换成 `__scx_name##__open_opts(__opts)`。`SCX_OPS_OPEN()` 保留为旧宏，展开为以 `__scx_name##__open()` 为 open 表达式。`tools/sched_ext/include/scx/compat.h` 约 +15/-5 行。
- <a class="article-ref" href="/lkm/2026/09/23/sched-20260923-013-tools-sched-ext-add-scx-ops-open-opts-for-schedulers-using-o.html">sched-20260923-013</a>（今天）：v2 把 `__SCX_OPS_OPEN` 重构为接受 `__opts` 参数，skeleton 打开动作统一为 `__scx_name##__open_opts(__opts)`；`SCX_OPS_OPEN()` 改为以 0 为 opts 调 `SCX_OPS_OPEN_OPTS()`，消除两份宏展开的重复（Tejun 建议，v1→v2 的唯一实质变化）。`tools/sched_ext/include/scx/compat.h` 约 +8/-5 行。

## 版本演进与当前进展
- v1（09-22）：新增 `SCX_OPS_OPEN_OPTS()` 宏，保留兼容检查同时允许传 open opts；`SCX_OPS_OPEN()` 保留为旧宏。Tejun 建议收敛实现。
- **v2**（09-22 23:56 UTC，`<20260923035613.20099-1-zhaofuyu@vivo.com>`）：本日进入缓存，采纳 Tejun 建议（`SCX_OPS_OPEN()` 以 0 opts 调 `SCX_OPS_OPEN_OPTS()`）收敛实现；作者另回帖确认采纳。

## Maintainer 意见与讨论焦点
Tejun Heo 上轮的建议（`SCX_OPS_OPEN()` 直接以 0 opts 调 `SCX_OPS_OPEN_OPTS()`）已被 v2 采纳，作者回帖「Yes, that makes sense. I'll update the patch accordingly.」。无争议、无 NAK。

## 合入评估
*likelihood=medium*。方向无异议、实现已按维护者建议收敛，纯工具链改动低风险；但 v2 尚未得到 Tejun 的复审确认。*blocking_issues*：无明确项（仅待 Tejun 审 v2）。*next_action*：Tejun 复审 v2 后收取。

## 效果评估
无性能数据，纯工具链易用性增强（允许传 open opts 而不丢兼容检查）。

## 我可以参与的点
- kind=testing：在用到 open opts 的 sched_ext 调度器上验证 `SCX_OPS_OPEN_OPTS` 的兼容检查与 skeleton 打开行为。
- kind=review：确认收敛后 `SCX_OPS_OPEN()` 以 0 opts 调用的语义与原实现完全等价、各旧宏用户无回归。

## 参考链接
- lore（v2 补丁）: https://lore.kernel.org/all/20260923035613.20099-1-zhaofuyu@vivo.com/
- lore（v1）: https://lore.kernel.org/all/20260922031618.2858-1-zhaofuyu@vivo.com/
