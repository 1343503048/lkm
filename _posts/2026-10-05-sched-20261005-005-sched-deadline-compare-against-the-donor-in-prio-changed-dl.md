---
id: sched-20261005-005
date: '2026-10-05'
subject: 'sched/deadline: Compare against the donor in prio_changed_dl()'
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: <20261005120350.2026799-1-zhanxusheng@xiaomi.com>
lore_url: https://lore.kernel.org/all/20261005120350.2026799-1-zhanxusheng@xiaomi.com/
authors:
- Zhan Xusheng
maintainers_involved: []
current_version: v2
patch_series:
- version: v1
  msgid: <20260924121213.106673-1-zhanxusheng@xiaomi.com>
  date: '2026-09-24'
  summary: prio_changed_dl 抢占判定从 rq->curr 改为 rq->donor
  review_outcome: 无 review
- version: v2
  msgid: <20261005120350.2026799-1-zhanxusheng@xiaomi.com>
  date: '2026-10-05'
  summary: 撤回蕴含论证（承认双向行为影响）；撤回 dl_server 两处顺带转换（避开与 Andriaccio RFC v6 冲突）
  review_outcome: 发布当日无 review
related_articles:
- sched-20260924-002
upstream_commit: null
fixes_commit: af0c8b2bf67b
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues: 无维护者 review；proxy execution 栈 churn 中 donor/curr 语义未定
  next_action: 等 Juri/Peter review；Andriaccio 系列合入后发 dl_server follow-up
generated_at: '2026-10-06T01:00:00'
tags:
- deadline
- proxy_execution
title: 'sched/deadline: Compare against the donor in prio_changed_dl()'
layout: article
---

> **subject**：`sched/deadline: Compare against the donor in prio_changed_dl()`

## TL;DR

本文为增量更新，完整脉络见 related_articles。

- <a class="article-ref" href="/lkm/2026/09/24/sched-20260924-002-sched-deadline-compare-against-the-donor-in-prio-changed-dl.html">sched-20260924-002</a>：Zhan Xusheng 的一致性修复 v1——`prio_changed_dl()` 的 else 分支询问「p 是否应抢占当前调度上下文」，proxy execution 下该上下文是 `rq->donor`，但代码仍与 `rq->curr` 比较；补丁改为与 `rq->donor` 比较，与同 commit 已修好的 `prio_changed_rt()` 对齐；`CONFIG_SCHED_PROXY_EXEC=n` 下 `build_policy.o` 字节级一致。
- <a class="article-ref" href="/lkm/2026/10/05/sched-20261005-005-sched-deadline-compare-against-the-donor-in-prio-changed-dl.html">sched-20261005-005</a>（今天）：**v2 重发**，两处实质性自我修正——(1) 撤回 v1「donor 测试蕴含 curr 测试」的论证：构造「非 DL donor + DL rq->curr」时 donor 测试为真而 curr 测试可假，所以现行代码**既可能多加 reschedule，也可能漏掉该有的 reschedule**，不只是冗余问题；(2) 撤回把 `dl_server_timer()`/`dl_server_start()` 一并转换的建议——Yuri Andriaccio 的「sched/deadline: Do not access dl_se->rq directly」（RFC v6 03/25）正在重写那两行（`dl_se->rq` 转局部 `rq` 但保持 `->curr`），donor 转换应在其之上做而非对抗它。base-commit 更新为 `a90ee4305c4a`；`=n` 下字节级一致验证照做。

## 背景与问题

（承接 <a class="article-ref" href="/lkm/2026/09/24/sched-20260924-002-sched-deadline-compare-against-the-donor-in-prio-changed-dl.html">sched-20260924-002</a>）commit `af0c8b2bf67b`（"sched: Split scheduler and execution contexts"）把调度上下文（`rq->donor`）与执行上下文（`rq->curr`）拆分后，`prio_changed_dl()` 只在 dispatch 条件处改用 `task_current_donor()`，else 分支的抢占判定仍比较 `rq->curr`——proxy execution 下 `rq->curr` 可能是「借用 donor 参数运行的 mutex owner」，比较对象用错。同一 commit 已把 `prio_changed_rt()` 对应分支改成 `rq->donor`，deadline.c 被遗漏。v1 曾论证「donor 测试蕴含 curr 测试、改动纯冗余清理」；v2 自我推翻：该蕴含不成立（非 DL donor + DL curr 时两测试结果相反），所以这是**双向行为偏差**——现行代码可能在该 reschedule 时跳过 reschedule。

