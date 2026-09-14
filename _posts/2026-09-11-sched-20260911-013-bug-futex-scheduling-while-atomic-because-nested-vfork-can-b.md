---
id: sched-20260911-013
subject: '[BUG] futex: scheduling-while-atomic because nested vfork can break guard(private_hash)'
date: '2026-09-11'
subsystem: sched
type: bug
status: under_review
severity: medium
thread_root_msgid: <CAG48ez26PrUOb8er9TP1gWLsqVLU8TEDr+1Zs25fgH0++=zhUQ@mail.gmail.com>
lore_url: https://lore.kernel.org/all/CAG48ez26PrUOb8er9TP1gWLsqVLU8TEDr+1Zs25fgH0++=zhUQ@mail.gmail.com/
authors:
- Peter Zijlstra
maintainers_involved:
- Peter Zijlstra
- Thomas Gleixner
current_version: v1
patch_series:
- version: 内联修正提案
  msgid: <20260911090447.GT788244@noisy.programming.kicks-ass.net>
  date: 2026-09-11
  summary: need_futex_hash_allocate_default() 不再排除 CLONE_VFORK（kernel/fork.c 2 行），任何
    CLONE_VM 克隆都分配默认私有 hash；确认治愈 nested vfork 测试用例。
  review_outcome: tglx 把「当初为何排除 vfork」转问 bigeasy；正式补丁未投递；vfork+exec 新增分配的性能权衡待确认。
upstream_commit: null
fixes_commit: ee9dce44362b
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
  - 等待 Sebastian (bigeasy) 答复排除 vfork 的历史原因与性能权衡
  - 修正尚未转正为带 Fixes 的正式补丁
  next_action: '内联 diff 转正为补丁（Fixes: ee9dce44362b），Sebastian 确认后收进入口树'
contribution_opportunities:
- kind: testing
  description: 高频 vfork+exec 负载上量化私有 hash 分配新增开销，供 Sebastian 确认权衡
- kind: review
  description: 分析 nested vfork 打破前提的完整路径，确认修正覆盖全部克隆形态
generated_at: '2026-09-14T11:35:00'
source_email_count: 5
related_articles: []
tags:
- regression
title: '[BUG] futex: scheduling-while-atomic because nested vfork can break guard(private_hash)'
layout: article
---

## TL;DR
Jann Horn 报告的 futex bug（原始报告 09-10 深夜入箱）当日获得快速定性与修复：nested vfork 可以使私有 futex hash 从未分配的进程进入本应持有 guard 的路径，触发 scheduling-while-atomic；Peter Zijlstra 定位到 need_futex_hash_allocate_default() 对 vfork 的排除（commit ee9dce44362b 引入）并贴出确认能治愈测试用例的 2 行修正，Thomas Gleixner 把「当初为何排除 vfork」的问题抛给 Sebastian Andrzej Siewior。

## 背景与问题
单线程进程本不该有私有 futex waiter，私有 hash 在克隆出第二个线程时才分配；need_futex_hash_allocate_default() 显式排除了 vfork（`(clone_flags & (CLONE_VM | CLONE_VFORK)) == CLONE_VM`），即 vfork 的子进程不分配私有 hash。Jann Horn 构造的 nested vfork 场景可以打破这一前提：进入本应被 guard(private_hash) 保护的路径时 hash 未就绪，随后在原子上下文里发生调度（scheduling-while-atomic）。引入该排除的 commit ee9dce44362b（"futex: Drop CLONE_THREAD requirement for private default hash alloc"）的提交说明称「排除 vfork 让既有路径保持不变（无开销），且不可能竞争」——Jann 指出这实际上只是给 vfork+exec 的单线程进程做的性能优化。

## 技术方案
Peter Zijlstra 的修正（内核/fork.c，2 行）：把 need_futex_hash_allocate_default() 的条件从 `(clone_flags & (CLONE_VM | CLONE_VFORK)) == CLONE_VM` 改为 `clone_flags & CLONE_VM`——不再排除 vfork，任何共享父 mm 的克隆都分配默认私有 hash。PeterZ 确认该改动「does in fact cure your testcase」。代价是 vfork+exec 进程也会分配私有 hash（正是当初被优化掉的路径），这层权衡待 tglx/Sebastian 确认。该修正以线程内联 diff 形式出现，尚未作为正式 PATCH 投递。

