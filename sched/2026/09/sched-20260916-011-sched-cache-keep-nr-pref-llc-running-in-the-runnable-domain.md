# sched/cache: Keep nr_pref_llc_running in the runnable domain

## TL;DR
Tim Chen 的 cache-aware 系列 patch 1/4（本日为 Peter Zijlstra 评审轮）：让 `nr_pref_llc_running` 只统计 runnable 域内的任务。Peter 只提了一条实质意见——**需要补 `Fixes:` 标签**（便于回溯），并提醒要注明「以后 flat-pick 演进时要再把这个条件拿掉」。Kayra Cizmeci 当场定位出引入 commit。合入可能性中等。

## 背景与问题
`nr_pref_llc_running` 用于 cache-aware 调度里判断某个 preferred LLC 上还有多少任务在运行。当前（或此前某版）它被放进了一个「只在 runnable 域」才成立的条件里，而 Peter 指出这与 flat-pick 引入的 delayed task 语义有耦合：现在只有 flat pick 场景下任务会被 delayed，而这个计数条件需要保持在 runnable 域。cache-aware 相关代码上一个周期才合入主线，因此这个修复若要回溯（backport），必须带上正确的 `Fixes:` 标签。

## 技术方案
保持 `nr_pref_llc_running` 的统计在 runnable 域内（patch 本体的具体代码改动不在今日邮件正文，仅在评审回复中讨论）。Peter 要求补 `Fixes:` 并在注释里标注未来随 flat-pick/delayed 演进需要移除该条件的 TODO。

## 版本演进与当前进展
- 本日为 Peter 对 4-patch 系列 patch 1/4 的评审（107161）。Kayra（107335）直接给出 `Fixes: 714059f79ff0 ("sched/cache: Handle moving single tasks to/from their preferred LLC")`，即引入 `env->src_rq->nr_pref_llc_running == env->src_rq->cfs.h_nr_runnable` 条件的 commit，免去作者重新检索。

## Maintainer 意见与讨论焦点
- **Peter Zijlstra**：要求补 `Fixes:` 标签；指出因 cache-aware 上一个周期才合入，回溯时需要保留该条件，但之后应注明「之后把这个条件拿掉」。
- **Kayra Cizmeci**：帮忙定位并给出精确的 `Fixes:` commit。
- 无 NAK。

## 合入评估
*likelihood=medium*。方向明确、Peter 已参与且只提可执行的补标签意见，但尚未有最终 Ack，系列还涉及 3/4、4/4 的评审（见 sched-20260916-012 / 013）。*blocking_issues*：缺 `Fixes:` 标签。*next_action*：作者补 `Fixes: 714059f79ff0` 并加后续移除 TODO 后重发。

## 效果评估
本日评审未涉及性能数据，属记账正确性修复讨论。

## 我可以参与的点
- kind=review：核对 `nr_pref_llc_running` 在 delayed/flat-pick 路径下的增删是否闭合，确认 runnable 域条件未来可安全移除。
- kind=discussion：评估该条件与「flat pick 只 delay 单个任务」的耦合，提前规划后续移除方案。

## 参考链接
- Peter 评审：https://lore.kernel.org/all/20260916123046.GE776954@noisy.programming.kicks-ass.net/
- Kayra 提供的 Fixes commit：https://lore.kernel.org/all/20260916133328.3422-1-kayracizmeci@gmail.com/

---
id: sched-20260916-011
date: '2026-09-16'
subject: 'sched/cache: Keep nr_pref_llc_running in the runnable domain'
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: '<82736e1329bf8ed195bbbc4990486c87094e6789.1789061845.git.tim.c.chen@linux.intel.com>'
lore_url: 'https://lore.kernel.org/all/82736e1329bf8ed195bbbc4990486c87094e6789.1789061845.git.tim.c.chen@linux.intel.com/'
authors:
  - 'Tim Chen'
maintainers_involved:
  - 'Peter Zijlstra'
current_version: null
patch_series:
  - version: v1
    msgid: '<82736e1329bf8ed195bbbc4990486c87094e6789.1789061845.git.tim.c.chen@linux.intel.com>'
    date: '2026-09-15'
    summary: '将 nr_pref_llc_running 统计保持在 runnable 域'
    review_outcome: 'Peter 要求补 Fixes 标签并加后续移除 TODO'
upstream_commit: null
fixes_commit: '714059f79ff0'
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
    - '缺 Fixes 标签（Peter 要求）'
  next_action: '作者补 Fixes: 714059f79ff0 与后续移除 TODO 后重发'
contribution_opportunities:
  - kind: review
    description: '核对 nr_pref_llc_running 在 delayed/flat-pick 路径的增删闭合性'
  - kind: discussion
    description: '评估该条件与 flat pick 的耦合，规划后续移除方案'
generated_at: '2026-09-17T09:00:00'
source_email_count: 2
related_articles:
  - sched-20260915-005
tags:
  - cfs
---