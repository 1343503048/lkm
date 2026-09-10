---
id: sched-20260910-004
date: 2026-09-10
subject: 'sched/eevdf: Fix rb augmented with multi fields'
subsystem: sched
type: bug
status: merged_tip
severity: medium
thread_root_msgid: <20260908135526.2783039-1-vincent.guittot@linaro.org>
lore_url: https://lore.kernel.org/all/20260909150522.858312-1-vincent.guittot@linaro.org/
upstream_commit: 51b0e68cfa0ac69e3c3ea9d6753af7e15dfaab22
fixes_commit: aef6987d8954
merged_branch: tip/sched/urgent
current_version: v2
generated_at: '2026-09-11T10:10:00'
authors:
- Vincent Guittot
maintainers_involved:
- Peter Zijlstra
- K Prateek Nayak
patch_series:
- version: v1
  msgid: <20260908135526.2783039-1-vincent.guittot@linaro.org>
  date: '2026-09-08'
  summary: 把 RB_DECLARE_CALLBACKS 泛化为 MULTI 版本，fair.c 提供 min_vruntime_copy() 一次拷贝
    3 个增广字段。
  review_outcome: Prateek 评审提出修改（详见 sched-20260909-008）。
- version: v2
  msgid: <20260909150522.858312-1-vincent.guittot@linaro.org>
  date: '2026-09-09'
  summary: 按评审更新后重发。
  review_outcome: Prateek 给出 Reviewed-by + Tested-by；09-10 Peter 合入 tip/sched/urgent；Kayra
    Cizmeci 补充独立 Reviewed-by 并引发 min_vruntime_update() bool 参数冗余的两轮讨论，结论为该删但无干净删法、未阻塞合入。
merge_assessment:
  likelihood: merged
  blocking_issues: []
  next_action: 已合入 tip/sched/urgent，等待进入 -rc；可选后续是清理 RBCOMPUTE 双函数签名不一致
contribution_opportunities:
- kind: new_patch
  description: 清理 min_vruntime_update() 用不到的 bool 参数（RBCOMPUTE 两个函数签名不一致），Kayra 确认该删但无人认领
- kind: testing
  description: 在 aef6987d8954..51b0e68cfa0a 区间验证 cgroup 层级下 min_slice/max_slice 增广值异常的可观测影响，为
    stable 回合提供依据
source_email_count: 4
related_articles:
- sched-20260909-008
- sched-20260908-004
tags:
- eevdf
- cfs
title: 'sched/eevdf: Fix rb augmented with multi fields'
layout: article
---

## TL;DR
本文为增量更新，完整背景见 related_articles 中的 sched-20260909-008 / sched-20260908-004。Vincent Guittot 的修复已被 Peter Zijlstra 合入 tip/sched/urgent（commit 51b0e68cfa0a，09-10 10:22 +0200），EEVDF 运行树 3 个增广字段只拷贝 min_vruntime 的问题正式进入紧急修复通道；同日线程里 Kayra Cizmeci 补了一轮独立 review（给出 Reviewed-by），并与 Peter 就 min_vruntime_update() 的 bool 参数是否冗余交锋两轮，结论是「该删但没有干净的删法」，留作后续清理。

## 背景与问题
EEVDF 运行树增广了 3 个字段（min_vruntime/min_slice/max_slice），但 RB_DECLARE_CALLBACKS 模板只支持单个 RBAUGMENTED 字段，_copy 与 _rotate 回调只搬 min_vruntime，插入再平衡与删除变色路径会丢另外两个字段，导致父级增广值计算错误（影响基于 min_slice/max_slice 的 eligibility/最长 slice 判定）。Fixes: aef6987d8954 ("sched/eevdf: Propagate min_slice up the cgroup hierarchy")。

