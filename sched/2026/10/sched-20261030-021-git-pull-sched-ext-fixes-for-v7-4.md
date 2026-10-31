# [GIT PULL] sched_ext: Fixes for v7.4

## TL;DR
Tejun Heo 的 `sched_ext: Fixes for v7.4` GIT PULL（10-27 发出）已被 Linus 合并进 `torvalds/linux.git`，合并 commit 为 `729beb5aa80ce4bcf40f9ff74ed845269393a6ae`。这是 v7.4 窗口的 sched_ext 修复集（区别于此前已单独覆盖的「sched_ext: Changes for v7.4」新功能 pull），随 pr-tracker-bot 的合并通知到达。

## 背景与问题
v7.4 开发周期中，sched_ext 通过独立 pull 分别推送「新功能（Changes）」与「修复（Fixes）」。本次是 **Fixes** pull 的合并确认，标志着 sched_ext 在 v7.4 的修复已在 mainline 落地。合并通知未展开 pull 内容，仅给出合并 commit。

## 技术方案
本文为合并通知类条目，无补丁方案。合并 commit：`729beb5aa80ce4bcf40f9ff74ed845269393a6ae`（torvalds/linux.git）。当日同窗口内另有多条 `sched_ext/for-7.4-fixes` 分支的修复补丁（如 `Avoid unnecessary IMMED reenqueues on idle CPUs` 已被 Tejun 标注 Applied），具体哪些进入本次 pull 未在通知中列出。

## 版本演进与当前进展
*current_version: null*。pull 于 2026-10-27 发出，2026-10-30 合并进 mainline。

## Maintainer 意见与讨论焦点
Linus 已合并，无异议可述；pr-tracker-bot 仅做机械化确认。

## 合入评估
*likelihood=merged*。已合并进 `torvalds/linux.git`。*blocking_issues*：无。*next_action*：无（已合入）；后续 sched_ext 修复继续走独立 fixes pull。

## 效果评估
无性能数据；为合入状态条目。

## 我可以参与的点
当前阶段暂无明显参与空间（已合入）；可关注 v7.4 -rc 阶段的 sched_ext 回归验证。

## 参考链接
- 合并 commit: https://git.kernel.org/torvalds/c/729beb5aa80ce4bcf40f9ff74ed845269393a6ae
- pull 的原始 Message-ID 取自通知头，未在缓存正文中直接取得独立链接：未获取到。

---
id: sched-20261030-021
date: 2026-10-30
subject: "[GIT PULL] sched_ext: Fixes for v7.4"
subsystem: sched
type: fix
status: merged_tip
severity: none
thread_root_msgid: "<e5758e0a056fcef3e669b4d1f285a787@kernel.org>"
lore_url: "https://lore.kernel.org/all/e5758e0a056fcef3e669b4d1f285a787@kernel.org/"
authors: [Tejun Heo]
maintainers_involved: []
current_version: null
patch_series: []
upstream_commit: "729beb5aa80ce4bcf40f9ff74ed845269393a6ae"
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: merged
  blocking_issues: []
  next_action: "无（已合入 mainline），后续修复继续走独立 fixes pull"
contribution_opportunities: []
generated_at: "2026-10-31T09:00:00"
source_email_count: 1
related_articles: []
tags: [sched_ext]
---