## 版本演进与当前进展
current_version: 无版本化补丁（bug 报告 + 内联修正提案）。原始报告未入当日缓存（msgid `<CAG48ez26PrUOb8er9TP1gWLsqVLU8TEDr+1Zs25fgH0++=zhUQ@mail.gmail.com>`，据前一日缓存为 Jann Horn 于 09-10 23:27 发出）；当日 5 封均为跟进：

- 09-11 16:36 PeterZ：确认该状态转换本不该可能，指出 vfork 排除可疑，「需要更多思考是否带来其他问题」；（同时抱怨报告邮件在 text/plain 里带 markdown 标签）
- 09-11 17:04 PeterZ：贴出修正 diff 并确认治愈测试用例，向 tglx 汇报 ee9dce44362b 排除 vfork 的动机（性能 + 认为不可能有影响）已被证伪；
- 09-11 19:51 tglx：CC +bigeasy，「我不记得当初为什么排除 VFORK。Sebastian？」；
- 09-11 23:28/23:31 Jann Horn：补充 ee9dce44362b 提交说明的引文与动机分析（纯性能优化）；另一封为邮件排版讨论。

## Maintainer 意见与讨论焦点
- **Peter Zijlstra**：主导定位与修复，对「排除 vfork」的原始动机持否定态度（"thinking this would/could not matter, which you've proven to be clearly false"）；
- **Thomas Gleixner**：不记得排除 VFORK 的原因，把问题转给当年相关工作的 Sebastian Andrzej Siewior（bigeasy）——修复的最终确认卡在这个历史问题上；
- **Jann Horn**：提供引入 commit 的动机分析（单线程 vfork+exec 的性能优化）；
- 分歧/未闭合：移除 vfork 排除会让 vfork+exec 多一次私有 hash 分配，性能回退是否可接受尚无人评估；修正尚未成为正式补丁。

## 合入评估
likelihood=medium：修复由子树维护者亲自提出并验证有效，技术路线无争议；但需要 Sebastian/tglx 确认移除排除无其他副作用（PeterZ 自己也说「need more thinking」），且尚未转正为带 Fixes 标签的补丁。blocking_issues：等待 bigeasy 对「当初为何排除 vfork」的答复；正式补丁（带 Fixes: ee9dce44362b）未投递。next_action：PeterZ（或报告者）把内联 diff 转正为补丁，附 Fixes 与报告者 Tested-by；Sebastian 确认性能权衡后收进入口树。

## 效果评估
效果证据为修复断言：PeterZ 明确「I can confirm that the below does in fact cure your testcase」——即 nested vfork 测试用例不再触发 scheduling-while-atomic。除此之外无线程数/性能影响的量化数据：vfork+exec 路径新增 hash 分配的开销只有定性预期，未见测量。

## 我可以参与的点
- kind=testing：在高频 vfork+exec 的负载（shell 脚本、容器 init 等）上对比修复前后的微基准，量化私有 hash 分配新增的开销——这正是Sebastian 确认时需要的数据。
- kind=review：分析 nested vfork 打破前提的完整路径（guard(private_hash) 与 hash 分配时机），确认 `clone_flags & CLONE_VM` 之外是否还有未覆盖的克隆形态。

## 参考链接
- 原始报告（09-10，未入当日缓存）：https://lore.kernel.org/all/CAG48ez26PrUOb8er9TP1gWLsqVLU8TEDr+1Zs25fgH0++=zhUQ@mail.gmail.com/
- PeterZ 的定位与修复提案：https://lore.kernel.org/all/20260911083639.GX776954@noisy.programming.kicks-ass.net/
- PeterZ 的确认与 diff：https://lore.kernel.org/all/20260911090447.GT788244@noisy.programming.kicks-ass.net/
- tglx 转问 bigeasy：https://lore.kernel.org/all/87cxukypiz.ffs@fw13/
- 引入排除的 commit：ee9dce44362b（"futex: Drop CLONE_THREAD requirement for private default hash alloc"，hash 取自回帖引文）
