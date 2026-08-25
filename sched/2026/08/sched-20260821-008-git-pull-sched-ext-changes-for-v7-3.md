# sched_ext v7.3 的变更已被合入 torvalds/linux.git

## TL;DR

sched_ext v7.3 的变更已被合入 torvalds/linux.git。Tejun Heo 的 pull request 于 8 月 17 日发出，8 月 21 日确认合入主线。

## 背景与问题

sched_ext 是 BPF 可编程调度器框架，允许通过 BPF 程序实现自定义调度策略。v7.3 版本包含一系列改进和修复。

## 技术方案

Pull request 包含 sched_ext 框架的增量改进。具体内容需参考 pull request 邮件。

## 版本演进与当前进展

- Pull request 于 2026-08-17 发出
- 2026-08-21 pr-tracker-bot 确认已合入 torvalds/linux.git
- 合入 commit: `11260c335ec6071af5543aef73000b28f041c124`

## Maintainer 意见与讨论焦点

已合入主线，无争议。

## 合入评估

- **likelihood**: merged
- 已合入 torvalds/linux.git

## 效果评估

暂无具体变更列表的性能数据。

## 我可以参与的点

- 关注 sched_ext v7.3 的新 API/功能，为自己的 BPF 调度器开发做准备
- 在新版本基础上测试现有 SCX 调度器的兼容性

## 参考链接

- torvalds/linux commit: https://git.kernel.org/torvalds/c/11260c335ec6071af5543aef73000b28f041c124
- lore thread: 未获取到
- stable backport: 未获取到

---
id: sched-20260821-008
date: 2026-08-21
subsystem: sched
type: feature
status: merged_tip
severity: none
thread_root_msgid: "未获取到"
lore_url: "未获取到"
authors: ["Tejun Heo"]
maintainers_involved: []
current_version: v1
patch_series:
  - version: v1
    msgid: "未获取到"
    date: 2026-08-17
    summary: "sched_ext v7.3 变更合入主线"
    review_outcome: "已合入 torvalds/linux"
upstream_commit: "11260c335ec6071af5543aef73000b28f041c124"
fixes_commit: null
merged_branch: "torvalds/linux"
merge_assessment:
  likelihood: merged
  blocking_issues: []
  next_action: "已合入"
contribution_opportunities: []
generated_at: "2026-08-21T10:00:00"
source_email_count: 1
related_articles: []
tags: ["sched_ext"]
---
