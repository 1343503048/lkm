# sched: Account cgroup CPU time to the execution context

## TL;DR
本文为增量更新，完整背景与 v1/v2 演进见 related_articles 中的 sched-20260909-013 / sched-20260904-003。09-10 的唯一进展是 **Tejun Heo 直接回复 John Stultz，把这枚单行补丁背后的口径之争定了调**：cgroup 基础统计应当与 per-thread 上报一致，即使这意味着它与 bandwidth enforcement 不再吻合，而这个缺口应该用「proxy execution 的显式统计」来补——也就是 John 自己提的 donated/gifted 时间思路。至此 cgroup 维护者与原设计者两方立场对齐，此前一直无人认领的那个后续工作被 Tejun 明确认定为正确方向。补丁本身仍等 Peter Zijlstra 收取。

## 背景与问题
（本节为增量文章，完整背景见 sched-20260909-013，此处只保留理解本日讨论所必需的部分。）

proxy execution 把调度上下文（`rq->donor`）与执行上下文（`rq->curr`）拆开后，per-task 与 thread-group 的 user/system 时间已跟随实际执行者，但 `cgroup_account_cputime()` 仍记给 donor。当 donor 与锁持有者分属不同 cgroup 时，`cpu.stat` 的 `usage_usec` 会落到另一个组头上。

争议点不是代码而是**设计意图**：`aa4f74dfd42b`（"sched: Fix runtime accounting w/ split exec & sched contexts"）当初刻意记给 donor，John Stultz 在 09-09 的说明是——他按 CPU 带宽控制器的情形来想，「该被限流的组」就是 donor 的组，即便 donor 把时间借给锁持有者、甚至因此突破 owner 组的限流，也应记在 donor 账上。Hui Su 的回应是划清作用域：本补丁只改 `cgroup_account_cputime()` 的 usage 归属，不动 `update_curr()` → `account_cfs_rq_runtime()` 的带宽路径，因此 John 设想的限流行为完全不变。

本日 Tejun 的回帖，正面回答的正是这个「usage 口径与 bw 口径要不要一致」的问题。

## 技术方案
补丁方案本日无变化：`kernel/sched/fair.c` 单行，把 `cgroup_account_cputime()` 的记账目标从 `rq->donor` 改为 `rq->curr`。

本日新增的是**方案之上的口径决策**，Tejun 原文（09-10 01:48）：

> Yeah, I want the cgroup base stats to agree with what's reported for threads. This makes it disagree with bw enforcement but I think it makes more sense to bridge that gap with explicit stats for proxy execution like you're suggesting.

拆开看是三层决定：

1. **cgroup 基础统计（base stats）与 per-thread 上报必须一致**——这是 Tejun 作为 cgroup 维护者给出的硬约束，等价于认可本补丁的方向：既然线程级时间已跟 `rq->curr`，cgroup 级 usage 也必须跟 `rq->curr`，否则同一份 CPU 时间在 `cpu.stat` 与 `/proc/<pid>/stat` 两处对不上。
2. **明确承认由此产生的不一致**：usage 口径与 bandwidth enforcement 口径将分道（前者跟执行者，后者跟调度上下文）。这不是被忽略的副作用，而是被接受的设计结果——Hui Su 09-09 划出的作用域边界，在 Tejun 这里从「本补丁不触及」升级为「本来就该分开」。
3. **缺口的补法是显式统计而非改记账口径**：用 proxy execution 专门的统计（John 提的 per-task "donated"/"gifted" 时间）把两个口径之间的差额暴露出来，而不是让 usage 去迁就 bw。

这个取舍的意义在于：它把「记给谁」这个二选一问题，转成「两个口径各自服务不同目的 + 用第三组统计把差额讲清楚」。后续若有人再以「donor 的组该被限流」为由要求把 usage 改回 donor，Tejun 这句话就是明确的反证。

## 版本演进与当前进展
- v1 / v2（v2 线程根 `<20260904034707.268416-1-sh_def@163.com>`，09-04）：按 Tejun 意见改为跟随执行上下文；Tejun 当时给的是**带条件**的 Acked-by——"Provided John is okay with going this way"。
- 09-09 13:17：John Stultz 给出 "Tentatively: Acked-by"，并说明 `aa4f74dfd42b` 当初记给 donor 的历史动机；Tejun 的前置条件形式上被满足。
- 09-09 14:08：作者 Hui Su 回应，划出 usage 与 CFS bandwidth 的作用域边界，并认同 donated/gifted 时间属独立后续工作。
- **09-10 01:48（本日）**：Tejun 回复 John，给出上述三层口径决定。这是该线程第一次由 cgroup 维护者对「usage 与 bw 不一致是否可接受」正面表态。
- 无 v3，无 tip-bot，无 stable 回帖；补丁仍未被任何树收取。

