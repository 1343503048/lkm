---
id: sched-20260924-016
date: '2026-09-24'
subject: 'tools/sched_ext: Add SCX_OPS_OPEN_OPTS for schedulers using open opts'
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
- version: v2
  msgid: <20260923035613.20099-1-zhaofuyu@vivo.com>
  date: '2026-09-23'
  summary: SCX_OPS_OPEN 以 0 opts 调 SCX_OPS_OPEN_OPTS 收敛单份展开
  review_outcome: Tejun 请对称加 SCX_OPS_CID_OPEN_OPTS 并出 v3
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: []
  next_action: 作者补 SCX_OPS_CID_OPEN_OPTS 出 v3，Tejun 复审收取
contribution_opportunities:
- kind: testing
  description: 验证 OPEN/CID_OPEN 两入口的 open opts 兼容检查与打开行为
- kind: review
  description: 确认 CID 变体对称收敛后旧宏用户无回归
generated_at: '2026-09-25T09:00:00'
source_email_count: 1
related_articles:
- sched-20260923-013
- sched-20260922-006
tags:
- sched_ext
title: 'tools/sched_ext: Add SCX_OPS_OPEN_OPTS for schedulers using open opts'
layout: article
---

## TL;DR
- <a class="article-ref" href="/lkm/2026/09/22/sched-20260922-006-tools-sched-ext-add-scx-ops-open-opts-for-schedulers-using-o.html">sched-20260922-006</a>：Fuyu Zhao 为 sched_ext 工具链新增 `SCX_OPS_OPEN_OPTS()` 宏，让调度器在打开 BPF skeleton 时能传自定义 `bpf_object_open_opts`，同时保留 `SCX_OPS_OPEN()` 的兼容性检查；Tejun Heo 建议 `SCX_OPS_OPEN()` 以 0 为 opts 调 `SCX_OPS_OPEN_OPTS()` 减少重复。
- <a class="article-ref" href="/lkm/2026/09/23/sched-20260923-013-tools-sched-ext-add-scx-ops-open-opts-for-schedulers-using-o.html">sched-20260923-013</a>：v2 采纳 Tejun 建议，`SCX_OPS_OPEN()` 内部以 0 opts 调 `SCX_OPS_OPEN_OPTS()`，收敛为单份展开，待 Tejun 复审。
- <a class="article-ref" href="/lkm/2026/09/24/sched-20260924-016-tools-sched-ext-add-scx-ops-open-opts-for-schedulers-using-o.html">sched-20260924-016</a>（今天，增量更新）：Tejun Heo 复审 v2 后提出扩展——请作者同样加一个 `SCX_OPS_CID_OPEN_OPTS()`，并让 `SCX_OPS_CID_OPEN()` 以 0 调用它，与 `SCX_OPS_OPEN()` 保持对称（CID 变体是调度器里按 cgroup id 打开的入口）。方向认可、无 NAK，进入下一轮小改。

## 背景与问题
- <a class="article-ref" href="/lkm/2026/09/22/sched-20260922-006-tools-sched-ext-add-scx-ops-open-opts-for-schedulers-using-o.html">sched-20260922-006</a>：`sched_ext` 调度器用 `SCX_OPS_OPEN()` 打开 BPF skeleton 并做内核版本兼容检查（`hotplug_seq`、`dump()` 字段、`cgroup_set_bandwidth` 等）；需要传额外 open opts 的调度器用 bpftool 生成的 `*_open_opts()` 会绕过这套兼容处理。
- <a class="article-ref" href="/lkm/2026/09/24/sched-20260924-016-tools-sched-ext-add-scx-ops-open-opts-for-schedulers-using-o.html">sched-20260924-016</a>（今天）：无新背景，属 v2 复审后对 CID 变体的对称扩展。

## 技术方案
- <a class="article-ref" href="/lkm/2026/09/22/sched-20260922-006-tools-sched-ext-add-scx-ops-open-opts-for-schedulers-using-o.html">sched-20260922-006</a>：重构 `__SCX_OPS_OPEN` 接受 open 表达式，新增 `SCX_OPS_OPEN_OPTS(__ops_name, __scx_name, __opts)`，`SCX_OPS_OPEN()` 保留为旧宏。
- <a class="article-ref" href="/lkm/2026/09/23/sched-20260923-013-tools-sched-ext-add-scx-ops-open-opts-for-schedulers-using-o.html">sched-20260923-013</a>：v2 把 skeleton 打开统一为 `__scx_name##__open_opts(__opts)`，`SCX_OPS_OPEN()` 以 0 为 opts 调 `SCX_OPS_OPEN_OPTS()`。
- <a class="article-ref" href="/lkm/2026/09/24/sched-20260924-016-tools-sched-ext-add-scx-ops-open-opts-for-schedulers-using-o.html">sched-20260924-016</a>（今天）：Tejun 要求对称地新增 `SCX_OPS_CID_OPEN_OPTS()`，并让 `SCX_OPS_CID_OPEN()` 以 0 调用它（`SCX_OPS_CID_OPEN` 是 CID 场景的打开入口，此前 `__SCX_OPS_OPEN(__ops_name, __scx_name, "sched_ext_ops_cid")` 需要同样支持自定义 opts）。无实质代码变化争议，纯接口对称扩展。

## 版本演进与当前进展
- v1（09-22）→ v2（09-23，`<20260923035613.20099-1-zhaofuyu@vivo.com>`）。本日（09-24）Tejun 复审后请加 `SCX_OPS_CID_OPEN_OPTS()`，进入 v3 预期。

## Maintainer 意见与讨论焦点
- **Tejun Heo（sched_ext 维护者）**：认可 v2 收敛方向，提出对称扩展（`SCX_OPS_CID_OPEN_OPTS()` + `SCX_OPS_CID_OPEN()` 以 0 调用）。无 NAK。

## 合入评估
*likelihood=high*。方向认可、仅差一个对称接口扩展，纯工具链改动低风险。*blocking_issues*：无实质项，待作者补 `SCX_OPS_CID_OPEN_OPTS()` 后复审。*next_action*：作者补 CID 变体并出 v3，Tejun 复审后收取。

## 效果评估
无性能数据，纯工具链易用性增强（允许传 open opts 而不丢兼容检查，且 OPEN/CID_OPEN 两入口对称）。

## 我可以参与的点
- kind=testing：在用到 open opts（含 CID 变体）的 sched_ext 调度器上验证 `SCX_OPS_OPEN_OPTS`/`SCX_OPS_CID_OPEN_OPTS` 的兼容检查与 skeleton 打开行为。
- kind=review：确认 `SCX_OPS_CID_OPEN_OPTS` 与 `SCX_OPS_CID_OPEN` 对称收敛后各旧宏用户无回归。

## 参考链接
- lore (v2 补丁): https://lore.kernel.org/all/20260923035613.20099-1-zhaofuyu@vivo.com/
- Tejun CID 扩展请求: https://lore.kernel.org/all/87f1a460f3dee3782d6161ec5493ff2c@kernel.org/
