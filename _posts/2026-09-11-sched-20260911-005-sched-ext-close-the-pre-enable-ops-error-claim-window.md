---
id: sched-20260911-005
subject: 'sched_ext: Close the pre-enable ops error claim window'
date: '2026-09-11'
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: <20260910084533.2420199-1-fangqiurong@kylinos.cn>
lore_url: https://lore.kernel.org/all/20260910084533.2420199-1-fangqiurong@kylinos.cn/
authors:
- Qiurong Fang
maintainers_involved:
- Tejun Heo
current_version: v2
patch_series:
- version: v1
  msgid: <20260910084533.2420199-1-fangqiurong@kylinos.cn>
  date: 2026-09-10
  summary: 关闭 sched_ext 使能路径的 pre-enable ops 错误认领窗口（补丁正文未入缓存，要点取自 Tejun 回帖）。
  review_outcome: Tejun Heo 09-11 05:40：删不可达错误路径 hunk，移动状态转换并保留分配失败重置。
- version: v2
  msgid: <20260911024256.125287-1-fangqiurong@kylinos.cn>
  date: 2026-09-11
  summary: 按 Tejun 意见调整（补丁正文未入缓存）。
  review_outcome: Tejun Heo 09-11 23:24：确认分配失败均先于 ops->priv 发布、无 disable 竞争，给出 WARN_ON_ONCE
    断言写法并要求更新被移动注释。
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: []
  next_action: 等 v3 按 Tejun 意见落实后收取（后续已合入 sched_ext/for-7.3-fixes，见 sched-20260913-003）
contribution_opportunities:
- kind: new_patch
  description: 回合 sched_ext 修复时核对该修复最终形态（v3 + wording cleanup）并评估同步
generated_at: '2026-09-14T11:35:00'
source_email_count: 2
related_articles:
- sched-20260913-003
tags:
- sched_ext
title: 'sched_ext: Close the pre-enable ops error claim window'
layout: article
---

## TL;DR
Qiurong Fang（kylinos）修复 sched_ext 使能路径上「ops 错误认领窗口」的系列，当日收到 Tejun Heo 对 v1、v2 的两轮具体评审：删不可达错误路径、给出分配失败回退处的断言写法。评审在两轮内收敛、无异议——按 09-11 当日时点已属待收取状态（后续走向见 sched-20260913-003：v3 已被 Tejun 应用到 sched_ext/for-7.3-fixes）。原始补丁邮件未入本日缓存，脉络依据 Tejun 回帖中的真实 In-Reply-To/References 重建。

## 背景与问题
补丁处理 sched_ext 使能（scx enable）路径中 ops->priv 发布与使能状态转换（SCX_ENABLING）的先后关系：在此顺序下，「使能完成之前 ops 错误被认领（claim）」的窗口是否存在，以及分配失败时应走本地回退还是完整 disable。Tejun 的回帖给出了所有权边界的权威结论：所有分配失败都发生在 ops->priv 发布之前，因此不可能有 disable 竞争。

## 技术方案
依据 Tejun 两轮回帖可确定的要点（补丁 diff 本身未入缓存）：

- 调整使能状态转换与 ops->priv 发布顺序，让 SCX_ENABLING 先于 ops->priv 发布，从而关闭 pre-enable ops error claim window；
- v1 回帖：删掉一处 hunk——「一旦 SCX_ENABLING 先于 ops->priv 发布，scx_tryset_enable_state() 在该处不可能失败」，该错误路径不可达；移动既有转换并保留分配失败时的重置；
- v2 回帖：分配失败回退处改用断言 `WARN_ON_ONCE(scx_set_enable_state(SCX_DISABLED) != SCX_ENABLING)`；同步更新被移动的注释；「分配失败仍本地回退（unwind locally），完整 disabling 只在 scx_alloc_and_add_sched() 成功之后才适用」。

## 版本演进与当前进展
*current_version: v2（截至 09-11 当日；v3 于 09-12 发出并合入，见 sched-20260913-003）*。

- v1（msgid `<20260910084533.2420199-1-fangqiurong@kylinos.cn>`，msgid 时间戳 09-10）：Tejun 09-11 05:40 回复，删不可达 hunk、移动状态转换、保留分配失败重置；
- v2（msgid `<20260911024256.125287-1-fangqiurong@kylinos.cn>`，msgid 时间戳 09-11）：Tejun 09-11 23:24 回复，确认无 disable 竞争并给出 WARN_ON_ONCE 断言写法，要求更新被移动的注释。

## Maintainer 意见与讨论焦点
- **Tejun Heo**：两轮都是具体、收敛、无保留的评审意见——v1 指出不可达路径，v2 直接给出断言实现并解释无竞争的原因；无分歧、无 NAK。
- 无其他参与者出现在本日线程邮件中。

## 合入评估
*likelihood=high*（按 09-11 当日时点）：维护者评审两轮收敛、给出的修改全部是收窄性的，无待决问题——属「评审无异议待收取」。*blocking_issues*：无（当日时点）；仅剩 v3 按 Tejun 意见落实后等待应用。后续事实（供补跑读者）：v3 于 09-12 发出，09-13 被 Tejun 以 minor wording cleanups 应用到 sched_ext/for-7.3-fixes，详见 sched-20260913-003。*next_action*：回合该修复的内部分支以最终合入形态为准。

## 效果评估
暂无效果数据：这是使能路径竞态窗口的修复，邮件中没有复现触发条件（如特定 CONFIG、负载）或失败日志的描述；原始报告动机未获取到。

## 我可以参与的点
- kind=new_patch：回合 sched_ext 修复时核对该修复的最终形态（v3 + Tejun 的 wording cleanup），评估是否同步到内部维护分支。

## 参考链接
- v1 补丁：https://lore.kernel.org/all/20260910084533.2420199-1-fangqiurong@kylinos.cn/
- v2 补丁：https://lore.kernel.org/all/20260911024256.125287-1-fangqiurong@kylinos.cn/
- Tejun 对 v1 的回复：https://lore.kernel.org/all/c3b851d927a8be1a0038cb208d33349b@kernel.org/
- Tejun 对 v2 的回复：https://lore.kernel.org/all/664afc289472acecc783762fdf7a9baa@kernel.org/