## Maintainer 意见与讨论焦点
- **Tejun Heo（cgroup / workqueue 维护者）**：本日定调方。他的措辞 "I want the cgroup base stats to agree with what's reported for threads" 是**要求**而非偏好，且他主动承认代价（"This makes it disagree with bw enforcement"）并指定了补偿手段。此前他的 ack 是条件式的，本日的表态实质上把条件变成了他本人的设计主张。
- **John Stultz（`aa4f74dfd42b` 作者）**：被回复方。他 09-09 的 ack 仍写作 "Tentatively"，原话包含 "I'll trust your judgement"；他提的 donated/gifted 统计被 Tejun 本日明确 endorse（"like you're suggesting"）。**但 John 在 09-10 缓存截止前没有回复 Tejun 这封**，因此他的 Tentatively 是否转正、他是否接受「bw 与 usage 口径分离」这个结论，仍未落定。这是本线程当前唯一悬着的技术性确认。
- **Peter Zijlstra（sched 侧）**：当日未参与本线程。值得注意的是同日他在同作者的相邻补丁 `sched/core: Call wq_worker_tick() for the execution context` 上明确表态 "I can take it through sched/urgent"（见 sched-20260910-017），说明 PE 记账类小修复的收取通道是通的——本补丁尚未获得同样的表态。
- 无 NAK、无新分歧。焦点已从「改不改」转移到「谁把 donated/gifted 统计做出来」。

## 合入评估
likelihood: high（与 sched-20260909-013 持平，但支撑更实：此前依赖 John 的让步式 ack，现在有 cgroup 维护者主动给出设计原则）。

blocking_issues：
- John Stultz 的 ack 仍是 "Tentatively"，且他未回复 Tejun 本日的定调邮件。
- Peter Zijlstra 未表态收取；补丁既不在 sched 树也不在 wq/cgroup 树里（`cgroup_account_cputime()` 的调用点在 `kernel/sched/fair.c`，路由天然归 sched）。
- commit message 仍未写入「usage 跟 `rq->curr`、bandwidth 跟调度上下文」这一区分——现在有了 Tejun 的原话可引，比 09-09 时更容易补。

next_action：作者把 Tejun 这段表态引进 commit message（或直接作为 cover 说明），请 John 把 Tentatively 转正，然后请 Peter 收取；考虑到同日 Peter 已愿意用 `sched/urgent` 收同作者的相邻修复，本补丁完全可以一并提出。

## 效果评估
本日无新增测试数据，也无性能影响面（只改统计归属）。

新增的是**论证性证据**，且层级比 09-09 更高：Tejun 给出的不是「我觉得这样更好」，而是一条可检验的一致性约束——cgroup base stats 必须与 per-thread 上报吻合。这条约束本身就是本补丁的效果论据：改之前，在 donor 与 owner 跨 cgroup 的 PE 场景下，`cpu.stat:usage_usec` 与 `/proc/<pid>/stat` 的 utime/stime 之和会对不上；改之后一致。

仍需标注为未验证的部分：「bandwidth 与 throttling 行为不变」这一断言至今只有 Hui Su 的代码路径论证，无实测；本补丁会改变监控/计费口径的读数，邮件中无人讨论过对既有采集侧的迁移影响。

## 我可以参与的点
- **把 donated/gifted 统计做出来（extend）**：本日的实质变化就在这里——这个后续工作此前「双方认可但无人认领」，现在 cgroup 维护者明确说「该用这个办法补缺口」。范围清楚：为 PE 场景增加 per-task（并可聚合到 cgroup）的 donated/gifted 时间计数，配合 rstat 暴露，使 usage 与 bw 两个口径的差额可观测。这是一个动机已被维护者写进邮件、且尚无人动手的独立特性，适合作为后续 patch 发出。
- **实测补齐唯一的无数据断言（testing）**：在启用 proxy execution 的环境构造 donor 与锁持有者跨 cgroup 的负载，同时记录三组数据——改前/改后 `cpu.stat:usage_usec` 的归属、`/proc/<pid>/stat` 的 utime+stime、以及 CFS 限流触发点，验证「只有前两者变化、限流不变」。把结果回帖可以同时收口 John 的 Tentatively 与 Tejun 的一致性主张。
- **推动收口（discussion）**：把 Tejun 本日的原话回给 John，请他确认这已解决其顾虑并将 ack 转正；同时提请 Peter 参照同日 `wq_worker_tick()` 补丁的处理方式（`sched/urgent`）一并收取。
- 自家分支若启用 PE 且依赖 cgroup CPU 计费口径，这枚单行补丁适合回合，但需先确认采集侧是否假定「记给 donor」（new_patch，同 sched-20260909-013）。

