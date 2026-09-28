# tools/sched_ext: Add SCX_OPS_OPEN_OPTS for schedulers using open opts

## TL;DR

本文为增量更新，完整脉络见 related_articles。Fuyu Zhao 为 sched_ext 工具链新增 `SCX_OPS_OPEN_OPTS()`/`SCX_OPS_CID_OPEN_OPTS()` 宏，让调度器在打开 BPF skeleton 时能传自定义 `bpf_object_open_opts`，同时保留原有的内核版本兼容检查。

- sched-20260922-006：初版加 `SCX_OPS_OPEN_OPTS()`，Tejun 建议 `SCX_OPS_OPEN()` 以 0 为 opts 调用它减少重复。
- sched-20260924-016：Tejun 复审后要求对称地加 `SCX_OPS_CID_OPEN_OPTS()`，进入 v3 预期。
- sched-20260928-006（今天）：v3 发出，补上 `SCX_OPS_CID_OPEN_OPTS()` 并让 `SCX_OPS_CID_OPEN()` 以 0 调用；Andrea Righi 给出 Reviewed-by，待 Tejun 收取。

## 背景与问题

（承接）`sched_ext` 调度器用 `SCX_OPS_OPEN()` 打开 BPF skeleton 并做内核版本兼容检查（`hotplug_seq`、`dump()` 字段、`cgroup_set_bandwidth` 等）；需要传额外 open opts 的调度器若改走 bpftool 生成的 `*_open_opts()`，会绕过这套兼容处理。今天无新背景，纯是前一版评审意见的收敛。

## 技术方案

（承接）把骨架打开统一为 `__scx_name##__open_opts(__opts)`，新增 `SCX_OPS_OPEN_OPTS()` 与 `SCX_OPS_CID_OPEN_OPTS()` 两个入口，`SCX_OPS_OPEN()`/`SCX_OPS_CID_OPEN()` 分别以 0 为 opts 调用对应 `_OPTS` 宏，保证两入口对称。v3 新增的就是 `SCX_OPS_CID_OPEN_OPTS()`（CID 变体是调度器按 cgroup id 打开的场景）。

## 版本演进与当前进展

*current_version: v3*（`<20260928030955.12353-1-zhaofuyu@vivo.com>`）。v1（09-22）→ v2（09-23，`SCX_OPS_OPEN()` 收敛为以 0 调用）→ v3（09-28，按 Tejun 要求补 `SCX_OPS_CID_OPEN_OPTS()`）。Andrea Righi 当日对 v3 给出 Reviewed-by。

## Maintainer 意见与讨论焦点

- **Tejun Heo**（sched_ext 维护者）：前几轮提出的两条意见（`SCX_OPS_OPEN()` 以 0 调用、加 `SCX_OPS_CID_OPEN_OPTS()`）均在 v3 落实。无 NAK。
- **Andrea Righi**（sched_ext 维护者）：v3 `Reviewed-by: Andrea Righi`。

## 合入评估

*likelihood=high*。方向早已认可、两维护者其一已给 Reviewed-by，改动纯工具链、低风险。*blocking_issues*：无实质项，仅等 Tejun 最终收取（或并入 sched_ext 工具链分支）。*next_action*：等待 Tejun 收取/合入；如长期未动，可在 sched_ext 邮件列表 bump。

## 效果评估

无性能数据；属工具链易用性增强（允许传 open opts 而不丢兼容检查，且 OPEN/CID_OPEN 两入口对称）。

## 我可以参与的点

- `testing`：在用到 open opts（含 CID 变体）的 sched_ext 调度器上验证 `SCX_OPS_OPEN_OPTS`/`SCX_OPS_CID_OPEN_OPTS` 的兼容检查与 skeleton 打开行为。
- `review`：确认 CID 变体对称收敛后，各旧宏用户（`SCX_OPS_OPEN`/`SCX_OPS_CID_OPEN`）无回归。

## 参考链接

- v3 补丁: https://lore.kernel.org/all/20260928030955.12353-1-zhaofuyu@vivo.com/
- Andrea Righi Reviewed-by: https://lore.kernel.org/all/aroIi7aE6wdJH3Tv@gpd4/

---
id: sched-20260928-006
date: '2026-09-28'
subject: 'tools/sched_ext: Add SCX_OPS_OPEN_OPTS for schedulers using open opts'
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: '<20260928030955.12353-1-zhaofuyu@vivo.com>'
lore_url: 'https://lore.kernel.org/all/20260928030955.12353-1-zhaofuyu@vivo.com/'
authors:
  - 'Fuyu Zhao'
maintainers_involved:
  - 'Tejun Heo'
  - 'Andrea Righi'
current_version: v3
patch_series:
  - version: v3
    msgid: '<20260928030955.12353-1-zhaofuyu@vivo.com>'
    date: '2026-09-28'
    summary: '补 SCX_OPS_CID_OPEN_OPTS()，SCX_OPS_CID_OPEN() 以 0 调用，两入口对称'
    review_outcome: 'Andrea Righi Reviewed-by；待 Tejun 收取'
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: []
  next_action: '等待 Tejun 收取/合入'
contribution_opportunities:
  - kind: testing
    description: '在含 CID 变体的 sched_ext 调度器上验证 open opts 兼容检查与打开行为'
  - kind: review
    description: '确认 CID 变体对称收敛后旧宏用户无回归'
generated_at: '2026-09-29T01:00:00'
source_email_count: 3
related_articles:
  - sched-20260924-016
  - sched-20260923-013
  - sched-20260922-006
tags:
  - sched_ext
---