## 技术方案

（承接）把 else 分支判定从 `!dl_task(rq->curr) || dl_time_before(p->dl.deadline, rq->curr->dl.deadline)` 改为与 `rq->donor` 比较（2 行，kernel/sched/deadline.c）。

v2 的两处修正：

- **语义修正**：v1 的 commit 论据「donor 是最早 deadline 实体、donor 测试蕴含 curr 测试」被作者撤回——反例：非 DL donor + DL rq->curr 时，donor 测试（`!dl_task(rq->donor)`）为真、curr 测试（`!dl_task(rq->curr)`）为假，两者判定相反。因此补丁不只「去掉多余 reschedule」，也可能「补上被漏掉的 reschedule」——修复性质比 v1 论证的重。
- **范围收缩**：不再顺带转换 `dl_server_timer()`/`dl_server_start()` 两处同类比较——Yuri Andriaccio「sched/deadline: Do not access dl_se->rq directly」（RFC v6 03/25）正把那两行的 `dl_se->rq` 重写为局部 `rq` 而保持 `->curr`，donor 转换应在该系列之上叠加而非与之冲突；`prio_changed_dl()` 不在其触碰范围，故本补丁先行。

验证：`CONFIG_SCHED_PROXY_EXEC=y`/`=n` 均构建；`=n` 时两 rq 成员为匿名 union，`kernel/sched/build_policy.o` 与未打补丁树字节级一致。

## 版本演进与当前进展

- v1（09-24，`<20260924121213.106673-1-zhanxusheng@xiaomi.com>`，base `a9b3c7570564`）：首投，无 review（<a class="article-ref" href="/lkm/2026/09/24/sched-20260924-002-sched-deadline-compare-against-the-donor-in-prio-changed-dl.html">sched-20260924-002</a>）。
- v2（10-05，`<20261005120350.2026799-1-zhanxusheng@xiaomi.com>`，base `a90ee4305c4a`）：撤回蕴含论证（承认双向行为影响）、撤回 dl_server 两处顺带转换（避开与 Yuri Andriaccio RFC v6 的冲突）。暂无 review 回复。

## Maintainer 意见与讨论焦点

- **Zhan Xusheng**（作者）：v2 的两处自我修正质量高——主动暴露 v1 论证错误（诚实标注「It does not」），并给出与并行系列（Yuri Andriaccio RFC v6）的正确叠加策略。
- 无维护者回帖（v1 至今 11 天无人 review）；`af0c8b2bf67b` 的作者圈（proxy execution 相关）未介入。
- 焦点：v2 后该补丁的行为影响论证已完整（双向），剩「先只改 prio_changed_dl、dl_server 两处等 Andriaccio 系列」的切分是否被接受。

## 合入评估

*likelihood=medium*。改动极小（2 行）、方向与 `prio_changed_rt()` 既有先例一致、v2 论证完整且避开并行系列冲突；不利是 proxy execution 栈仍在高 churn，维护者注意力稀缺，v1 已搁 11 天。*blocking_issues*：无维护者 review；SCHED_PROXY_EXEC 仍依赖 `!SCHED_CLASS_EXT` 的上游语境下，donor/curr 语义是否稳定待 proxy 系列收敛。*next_action*：等 proxy-execution/deadline 侧维护者（Juri/Peter）过目；若 Andriaccio 系列先合入，dl_server 两处的 follow-up 补丁可立即提。

## 效果评估

无性能数据。v2 提供的是正确性论证升级：反例构造（非 DL donor + DL curr）证明现行代码存在「漏 reschedule」方向的真实偏差，v1 的「无行为变化」说法被作者自己纠正。构建验证：`=n` 下 `build_policy.o` 字节级一致。

## 我可以参与的点

- `review`：构造 v2 反例的实际运行验证——非 DL donor（如被 proxy 的 fair mutex owner）+ DL curr 场景下打/不打补丁的 reschedule 行为差异，把论证升级为可复现观测。
- `new_patch`：v2 落地后按作者预留的叠加路径，在 Yuri Andriaccio「Do not access dl_se->rq directly」系列之上发 `dl_server_timer()`/`dl_server_start()` 的 donor 转换 follow-up。

## 参考链接

- v2 补丁: https://lore.kernel.org/all/20261005120350.2026799-1-zhanxusheng@xiaomi.com/
- v1 补丁（09-24）: https://lore.kernel.org/all/20260924121213.106673-1-zhanxusheng@xiaomi.com/
