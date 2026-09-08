# sched/fair: reuse the ENQUEUE_DELAYED calculation in enqueue_task_fair()

## TL;DR

本文为增量更新，方案背景见 [[sched-20260824-011]] 与 [[sched-20260826-002]]，命名之争的经过见 [[sched-20260827-019]]。09-08 这处持续三天的口味之争收尾了，而且收得有点戏剧性：Kayra Cizmeci 在 00:05 误发了一封「Gentle ping on this patch」到另一个补丁（`sched/fair: Remove unused autogroup.h include`）的线程上，九分钟后在正确的线程里一边回帖一边道歉（「Sorry for this autogroup.h ping thing. Ah..」），并给出结论——他放弃自己原本「改名后两处共用」的想法，接受 Prateek 的判断，直接**丢掉 1/2**，只继续推 2/2（`sched/fair: reduce repeated work in enqueue path`）。也就是说这个补丁不会进主线了，本线程最后剩下的实质信息是作者的取舍理由。

## 背景与问题

摘要（详见前文）：v2 两补丁的 1/2 把 `enqueue_task_fair()` 内散落的 `flags & ENQUEUE_DELAYED` 检查收敛为函数开头计算一次的局部 `bool delayed`，声明 "No functional change intended"。Prateek Nayak 08-26 提 nit：`if (!p->se.sched_delayed || delayed)` 读起来别扭（「not delayed or delayed?」），并认为这层间接反正会被编译器优化掉，大写宏对人类读者更友好。08-27 作者反问「为什么不干脆改名后两处共用」，讨论悬在这里。

## 技术方案

本日无代码更新，是作者对方案取舍的最终表态。他贴出的争议 hunk 原样保留在邮件里：

```
 	-	if (!p->se.sched_delayed || (flags & ENQUEUE_DELAYED))
 	+	if (!p->se.sched_delayed || delayed)
```

Prateek 的原话（作者在回帖中引用的部分）：

> nit. This reads funny now - not delayed or delayed?
> Maybe wakeup_delayed but all of this should be optimized by compiler
> at the end and a big ENQUEUE_DELAYED is better for humans who are
> reading the code no?

作者接受这个判断，并逐条给出理由：

> In my first message I was thinking that renaming and using it in both places would be the better approach. But I thought about this the meantime and I changed my mind. flags & ENQUEUE_DELAYED reads better and more clear than a bool. And I can't really see a big advantage of renaming it over this version.

他还主动修正了自己补丁标题的口径问题——这其实是被 Prateek 顺带点出来的第二件事：

> Patch subject is a bit confusing since it says reuse the bla bla calculation in the enqueue_task_fair(). And this subject makes it seem like there is a performance claim.
> I knew It was getting optimized by the compiler, I thought at the time that gathering this flags & ENQUEUE_DELAYED in one place would be better.

即「reuse … calculation」这个标题会被读成性能优化，而他本意只是把判断收集到一处，且他从一开始就知道编译器会优化掉。结论：「I'm dropping this patch (1/2) but I'll continue with 2/2 :->.」

## 版本演进与当前进展

- 09-08 00:05:21 误发（`<20260907160522.1152423-1-kayracizmeci@gmail.com>`，主题 `Re: [PATCH] sched/fair: Remove unused autogroup.h include`，正文只有「Gentle ping on this patch.」）。
- 09-08 00:14:48 作者在本线程发出正确回帖（`<20260907161448.1152895-1-kayracizmeci@gmail.com>`，`in-reply-to` 指向上面那封误发邮件），末尾附 NOTE 说明误发原因：「I send the wrong file that was with the same name with my correct file that I supposed to send.」
- 版本停在 v2，v3 未见。按本帖表态，v3 若出现只会包含 2/2 一片。
- 本线程本日无 Prateek 或其他人回帖。

## Maintainer 意见与讨论焦点

- 本日没有维护者发言；被关闭的是 **K Prateek Nayak** 的两条意见：（1）局部布尔量可读性差，建议改名或维持宏；（2）补丁标题暗示了不存在的性能收益。作者两条都接受。
- 争点以「撤回补丁」而非「采纳改名」结束，作者给的理由是可读性判断反转，不是技术障碍。
- 仍然悬空的相关问题：这个系列原本想解决的是 `enqueue_task_fair()` 里的重复判断，1/2 撤掉后，2/2（`reduce repeated work in enqueue path`）是否还能独立成立、以及是否仍带同样的「性能口径」标题问题，本日作者没有说明。

