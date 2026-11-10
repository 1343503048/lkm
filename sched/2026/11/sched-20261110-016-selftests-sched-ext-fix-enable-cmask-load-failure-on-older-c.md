# selftests/sched_ext: Fix enable_cmask load failure on older clangs

## TL;DR

Tejun Heo 修 sched_ext `enable_cmask` selftest 在老 clang 上加载失败的问题：该测试把任务 cmask 的 u64 arena 地址 cast 成 `__arena` 指针，但没走 `cast_kern()`，老 clang（无 `__BPF_FEATURE_ADDR_SPACE_CAST`）需要显式 cast，否则测试加载失败。补丁加一行 `cast_kern(m)`，已由作者标记「Applied to sched_ext/for-7.5」。这是对 20261109-013 那条「enable_cmask selftest 在 7.4-rc2 上加载失败」报告的修复。

## 背景与问题

（承接 sched-20261109-013）Zhijian Han 报告 `enable_cmask` selftest（merge window 经 `d781d1b78acf` 加入）在 v7.4-rc2 与 linux-next 上加载失败：`struct scx_cmask __arena *m = (struct scx_cmask __arena *)args->cmask_arena_addr;` 这处 C cast 不产生 `addr_space_cast` insn，首次解引用被 verifier 拒绝。老 clang 缺少 `__BPF_FEATURE_ADDR_SPACE_CAST`，需要显式 `cast_kern()` 才能产生正确的地址空间 cast。

## 技术方案

在 `enable_cmask.bpf.c` 里对 arena 地址显式加 `cast_kern(m)`（`asm volatile("" :: "r"(&arena));` 之后、`tctx = lookup_task_ctx(p);` 之前），让老 clang 也能产生 `addr_space_cast`。改动 `tools/testing/selftests/sched_ext/enable_cmask.bpf.c` 1 行。

## 版本演进与当前进展

*current_version: v1（2026-11-10，`<20261109162623.674441-1-tj@kernel.org>`）*。作者在正文末尾标注「Applied to sched_ext/for-7.5」，即已收款到 sched_ext 的 7.5 特性分支。

## Maintainer 意见与讨论焦点

- **Tejun Heo（sched_ext maintainer）**：亲自出补丁并直接收款（Applied to sched_ext/for-7.5），`Reported-by: Zhijian Han`。无争议。

## 合入评估

*likelihood=merged*。作者已标记 Applied to sched_ext/for-7.5。*blocking_issues*：无。*next_action*：随 sched_ext/for-7.5 进入下个 merge window。

## 效果评估

无性能数据。价值在测试可跑性：修复后老 clang 也能加载 `enable_cmask` selftest（作者未给具体 clang 版本清单）。

## 我可以参与的点

- **testing**：在较老 clang（无 `__BPF_FEATURE_ADDR_SPACE_CAST`）上复跑 `enable_cmask` selftest，确认加载不再失败。

## 参考链接

- lore thread: https://lore.kernel.org/all/20261109162623.674441-1-tj@kernel.org/

---
id: sched-20261110-016
date: '2026-11-10'
subject: "selftests/sched_ext: Fix enable_cmask load failure on older clangs"
subsystem: sched
type: fix
status: merged_tip
severity: low
thread_root_msgid: "<20261109162623.674441-1-tj@kernel.org>"
lore_url: "https://lore.kernel.org/all/20261109162623.674441-1-tj@kernel.org/"
authors: [Tejun Heo]
maintainers_involved: [Tejun Heo]
current_version: v1
patch_series:
  - version: v1
    msgid: "<20261109162623.674441-1-tj@kernel.org>"
    date: '2026-11-10'
    summary: "对 arena 地址显式 cast_kern(m)，让老 clang 也能加载"
    review_outcome: "Applied to sched_ext/for-7.5"
upstream_commit: null
fixes_commit: null
merged_branch: "sched_ext/for-7.5"
merge_assessment:
  likelihood: merged
  blocking_issues: []
  next_action: "随 sched_ext/for-7.5 进入下个 merge window"
contribution_opportunities:
  - kind: testing
    description: "在无 __BPF_FEATURE_ADDR_SPACE_CAST 的老 clang 上复跑 enable_cmask selftest"
generated_at: "2026-11-11T09:00:00+08:00"
source_email_count: 1
related_articles: [sched-20261109-013]
tags: [sched_ext]
---