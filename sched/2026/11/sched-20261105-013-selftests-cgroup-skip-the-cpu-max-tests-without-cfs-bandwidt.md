# selftests: cgroup: skip the cpu.max tests without CFS bandwidth control

## TL;DR

Sasha Levin 修 cgroup 自测：`cpu.max` 只有在内核开了 `CONFIG_CFS_BANDWIDTH` 时才存在（arm64 defconfig 未开），导致 `test_cpucg_max` 与 `test_cpucg_max_nested` 在 arm64 上写 `cpu.max` 失败而报错。补丁让两项测试在 `cpu.max` 不存在时跳过，并把 `CONFIG_CFS_BANDWIDTH` 加进 cgroup 自测 config。已在 144 核 Grace arm64 上验证，属低风险测试修复，合入概率高。

## 背景与问题

CGroup v2 的 `cpu.max` control 文件只在 `CONFIG_CFS_BANDWIDTH=y` 时创建。arm64 的 defconfig 未启用该选项，于是 `test_cpucg_max`、`test_cpucg_max_nested` 写 `cpu.max` 失败并被判定为测试失败（false negative）。这污染了在 arm64 上跑 cgroup kselftest 的结果。

## 技术方案

在两项测试里先探测 `cpu.max` 是否存在（`cgroup_util` 检查），不存在则跳过并标记 skip（非失败）；同时在 `tools/testing/selftests/cgroup/config` 里加 `CONFIG_CFS_BANDWIDTH`，让有条件的构建能真正跑到这两项测试。改动仅 2 文件、9 行插入 2 行删除。

## 版本演进与当前进展

*current_version: v1（2026-11-05）*。刚发出，暂无回复。

## Maintainer 意见与讨论焦点

暂无回复。补丁为自测修复，作者为 stable 维护者 Sasha Levin，`Fixes:` 指向引入两项测试的 commit（889ab8113ef1、a79906570f96）。

## 合入评估

*likelihood=high*。低风险、自包含的测试跳过修复，作者身份与 Fixes 标签齐备，无设计争议。*blocking_issues*：暂无。*next_action*：等 selftests/cgroup 维护者收取。

## 效果评估

作者在 144 核 Grace（arm64，KernelCI arm64 defconfig 构建 05441d697f7f9，`CONFIG_CFS_BANDWIDTH` 未开）上验证：两项测试现均跳过而非失败。

## 我可以参与的点

- testing：在 `CONFIG_CFS_BANDWIDTH=n` 的 x86 定制内核上确认跳过逻辑同样生效（当前只在 arm64 验证过）。
- 当前阶段暂无其它明显参与点。

## 参考链接

- lore thread（补丁）: https://lore.kernel.org/all/20261105011827.1143972-1-sashal@kernel.org/

---
id: sched-20261105-013
date: 2026-11-05
subject: "selftests: cgroup: skip the cpu.max tests without CFS bandwidth control"
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: "<20261105011827.1143972-1-sashal@kernel.org>"
lore_url: "https://lore.kernel.org/all/20261105011827.1143972-1-sashal@kernel.org/"
authors: [Sasha Levin]
maintainers_involved: []
current_version: v1
patch_series:
  - version: v1
    msgid: "<20261105011827.1143972-1-sashal@kernel.org>"
    date: 2026-11-05
    summary: "cpu.max 两项测试在无 CONFIG_CFS_BANDWIDTH 时跳过并补 config。"
    review_outcome: "刚发出，暂无 review。"
upstream_commit: null
fixes_commit: "889ab8113ef1"
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: []
  next_action: "等 selftests/cgroup 维护者收取"
contribution_opportunities:
  - kind: testing
    description: "在 CONFIG_CFS_BANDWIDTH=n 的 x86 内核确认跳过逻辑生效"
generated_at: "2026-11-06T09:00:00+08:00"
source_email_count: 1
related_articles: []
tags: [cgroup]
---