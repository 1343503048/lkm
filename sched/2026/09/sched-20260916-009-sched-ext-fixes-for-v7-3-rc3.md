# sched_ext: Fixes for v7.3-rc3

## TL;DR
Tejun Heo 发出的 sched_ext v7.3-rc3 修复 GIT PULL（10 枚 fix），已被 Linus 合入 mainline（merge commit `9b87fdc9af2fbfcdb5c24a64139685ef80f6573f`）。覆盖 pre-enable 错误声明窗口、compat kfunc 空指针解引用、sub-scheduler keep-running 决策、在线 cid mask、cgroup idle 状态传递等多个问题。

## 背景与问题
这是 sched_ext 子系统面向 v7.3-rc3 的例行修复窗口 pull。包含的修复此前大多已单独出现在日报中（pre-enable 窗口、NULL sched deref、在线 cid mask、cgroup idle 等），这里以一次 pull 的形式统一送入 Linus。

## 技术方案
本 pull 覆盖 10 枚补丁，作者分布：Tao Cui（2）、Tejun Heo（7）、Wanwu Li（1）、fangqiurong（1）。主要修复项：BPF 程序在调度器 enable 完成前抛错被 disable 路径的 pre-enable 捷径吞掉导致调度器无法停用后被 use-after-free；两个 compat kfunc 对已退出/idle 任务解引用 NULL 调度器 oops；dispatch 路径对 sub-scheduler 任务误用 root 调度器 flags 造成告警与 stall；为自带 CPU ID 映射的调度器新增内核维护的 online mask；cgroup idle 初始状态未在 cgroup init 传递及同值重写触发多余回调；scx_qmap 示例调度器的多项修复。

## 版本演进与当前进展
- 本日（105215，`<77a248741e07bbe690582f3c31442b7f@kernel.org>`）发出 pull，pr-tracker-bot 确认已合入 torvalds/linux.git。

## Maintainer 意见与讨论焦点
- **Tejun Heo**：作为 sched_ext 维护者组织并发出本次修复 pull。
- **Linus/pr-tracker-bot**：已合入，无异议。

## 合入评估
*likelihood=merged*，*status=merged_tip*。已进 mainline（merge commit `9b87fdc9af2fbfcdb5c24a64139685ef80f6573f`）。*blocking_issues*：无。*next_action*：相关带 stable 标签的修复后续回合 stable。

## 效果评估
无性能量化数据；属正确性/稳定性修复集合。

## 我可以参与的点
当前阶段已合入，暂无明显参与空间。可关注其中带 `Cc: stable` 的修复在 stable 分支的回合进展。

## 参考链接
- GIT PULL：https://lore.kernel.org/all/77a248741e07bbe690582f3c31442b7f@kernel.org/
- 合入确认：https://lore.kernel.org/all/178949987149.2238025.2488857518081041204.pr-tracker-bot@kernel.org/

---
id: sched-20260916-009
date: '2026-09-16'
subject: 'sched_ext: Fixes for v7.3-rc3'
subsystem: sched
type: fix
status: merged_tip
severity: none
thread_root_msgid: '<77a248741e07bbe690582f3c31442b7f@kernel.org>'
lore_url: 'https://lore.kernel.org/all/77a248741e07bbe690582f3c31442b7f@kernel.org/'
authors:
  - 'Tejun Heo'
maintainers_involved:
  - 'Tejun Heo'
current_version: null
patch_series: []
upstream_commit: '9b87fdc9af2fbfcdb5c24a64139685ef80f6573f'
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: merged
  blocking_issues: []
  next_action: '带 stable 标签的修复后续回合 stable'
contribution_opportunities: []
generated_at: '2026-09-17T09:00:00'
source_email_count: 2
related_articles: []
tags:
  - sched_ext
---