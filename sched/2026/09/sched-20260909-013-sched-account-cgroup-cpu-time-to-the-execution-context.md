# sched: Account cgroup CPU time to the execution context

## TL;DR

本文为增量更新，v1/v2 的来龙去脉见 related_articles 中的 sched-20260904-003。09-09 这枚单补丁拿到了**最关键的那一票**：John Stultz（`aa4f74dfd42b` 的作者、proxy execution 的原始设计者之一）给出 "Tentatively: Acked-by"，并第一次说明了当初为什么选择记到 donor——他是按 CPU 带宽控制器的情形来想的。Hui Su 随即用一个区分把这条反对意见拆掉：本补丁只改 `cgroup_account_cputime()` 这一处的 cgroup CPU usage，**不动 CFS bandwidth 记账**，John 担心的「donor 替 owner 破限」行为完全不变。

## 背景与问题

proxy execution 把调度上下文（`rq->donor`）与执行上下文（`rq->curr`）拆开后，per-task、thread-group 与 cgroup 的 user/system 时间已经记到实际执行的那个任务，但 `cgroup_account_cputime()` 仍记到 donor。当 donor 与执行任务分属不同 cgroup 时，cgroup 的 CPU 用量会被算到另一个组头上——`cpu.stat` 的 `usage_usec` 与实际消耗者不一致。

John Stultz 在 09-09 的回帖里补上了这段设计的历史动机，此前邮件中没人说清过（原文引述）：

> Commit aa4f74dfd42b ("sched: Fix runtime accounting w/ split exec & sched contexts") was trying to allow the owner's cputime to make sense in top, but we still want the donor to be "donating" their time, so I thought the compromise of charging the donor's cgroup would make more sense. I'm imagining something like the cpu bandwidth controllers, where it seemed like the donor's cgroup is who we'd want to charge, and eventually throttle, even though it is donating time to the lock owner to run (since even if the lock owner's cgroup was throttled, proxying will let the donor "bust" through the limit and run the lock owner using the donor's bandwidth - up until the donor's bandwidth was exceeded).

也就是说原来的选择不是疏忽，而是刻意把「该被限流的组」当作记账对象。

## 技术方案

1 行改动（`kernel/sched/fair.c`），把 cgroup CPU usage 的记账目标从 `rq->donor` 换成 `rq->curr`。

Hui Su 14:08 的回帖是本日技术上最有信息量的一段，他划出了本补丁的作用边界：

> this patch only changes the cgroup CPU usage accounting performed by `cgroup_account_cputime()`. It does not change CFS bandwidth accounting. Under proxy execution, `update_curr()` still accounts CFS bandwidth through `account_cfs_rq_runtime()` on the cfs_rq associated with the scheduling context. Thus, the donor's scheduling bandwidth continues to be consumed as before; this patch does not change the bandwidth or throttling behavior John described.

结论是：**「观测口径」（cgroup usage 统计）跟执行者走，「控制口径」（带宽消耗与限流）仍跟调度上下文走**。John 设想的那个破限场景确实存在，但它由 CFS bandwidth 那条路径决定，本补丁不触碰。这个区分如果写进 commit message，会显著降低后来人重新质疑同一件事的成本。

## 版本演进与当前进展

- v1、v2（v2 线程根 `<20260904034707.268416-1-sh_def@163.com>`，09-04）：沿用 Tejun Heo 的意见改成跟随执行上下文，Tejun 已给出带条件的 Acked-by（"Provided John is okay with going this way"）。
- 09-09 13:17 John Stultz 给出 "Tentatively: Acked-by"——Tejun 的前置条件被满足了。
- 09-09 14:08 作者回复，做出上面的 accounting 边界区分，并同意 John 提的 per-task "donated"/"gifted" 时间跟踪是**独立的后续工作**。
- 无 tip-bot，无 stable。

## Maintainer 意见与讨论焦点

- **John Stultz 的 "Tentatively" 是带保留的**：他的措辞是 "But if it is causing trouble for the accounting, and you think it makes more sense the other way, I'll trust your judgement." 这是把判断权让给作者/Tejun，而不是从技术上认同「记给执行者更对」。他的历史动机（按带宽控制器思路记给该被限流的组）在邮件里没有人在原则上反驳，只是被 Hui Su 说明了「本补丁不触及那条路径」。
- **一个悬着的后续**：John 提的 "Eventually I think we'll want to track per-task 'donated' and 'gifted' time so folks can more finely distinguish the accounting." ——作者也认同 "sounds useful"，但双方都把它划为 separate follow-up work，目前没有任何人认领。这是一个语义清楚、需求已成立、无人动手的口子。
- 本日没有反对意见。

## 合入评估

`likelihood=high`。1 行改动，Tejun Heo 有带条件的 Acked-by、条件（John 同意）本日已满足，且 John 明确说了 "I'll trust your judgement"。剩余风险只有一条：他的 ack 是 "Tentatively"，且他给出的原始设计理由并未被否定、只是被说明为不相关——如果后续有人真的拿「donor 的组该被限流」来主张恢复原记账，这场讨论会重开。

`next_action`：建议把 Hui Su 那段「usage 跟执行者、bandwidth 跟调度上下文」的区分写进 commit message，然后请 Peter Zijlstra 收下；顺带请 John 把 "Tentatively" 换成正式 tag，或直接把这段区分回给他确认。

## 效果评估

无 benchmark，也无实测数据。本日唯一新增的是**论证性证据**：John 说明了他当初的意图（这个补丁要反对的是设计意图而不是代码），Hui Su 用一个不重叠的作用域划分回应。补丁自身只改统计归属，没有性能影响面，因此「无数据」在这里是合理的，而不是缺失。

