# sched_ext: Fix idle CPU state initialization and validation

# sched_ext: 7.2-rc6 fixes pull（第二波）

## TL;DR
Tejun 在 08-04 发出 sched_ext 的 7.2-rc6 fixes pull 第二波，延续 08-03-003 的稳定性修复集合（UAF / kernfs 死锁 / sync wakeup 误标 busy）。状态 merged_tip，等待 7.2-rc6 进入主线。这是 08-03-003 的延续。

## 背景与问题
7.2-rc6 周期 sched_ext 累积的子调度器（sub-scheduler）生命周期稳定性修复：enable 失败撕裂未链接子调度器的 UAF、非 ext class 任务收到 enable 回调、policy 拒绝路径静默改写运行中任务策略、enable/disable 与 cgroup 移除/权重写经 kernfs 死锁、sync wakeup 误标 waker CPU 为 idle。详见 08-03-003。

## 技术方案
按子系统分别修复，08-04 的 pull 在 08-03-003 基础上补充/收尾同类修复并重新提交 tag。

## 版本演进与当前进展
- 08-03：首批 fixes pull（08-03-003）。
- 08-04：第二波 fixes pull，同 tag `sched_ext-for-7.2-rc6-fixes`。

## Maintainer 意见与讨论焦点
作为 maintainer 自身 fixes 汇总，无 NAK。

## 合入评估
已 **merged**（fixes tag，等待 7.2-rc6 进入主线）。

## 效果评估
稳定性修复集合，邮件未给基准；以「消除崩溃/死锁」衡量。

## 我可以参与的点
可关注 7.2-rc6 后续回归报告。

## 参考链接
- 08-03 文章：sched-20260803-003-sched-ext-fixes-for-v7.2-rc6

---
subject: "sched_ext: Fix idle CPU state initialization and validation"
id: sched-20260804-004
date: 2026-08-04
subsystem: sched
type: fix
status: merged_tip
severity: high
thread_root_msgid: "<unknown>"
lore_url: "unknown"
authors: [Tejun Heo]
maintainers_involved: [Tejun Heo]
current_version: v1
patch_series:
  - version: v1
    msgid: "<unknown>"
    date: 2026-08-04
    summary: "GIT PULL sched_ext-for-7.2-rc6-fixes（第二波）：延续 08-03-003 的 fixes 汇总，包含子调度器生命周期 UAF、enable/disable 与 cgroup 经 kernfs 死锁、sync wakeup 误标 waker busy 等。"
    review_outcome: "作为 fixes pull 发出，等待 tip 侧接收（08-03-003 已覆盖首批）。"
upstream_commit: null
fixes_commit: null
merged_branch: "sched_ext/for-7.2-rc6-fixes"
merge_assessment:
  likelihood: merged
  blocking_issues: []
  next_action: "等待 Linus 在 7.2-rc6 周期合入。"
contribution_opportunities: []
generated_at: "2026-08-05T00:25:00"
source_email_count: 1
related_articles: ["sched-20260803-003-sched-ext-fixes-for-v7.2-rc6"]
tags: [sched_ext, cgroup, idle]
---
