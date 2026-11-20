# sched: boost rwsem holders with contended high-priority waiters

## TL;DR

Peng Huang（Google）发 RFC 3 补丁系列：跟踪每个任务持有的 rw_semaphore 与每把 rwsem 上的最高优先级 waiter，对「持锁且被高优先级 waiter 竞争」的 fair 任务临时提升其 effective priority 与 EEVDF weight，以缓解读/写 rwsem 上的优先级反转。带 KUnit 自测与可选的 `rwsem_sched_boost=` 开关。纯 RFC、无 cover、无维护者表态。

## 背景与问题

读写信号量是内核里常见的优先级反转源：一个低优先级任务持有 rwsem，被高优先级（RT/DL，或更高 nice 的 fair）任务竞相等待时，持锁者不会因 waiter 而得到调度优先级提升（mutex 有 rt_mutex PI 机制，rwsem 没有）。结果高优先级 waiter 被低优先级持锁者长时间阻塞。系列试图用「调度侧 boost」而非「锁侧 PI」来缓解：不修改用户可见的 `static_prio`/`nice`，仅在调度路径临时提升持锁者。

## 技术方案

三补丁：

- **1/3** `locking/rwsem, sched: track held rwsems and waiter priorities`：每个任务用定长 slot 数组（`CONFIG_RWSEM_SCHED_BOOST_SLOTS`）记录持有的 `rw_semaphore` 指针，每把 rwsem 用 `max_waiter_prio`（封顶 `MAX_RT_PRIO`）记录最高优先级竞争 waiter；阻塞加锁路径跳过 irq/atomic 守卫避免 fastpath pushf，trylock 保留 IRQ/atomic 过滤；slot 在 `preempt_disable()` 下、释放 `sem->count` 之前清空，防止其它 CPU 先获取并 free 该 sem 后 tick/preempt 仍看到它。加 `rwsem_sched_boost=` 内核参数。
- **2/3** `sched: boost rwsem holders with contended high-priority waiters`：把持 rwsem 的排队 fair 任务挂到 `rq->held_rwsem_tasks`，在 wakeup/preempt/tick/idle 负载均衡 `pull` 路径检查 waiter 需求；当 `max_waiter_prio < 任务 prio` 时临时提升 effective priority 与 EEVDF weight，unlock 时恢复、tick 上惰性断开无竞争任务。无竞争 lock/unlock 路径完全不碰 `rq->held_rwsem_tasks`。
- **3/3** `locking/rwsem: add KUnit tests for scheduler priority boost`：KUnit 覆盖 slot 跟踪、乱序解锁、slot 溢出回退、写锁降级、读写持锁者唤醒 boost、AB 优先级反转延迟、误提升检查与 fastpath 开销。

## 版本演进与当前进展

*current_version: v1（RFC，2026-11-19 发出、11-20 收件，`<20261119224954.196990-3-penghuang@google.com>` 为 2/3，3 补丁）*。纯 RFC 首版，无 cover（0/3 未在缓存），无 review 反馈。

## Maintainer 意见与讨论焦点

无任何维护者/评审表态（当日缓存未见回复）。作者声明无竞争 fastpath 零迭代、`rq->held_rwsem_tasks` 绝大多数 tick/idle pull 为空，属性能考量陈述（未见数据）。

## 合入评估

*likelihood=unknown*。RFC 阶段、无人表态。方案本质是「调度侧 PI 近似」——绕开 rwsem 无 PI 的历史包袱，但临时改 effective priority/EEVDF weight 的做法是否被调度维护者（Peter/Ingo）接受、与 rt_mutex/proxy execution 的交互都未验证。*blocking_issues*：无任何反馈；与 proxy execution / PI 语义的交互未论证；无性能数据。*next_action*：等调度与 locking 维护者表态，作者补数据与 cover。

## 效果评估

作者声称「无竞争路径零额外开销（`rq->held_rwsem_tasks` 常空、tick/idle pull 立即退出）」，但为「作者主观判断，未见 benchmark 数据」；KUnit 覆盖广度大但同样无量化延迟改善。

## 我可以参与的点

- **review**：论证该 boost 与现有 rt_mutex PI（尤其 proxy execution 的 donor 语义）是否冲突，及临时改 EEVDF weight 对带宽/滞后记账的影响。
- **discussion**：与 Waiman Long 的 rwsem 可写性、以及「rwsem 是否应引入真正 PI」这一长期话题对照，给出取舍判断。
- **testing**：用 sched-messaging / rt-app 的 rwsem 争用场景复测优先级反转延迟改善幅度。

## 参考链接

- lore thread（2/3，sched 补丁）: https://lore.kernel.org/all/20261119224954.196990-3-penghuang@google.com/

---
id: sched-20261120-013
date: '2026-11-20'
subject: "sched: boost rwsem holders with contended high-priority waiters"
subsystem: sched
type: feature
status: rfc
severity: none
thread_root_msgid: "<20261119224954.196990-3-penghuang@google.com>"
lore_url: "https://lore.kernel.org/all/20261119224954.196990-3-penghuang@google.com/"
authors: [Peng Huang]
maintainers_involved: []
current_version: v1
patch_series:
  - version: v1
    msgid: "<20261119224954.196990-3-penghuang@google.com>"
    date: '2026-11-19'
    summary: "RFC 3 补丁：跟踪 task 持有的 rwsem 与 waiter 优先级，对 fair 持锁者临时提升 effective priority/EEVDF weight，带 KUnit"
    review_outcome: "无反馈"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues: ["无任何反馈", "与 proxy execution/PI 语义的交互未论证", "无性能数据"]
  next_action: "等调度与 locking 维护者表态，作者补数据与 cover"
contribution_opportunities:
  - kind: review
    description: "论证 boost 与 rt_mutex PI/proxy execution donor 语义的冲突及 EEVDF weight 影响"
  - kind: discussion
    description: "与 rwsem 是否应引入真正 PI 的长期话题对照给出取舍判断"
  - kind: testing
    description: "用 rwsem 争用场景复测优先级反转延迟改善幅度"
generated_at: "2026-11-21T09:00:00+08:00"
source_email_count: 216
related_articles: []
tags: [cfs]
---