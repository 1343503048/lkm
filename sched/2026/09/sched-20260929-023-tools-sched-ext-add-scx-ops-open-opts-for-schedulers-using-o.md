# tools/sched_ext: Add SCX_OPS_OPEN_OPTS for schedulers using open opts

> **subject**：`tools/sched_ext: Add SCX_OPS_OPEN_OPTS for schedulers using open opts`

## TL;DR

本文为增量更新，完整脉络见 related_articles。Fuyu Zhao 为 sched_ext 工具链新增 `SCX_OPS_OPEN_OPTS()`/`SCX_OPS_CID_OPEN_OPTS()` 宏，让调度器在打开 BPF skeleton 时能传自定义 `bpf_object_open_opts`，同时保留内核版本兼容检查。

- sched-20260922-006：初版加 `SCX_OPS_OPEN_OPTS()`，Tejun 建议 `SCX_OPS_OPEN()` 以 0 为 opts 调用减少重复。
- sched-20260924-016：Tejun 复审要求对称加 `SCX_OPS_CID_OPEN_OPTS()`。
- sched-20260928-006：v3 发出，补上 `SCX_OPS_CID_OPEN_OPTS()` 并让两入口对称；Andrea Righi 给 Reviewed-by。
- sched-20260929-023（今天）：Tejun Heo 回复「Applied to sched_ext/for-7.4」，v3 正式合入。

## 背景与问题

（承接）sched_ext 调度器用 `SCX_OPS_OPEN()` 打开 BPF skeleton 并做内核版本兼容检查（`hotplug_seq`、`dump()`、`cgroup_set_bandwidth` 等）；需要传额外 open opts 的调度器若改走 bpftool 生成的 `*_open_opts()` 会绕过兼容处理。今天无新背景，进展是合入。

## 技术方案

（承接）把骨架打开统一为 `__scx_name##__open_opts(__opts)`，新增 `SCX_OPS_OPEN_OPTS()` 与 `SCX_OPS_CID_OPEN_OPTS()` 两个入口，`SCX_OPS_OPEN()`/`SCX_OPS_CID_OPEN()` 分别以 0 为 opts 调用对应 `_OPTS` 宏，保证两入口对称。

## 版本演进与当前进展

*current_version: v3*（`<20260928030955.12353-1-zhaofuyu@vivo.com>`）。v1（09-22）→ v2（09-23 收敛为以 0 调用）→ v3（09-28 补 `SCX_OPS_CID_OPEN_OPTS()`）→ 09-29 Tejun 收「Applied to sched_ext/for-7.4」。

## Maintainer 意见与讨论焦点

- **Tejun Heo**（sched_ext 维护者）：前几轮的两条意见（`SCX_OPS_OPEN()` 以 0 调用、对称加 `SCX_OPS_CID_OPEN_OPTS()`）在 v3 落实，09-29 确认「Applied to sched_ext/for-7.4.」。
- **Andrea Righi**（sched_ext 维护者）：v3 `Reviewed-by`。
- 无 NAK。

## 合入评估

*likelihood=merged*。v3 已合入 sched_ext/for-7.4（纯工具链、低风险，两维护者均已认可）。*blocking_issues*：无。*next_action*：跟踪 sched_ext/for-7.4 随 7.4 合并窗口的 PR。

## 效果评估

无性能数据；属工具链易用性增强（允许传 open opts 而不丢兼容检查，OPEN/CID_OPEN 两入口对称）。

## 我可以参与的点

- `testing`：在用到 open opts（含 CID 变体）的 sched_ext 调度器上验证兼容检查与 skeleton 打开行为。

## 参考链接

- lore（v3 补丁）: https://lore.kernel.org/all/20260928030955.12353-1-zhaofuyu@vivo.com/
- lore（Tejun 收取）: https://lore.kernel.org/all/d9f8e00d70aa015cd2188bf8c62606f0@kernel.org/

---
id: sched-20260929-023
date: '2026-09-29'
subject: 'tools/sched_ext: Add SCX_OPS_OPEN_OPTS for schedulers using open opts'
subsystem: sched
type: feature
status: merged_tip
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
    review_outcome: 'Andrea Righi Reviewed-by；09-29 Tejun Applied to sched_ext/for-7.4'
upstream_commit: null
fixes_commit: null
merged_branch: 'sched_ext/for-7.4'
merge_assessment:
  likelihood: merged
  blocking_issues: []
  next_action: '跟踪 sched_ext/for-7.4 随 7.4 合并窗口的 PR'
contribution_opportunities:
  - kind: testing
    description: '在含 CID 变体的 sched_ext 调度器上验证 open opts 兼容检查与打开行为'
generated_at: '2026-09-30T01:15:00'
source_email_count: 1
related_articles:
  - sched-20260928-006
tags:
  - sched_ext
---