## 合入评估

`likelihood=low`——更准确地说，**这一片已按作者本人的决定不再推进**（撤回而非被 NAK）。`blocking_issues`：

1. 作者明确「dropping this patch (1/2)」，没有留下「若有人支持改名方案可再议」的口子。
2. 剩余价值判断（是否值得为可读性做这类替换）社区并未给出一般性结论，Prateek 的意见停留在个人口味表达，若日后有人重提，仍需回答同一个问题。

`next_action`：本补丁无需跟进；要跟进的是 2/2 的 v3。

## 效果评估

无效果数据，也不该有——作者自己承认这里没有性能主张（「I knew It was getting optimized by the compiler」），本线程从头到尾没有 benchmark，也不存在需要数据的场景。

## 我可以参与的点

- **只有一件小事（discussion）**：如果在意这类「把重复判断收敛到局部变量」的清理，可以在 2/2 出现时一并表态，判断标准是「编译器会优化掉的前提下，聚合是否提升可读性」——本线程两位参与者给了相反的答案，社区没有共识，这类口味争端的裁决规则比单个补丁更值得记下来。
- **不必做的事**：本线程已闭环，不需要测试、不需要 review 意见。硬要在这里做点是浪费维护者注意力。
- **可迁移的教训（自我提醒）**：标题里出现 "reuse"/"optimiz" 这类词会被当作性能声明。自己在写 sched 侧清理补丁时应避免这种口径，作者的这段反思对我也适用。

## 参考链接

- 本日作者回帖（撤回 1/2 + 误发说明）: https://lore.kernel.org/all/20260907161448.1152895-1-kayracizmeci@gmail.com/
- 本日误发的那封: https://lore.kernel.org/all/20260907160522.1152423-1-kayracizmeci@gmail.com/
- v2 1/2（系列 root）: https://lore.kernel.org/all/0b1ef9d0122ae3037dac38d2549f13c9b063369a.1787737648.git.kayracizmeci@gmail.com/
- Prateek Nayak 的 nit 原帖（08-26）: 未获取到——本日缓存里只有作者在回帖中转引的原文，该邮件不在本批缓存内
- tip-bot commit: 未获取到
- stable backport: 未获取到
---
id: sched-20260908-011
date: '2026-09-08'
subject: "sched/fair: reuse the ENQUEUE_DELAYED calculation in enqueue_task_fair()"
subsystem: sched
type: discussion
status: stalled
severity: none
thread_root_msgid: <0b1ef9d0122ae3037dac38d2549f13c9b063369a.1787737648.git.kayracizmeci@gmail.com>
lore_url: https://lore.kernel.org/all/20260907161448.1152895-1-kayracizmeci@gmail.com/
upstream_commit: null
fixes_commit: null
merged_branch: null
current_version: v2
generated_at: '2026-09-08'
authors:
- Kayra Cizmeci
maintainers_involved:
- K Prateek Nayak
patch_series:
- version: v2
  msgid: <0b1ef9d0122ae3037dac38d2549f13c9b063369a.1787737648.git.kayracizmeci@gmail.com>
  date: '2026-08-26'
  summary: '把 enqueue_task_fair() 内散落的 flags & ENQUEUE_DELAYED 收敛为函数开头一次的局部 bool delayed，声明 No functional change intended。'
  review_outcome: '作者 09-08 宣布 "I''m dropping this patch (1/2) but I''ll continue with 2/2"，接受 Prateek 关于可读性与标题暗示性能收益的两条意见；本版不再推进。同封还说明 00:05 那封 autogroup.h 的 Gentle ping 是误发（同名文件搞错）。'
merge_assessment:
  likelihood: low
  blocking_issues:
  - 作者主动撤回该补丁，未留重议口子（非维护者 NAK）
  - 同类「聚合重复判断是否提升可读性」的问题社区无一般性结论，日后重提仍要回答同一问题
  - 2/2 是否仍能独立成立、是否沿用同一标题口径，本日未说明
  next_action: '本补丁无需跟进；关注 2/2（sched/fair: reduce repeated work in enqueue path）的 v3'
contribution_opportunities:
- kind: discussion
  description: 在 2/2 出现时，就编译器会优化掉的前提下「聚合重复判断是否提升可读性」表态，给这类口味争端补一条可复用的判断标准
source_email_count: 2
related_articles:
- sched-20260827-019
- sched-20260824-011
- sched-20260826-002
tags:
- cfs
- eevdf
---