需要留意的是，这 1 行会直接改变 cgroup CPU 用量的**读数**：在启用 proxy execution 且 donor 与 owner 跨 cgroup 的负载上，`cpu.stat:usage_usec` 会从一个组转移到另一个组。这类改变对监控/计费口径的使用者是可感知的，但邮件里没有人讨论过迁移影响。

## 我可以参与的点

- `discussion`：本线程缺一次「John 是否确认那段边界区分解决了他顾虑」的正面收口。可以直接把「usage 跟 curr / bandwidth 跟 donor」这两句话回给他并请他把 Tentatively 转正。这是让补丁往前走的最省事的一步。
- `testing`：如果你有启用 proxy execution 的环境，构造一个 donor 与锁持有者分属不同 cgroup 的场景，记录改前/改后 `cpu.stat:usage_usec` 落在哪个组、以及 CFS 限流触发点是否确实没变。这一条正好是本文唯一没有任何实测支撑的断言。
- `extend`：John 提的 per-task "donated"/"gifted" 时间是明确被双方认可但无人认领的后续工作——把它做成一组新的 per-task/cgroup 统计字段（配合 rstat），是一个范围清楚、动机已被维护者写在工作邮件里的独立特性。
- `new_patch`：若自家分支启用了 proxy execution 且依赖 cgroup CPU 计费口径，这枚 1 行补丁适合直接回合；注意它是**统计口径变更**，需要先确认自家的用量采集侧是否假定「记给 donor」。

## 参考链接

- v2 线程根: https://lore.kernel.org/all/20260904034707.268416-1-sh_def@163.com/
- John Stultz 的 Tentatively Acked-by 与历史动机: https://lore.kernel.org/all/CANDhNCq5iPq87=iKSJv-XzYzTYJ8Hp+bPJ6SoVfWB3pRa=HypQ@mail.gmail.com/
- Hui Su 关于 usage 与 bandwidth 记账边界区分的回复: https://lore.kernel.org/all/20260909060843.2524877-1-sh_def@163.com/
- 相关上游提交 `sched: Fix runtime accounting w/ split exec & sched contexts`（aa4f74dfd42b）: https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=aa4f74dfd42b
- tip-bot commit: 未获取到
- stable backport: 未获取到

---
id: "sched-20260909-013"
date: "2026-09-09"
subject: "sched: Account cgroup CPU time to the execution context"
subsystem: sched
type: bug
status: under_review
severity: low
thread_root_msgid: "<20260904034707.268416-1-sh_def@163.com>"
lore_url: "https://lore.kernel.org/all/CANDhNCq5iPq87=iKSJv-XzYzTYJ8Hp+bPJ6SoVfWB3pRa=HypQ@mail.gmail.com/"
upstream_commit: null
fixes_commit: null
merged_branch: null
current_version: v2
generated_at: "2026-09-10T01:05:00"
authors:
  - "Hui Su"
maintainers_involved:
  - "John Stultz"
  - "Tejun Heo"
patch_series:
  - version: v2
    msgid: "<20260904034707.268416-1-sh_def@163.com>"
    date: "2026-09-04"
    summary: "沿用 Tejun Heo 意见，把 cgroup_account_cputime() 的目标从 rq->donor 改为 rq->curr，使 cgroup CPU usage 与实际执行任务一致；kernel/sched/fair.c 单行改动，不改 CFS bandwidth 记账路径。"
    review_outcome: "Tejun Heo 此前给出条件式 Acked-by（需 John 同意）。09-09 13:17 John Stultz 给 Tentatively Acked-by 并说明 aa4f74dfd42b 当初选择记给 donor 是出于 CPU 带宽控制器「该限流谁就记给谁」的考虑；14:08 作者回应本补丁不触及 account_cfs_rq_runtime() 的带宽路径，故该场景行为不变，并认同 donated/gifted 时间为独立后续工作。"
merge_assessment:
  likelihood: high
  blocking_issues:
    - "John Stultz 的 ack 仍写作 Tentatively，且他给的历史动机是被说明为不相关、而非被否定"
    - "commit message 里目前未包含「cgroup usage 跟执行者、CFS bandwidth 跟调度上下文」这一区分，后来人可能重复质疑"
    - "无 tip-bot 收录，尚需 Peter Zijlstra 收取"
  next_action: "把记账边界区分写进 commit message，请 John 将 Tentatively 转为正式 Acked-by 后由 Peter 收取"
contribution_opportunities:
  - kind: discussion
    description: "把 usage 跟 rq->curr、bandwidth 跟调度上下文这两句回给 John，请他确认这已解决其顾虑并把 Tentatively ack 转正"
  - kind: testing
    description: "在启用 proxy execution 的环境构造 donor 与锁持有者跨 cgroup 的负载，实测改前改后 cpu.stat:usage_usec 归属与 CFS 限流触发点是否确实如论证那样只有前者变化"
  - kind: extend
    description: "实现 John 提出、作者也认可但双方都未认领的 per-task donated/gifted 时间统计，配合 rstat 暴露到 cgroup 侧"
  - kind: new_patch
    description: "启用 proxy execution 且依赖 cgroup CPU 计费口径的自家分支可回合这枚单行补丁，但需先确认自身采集侧是否假定用量记给 donor"
source_email_count: 2
related_articles:
  - "sched-20260904-003"
  - "sched-20260903-008"
tags:
  - "cgroup"
  - "cfs"
---