## 参考链接
- Tejun Heo 本日的口径定调（本线程当日邮件）: https://lore.kernel.org/all/aqGb1ar23XBzdaKn@slm.duckdns.org/
- 被回复的 John Stultz 邮件（Tentatively Acked-by 与历史动机）: https://lore.kernel.org/all/CANDhNCq5iPq87=iKSJv-XzYzTYJ8Hp+bPJ6SoVfWB3pRa=HypQ@mail.gmail.com/
- Tejun 早先的条件式 Acked-by: https://lore.kernel.org/all/appnKwylGK3QUIJ3@slm.duckdns.org/
- v2 线程根: https://lore.kernel.org/all/20260904034707.268416-1-sh_def@163.com/
- 相关上游提交 `aa4f74dfd42b`（sched: Fix runtime accounting w/ split exec & sched contexts）的 lore 链接: 未获取到（该 commit 的邮件不在本缓存内，不构造搜索链接）
- tip-bot commit / stable backport: 未获取到（尚未合入）
- 同作者相邻补丁当日的进展: 见 sched-20260910-017

---
id: sched-20260910-016
date: 2026-09-10
subject: "sched: Account cgroup CPU time to the execution context"
subsystem: sched
type: bug
status: under_review
severity: low
thread_root_msgid: "<20260904034707.268416-1-sh_def@163.com>"
lore_url: "https://lore.kernel.org/all/aqGb1ar23XBzdaKn@slm.duckdns.org/"
upstream_commit: null
fixes_commit: null
merged_branch: null
current_version: v2
generated_at: "2026-09-11T01:25:00"
authors:
  - "Hui Su"
maintainers_involved:
  - "Tejun Heo"
  - "John Stultz"
patch_series:
  - version: v2
    msgid: "<20260904034707.268416-1-sh_def@163.com>"
    date: "2026-09-04"
    summary: "把 cgroup_account_cputime() 的记账目标从 rq->donor 改为 rq->curr，使 cgroup CPU usage 与实际执行任务一致；kernel/sched/fair.c 单行改动，不改 CFS bandwidth 记账路径。"
    review_outcome: "Tejun Heo 先给条件式 Acked-by（Provided John is okay）；09-09 John Stultz 给 Tentatively Acked-by 并说明 aa4f74dfd42b 记给 donor 的带宽控制器动机，作者回应本补丁不触及 account_cfs_rq_runtime()；09-10 Tejun 直接回复 John，定调 cgroup base stats 必须与 per-thread 上报一致，接受其与 bw enforcement 分离，并主张用 proxy execution 显式统计（John 提的 donated/gifted）来补该缺口。John 尚未回复此定调邮件。"
merge_assessment:
  likelihood: high
  blocking_issues:
    - "John Stultz 的 ack 仍写作 Tentatively，且他未回复 Tejun 09-10 的定调邮件"
    - "Peter Zijlstra 未表态收取，补丁不在任何树里"
    - "commit message 仍未写入 usage 跟 rq->curr、bandwidth 跟调度上下文这一区分（现有 Tejun 原话可引）"
  next_action: "把 Tejun 的表态引进 commit message，请 John 将 Tentatively 转正，并请 Peter 参照同日 wq_worker_tick() 补丁走 sched/urgent 一并收取"
contribution_opportunities:
  - kind: extend
    description: "实现 PE 场景的 per-task donated/gifted 时间统计并经 rstat 聚合到 cgroup——此前无人认领，09-10 起被 cgroup 维护者明确认定为弥补 usage 与 bw 口径差额的正确做法"
  - kind: testing
    description: "在启用 proxy execution 的环境构造 donor 与锁持有者跨 cgroup 的负载，同时记录改前改后 cpu.stat:usage_usec 归属、/proc/<pid>/stat 的 utime+stime、CFS 限流触发点，验证只有前两者变化"
  - kind: discussion
    description: "把 Tejun 的原话回给 John 请其确认并把 Tentatively ack 转正，同时提请 Peter 参照同日相邻补丁的处理方式收取"
  - kind: new_patch
    description: "启用 PE 且依赖 cgroup CPU 计费口径的自家分支可回合这枚单行补丁，但需先确认采集侧是否假定用量记给 donor"
source_email_count: 1
related_articles:
  - "sched-20260909-013"
  - "sched-20260904-003"
  - "sched-20260910-017"
tags:
  - cgroup
  - cfs
  - proxy_execution
---