## 技术方案
把模板泛化为 RB_DECLARE_CALLBACKS_MULTI（RBAUGMENTED 参数换成 RBCOPY 拷贝函数，由调用方一次拷全部字段），fair.c 侧提供 min_vruntime_copy()。合入版本 diffstat：include/linux/rbtree_augmented.h +35 行区间改动、kernel/sched/fair.c +12，合计 38 insertions(+), 9 deletions(-)。rbtree_augmented.h 是公共头，但 MULTI 是新增宏，不改动既有 RB_DECLARE_CALLBACKS 用户。

## 版本演进与当前进展
- v1（09-08，msgid `<20260908135526.2783039-1-vincent.guittot@linaro.org>`）：首发，Prateek 评审。
- v2（09-09，msgid `<20260909150522.858312-1-vincent.guittot@linaro.org>`）：按评审更新后重发，Prateek 给出 Reviewed-by + Tested-by。
- 09-10：Peter 合入 tip/sched/urgent（Commit-ID 51b0e68cfa0ac69e3c3ea9d6753af7e15dfaab22，CommitterDate 09-10 10:22:52 +0200）。同日 Kayra Cizmeci 在线程里补充独立 review。

## Maintainer 意见与讨论焦点
- K Prateek Nayak：Reviewed-by + Tested-by（已随合入 commit 记录）。
- Kayra Cizmeci（09-10，非维护者、独立 reviewer）：确认问题本质（"we need to copy 3 things and we copy 1 thing currently"）；nit：commit message 里 'datas' 英语不正确；质疑 min_vruntime_update() 的 bool 参数 grep 不到使用点、建议删除；给出 "Reviewed-by: Kayra Cizmeci"（注明 Include if you want to）；自述没做 boot test，认为加了也不增信息。
- Peter Zijlstra 回应 Kayra："grep for RBCOMPUTE, you'll find it used in RBNAME ## _propagate()."
- Kayra 收尾澄清：他知道参数在 _propagate 里被用，但 min_vruntime_update() 本身用不到它；参数存在是因为 RBCOMPUTE 对应两个不同函数、其一使用参数而另一个不用——"So it's better if we remove it, but there is no clean way that I can see using to remove it."。该清理无人认领，补丁已按原样合入。

## 合入评估
已合入：tip/sched/urgent，commit 51b0e68cfa0ac69e3c3ea9d6753af7e15dfaab22（likelihood: merged）。走 urgent 分支意味着会较快进入 -rc 修复流。遗留的 min_vruntime_update() bool 参数清理属可选后续，不影响本修复。

## 效果评估
合入邮件未附 benchmark。验证信息为 Prateek 的 Tested-by（具体测试内容邮件未展开，未获取到）。修复正确性可由增广字段拷贝语义静态确认。

## 我可以参与的点
- 做 RBCOMPUTE 双函数签名不一致的清理：把 min_vruntime_update() 用不到的 bool 参数去掉或拆分两个回调签名——Kayra 确认「该删但没有干净删法」且无人认领（new_patch）。
- 在自家内核验证 aef6987d8954 之后、51b0e68cfa0a 之前的区间是否存在 min_slice/max_slice 相关的可观测异常（如 cgroup 层级下 eligibility 判定偏差），为 stable 回合提供依据（testing）。

## 参考链接
- lore thread（v2 补丁）: https://lore.kernel.org/all/20260909150522.858312-1-vincent.guittot@linaro.org/
- tip-bot 合入通知: https://lore.kernel.org/all/178903092601.623050.18196425077971155305.tip-bot2@tip-bot2/
- gitweb: https://git.kernel.org/tip/51b0e68cfa0ac69e3c3ea9d6753af7e15dfaab22
- Kayra review: https://lore.kernel.org/all/20260909185828.1158142-1-kayracizmeci@gmail.com/
- Peter 回应: https://lore.kernel.org/all/20260909215850.GP776954@noisy.programming.kicks-ass.net/
- Kayra 收尾澄清: https://lore.kernel.org/all/20260910055937.1205721-1-kayracizmeci@gmail.com/
