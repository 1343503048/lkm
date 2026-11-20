---
id: sched-20261120-008
date: '2026-11-20'
subject: 'tools/sched_ext: Add "arena" BTF type tag to the __arena qualifier'
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: <20261120094934.979574-1-sunshaojie@kylinos.cn>
lore_url: https://lore.kernel.org/all/20261120094934.979574-1-sunshaojie@kylinos.cn/
authors:
- Shaojie Sun
maintainers_involved:
- Andrea Righi
current_version: v2
patch_series:
- version: v1
  msgid: <20261119102613.811845-1-sunshaojie@kylinos.cn>
  date: '2026-11-19'
  summary: 仅主定义补 btf_type_tag
  review_outcome: Tao Cui Tested-by；需 rebase + scx 仓库同步
- version: v2
  msgid: <20261120094934.979574-1-sunshaojie@kylinos.cn>
  date: '2026-11-20'
  summary: 补 fallback 定义（Andrea Righi 意见）
  review_outcome: Andrea Righi Reviewed-by
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues:
  - rebase 到当前树
  - sched-ext/scx 仓库侧同步
  next_action: 作者 rebase 后由 Tejun 收取，并在 scx 仓库提同类改动
contribution_opportunities:
- kind: review
  description: 确认 address_space+btf_type_tag 属性序跨 Clang/GCC 可移植性与 fallback 覆盖
generated_at: '2026-11-21T09:00:00+08:00'
source_email_count: 216
related_articles:
- sched-20261119-006
tags:
- sched_ext
title: 'tools/sched_ext: Add "arena" BTF type tag to the __arena qualifier'
layout: article
---

## TL;DR

本文为增量更新，完整脉络见下。

- <a class="article-ref" href="/lkm/2026/11/19/sched-20261119-006-tools-sched-ext-add-arena-btf-type-tag-to-the-arena-qualifie.html">sched-20261119-006</a>：Shaojie Sun 发 1 行修复给 `tools/sched_ext` 的 `__arena` 补 `btf_type_tag("arena")`，与 libarena 对齐；Tao Cui 给 Tested-by 但指出需 rebase + scx 仓库侧同步。
- <a class="article-ref" href="/lkm/2026/11/20/sched-20261120-008-tools-sched-ext-add-arena-btf-type-tag-to-the-arena-qualifie.html">sched-20261120-008</a>（今天）：**v2 发出**——按 Andrea Righi 意见把 tag 也补到 `__arena` 的 fallback 定义上（覆盖旧 LLVM 与 `BPF_ARENA_FORCE_ASM` 构型）；Andrea 已给 Reviewed-by。

## 背景与问题

（承接 <a class="article-ref" href="/lkm/2026/11/19/sched-20261119-006-tools-sched-ext-add-arena-btf-type-tag-to-the-arena-qualifie.html">sched-20261119-006</a>）`libarena` 用 `btf_type_tag("arena")` 标记 arena 类型（commit a0fa68d8ce75），`tools/sched_ext` 的 `__arena` 定义作用相同却缺该 tag，导致两处「如何描述 arena 类型」不一致。v1 只改主定义，未覆盖 fallback 定义。

## 技术方案

v2（`tools/sched_ext/include/scx/bpf_arena_common.bpf.h`，2 处各 1 行）：
- 主定义：`__attribute__((address_space(1))) __attribute__((btf_type_tag("arena")))`。
- fallback 定义：从空宏改为 `__attribute__((btf_type_tag("arena")))`，使旧 LLVM 与 `BPF_ARENA_FORCE_ASM` 构建也记录 tag。
- checkpatch 对「复杂值宏」的报错为误报（宏值是声明属性序列而非表达式），作者在 changelog 说明。

## 版本演进与当前进展

*current_version: v2（2026-11-20，`<20261120094934.979574-1-sunshaojie@kylinos.cn>`，单补丁）*。v1→v2：补 fallback 定义（Andrea Righi 意见）。

## Maintainer 意见与讨论焦点

- **Andrea Righi（sched_ext 共同维护者）**：v2 已给 `Reviewed-by`。
- 无 NAK；此前的 rebase 与 scx 仓库侧同步（20261119-006 中 Tao Cui 的意见）在本日缓存中未见新进展，仍需落地。

## 合入评估

*likelihood=high*。1-2 行工具头改动、维护者 Reviewed-by，不涉及调度核心逻辑。*blocking_issues*：rebase 到当前树、sched-ext/scx 仓库侧同步（承接前文）。*next_action*：作者 rebase 后由 Tejun 收取，并在 scx 仓库提同类改动。

## 效果评估

无性能数据；价值在 BTF 元数据一致性，使「是否 arena 类型」单凭 BTF 即可判断。

## 我可以参与的点

- **review**：确认 `address_space(1)` + `btf_type_tag` 属性序在 Clang/GCC 下的可移植性，以及 fallback 定义补齐后旧 LLVM 路径实际能记录 tag。

## 参考链接

- lore thread（v2）: https://lore.kernel.org/all/20261120094934.979574-1-sunshaojie@kylinos.cn/
