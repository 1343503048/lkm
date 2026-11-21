# tools/sched_ext: Add "arena" BTF type tag to the __arena qualifier

## TL;DR

本文为增量更新，完整脉络见下。

- sched-20261119-006：Shaojie Sun 发 1 行修复给 `tools/sched_ext` 的 `__arena` 补 `btf_type_tag("arena")`，与 libarena 对齐；Tao Cui 给 Tested-by 但指出需 rebase + scx 仓库侧同步。
- sched-20261120-008：v2 发出——按 Andrea Righi 意见把 tag 也补到 `__arena` 的 fallback 定义上；Andrea 已给 Reviewed-by。
- sched-20261121-012（今天）：**Tejun Heo 将该补丁「Applied to sched_ext/for-7.5」**，即已被 sched_ext 维护者收取入树。

## 背景与问题

（承接 sched-20261119-006 … 20261120-008）`libarena` 用 `btf_type_tag("arena")` 标记 arena 类型，`tools/sched_ext` 的 `__arena` 定义作用相同却缺该 tag，导致两处「如何描述 arena 类型」不一致。v1 只改主定义，v2 补齐 fallback 定义。

## 技术方案

v2（`tools/sched_ext/include/scx/bpf_arena_common.bpf.h`，2 处各 1 行）：主定义加 `__attribute__((btf_type_tag("arena")))`；fallback 定义从空宏改为带该 tag 的属性，使旧 LLVM 与 `BPF_ARENA_FORCE_ASM` 构建也记录 tag。

## 版本演进与当前进展

*current_version: v2（2026-11-20，`<20261120094934.979574-1-sunshaojie@kylinos.cn>`，单补丁）*。今日进展为 Tejun 的收取（Applied），无新版本。

## Maintainer 意见与讨论焦点

- **Tejun Heo（sched_ext 维护者）**：本日「Applied to sched_ext/for-7.5. Thanks.」
- **Andrea Righi（sched_ext 共同维护者）**（前情）：v2 已给 Reviewed-by。
- 无 NAK；已进入 maintainer 树，待 7.5 合并窗口。

## 合入评估

*likelihood=high*。已被 Tejun 收取到 `sched_ext/for-7.5` 分支，等价于维护者接受、待合入主线。*blocking_issues*：无阻塞合入主线的问题；scx 仓库侧同步（前情）为独立事项。*next_action*：随 7.5 合并窗口进主线。

## 效果评估

无性能数据；价值在 BTF 元数据一致性，使「是否 arena 类型」单凭 BTF 即可判断。

## 我可以参与的点

当前阶段暂无明显参与空间（已入树），可持续观察后续版本。

## 参考链接

- lore thread（v2）: https://lore.kernel.org/all/20261120094934.979574-1-sunshaojie@kylinos.cn/
- Tejun 收取回帖: https://lore.kernel.org/all/0c503fdf9f38c1b7d2a5853f43609dd9@kernel.org/

---
id: sched-20261121-012
date: '2026-11-21'
subject: 'tools/sched_ext: Add "arena" BTF type tag to the __arena qualifier'
subsystem: sched
type: fix
status: merged_tip
severity: low
thread_root_msgid: "<20261120094934.979574-1-sunshaojie@kylinos.cn>"
lore_url: "https://lore.kernel.org/all/20261120094934.979574-1-sunshaojie@kylinos.cn/"
authors: [Shaojie Sun]
maintainers_involved: [Andrea Righi, Tejun Heo]
current_version: v2
patch_series:
  - version: v1
    msgid: "<20261119102613.811845-1-sunshaojie@kylinos.cn>"
    date: '2026-11-19'
    summary: "仅主定义补 btf_type_tag"
    review_outcome: "Tao Cui Tested-by；需 rebase + scx 仓库同步"
  - version: v2
    msgid: "<20261120094934.979574-1-sunshaojie@kylinos.cn>"
    date: '2026-11-20'
    summary: "补 fallback 定义（Andrea Righi 意见）"
    review_outcome: "Andrea Righi Reviewed-by；Tejun 收取到 sched_ext/for-7.5"
upstream_commit: null
fixes_commit: null
merged_branch: "sched_ext/for-7.5"
merge_assessment:
  likelihood: high
  blocking_issues: []
  next_action: "随 7.5 合并窗口进主线"
contribution_opportunities: []
generated_at: "2026-11-22T01:00:00+08:00"
source_email_count: 91
related_articles: [sched-20261119-006, sched-20261120-008]
tags: [sched_ext]
---