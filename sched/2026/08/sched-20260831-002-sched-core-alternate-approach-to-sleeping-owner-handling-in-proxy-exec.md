# sched/core: Alternate approach to sleeping-owner handling in PROXY_EXEC

## TL;DR

本文为增量更新（完整背景见 related_articles）。K Prateek Nayak（AMD）的 16 补丁 RFC PoC 在 8/31 于 `04/16 "Activate blocked donor when no owner is found"` 上给出决定性数据：为回应 Andrea Righi「owner 为 NULL 时 `proxy_resched_idle()` 会空转、要唤醒所有观察到 `!owner` 的任务」，他贴出三组 mutex 侧实验（强制 handoff / 新增 `MUTEX_FLAG_STEAL` / 临时把 owner 换成 idle 任务）与 `sched-messaging` 结果，证明「有 waiter 就强制 handoff」会带来 -11%~-122% 回退；Andrea 当晚接受该结论并转而追问 `find_proxy_task()` 是否要显式处理 STEAL，避免与 idle 任务建立 donor 关系。仍是 RFC/PoC，无人 Ack/NAK。

## 背景与问题

该系列处理的是 proxy-exec 里 **sleeping owner** 与 blocked donor 的竞态：owner 睡着时 proxy chain 要挂在 owner 上并在 owner 唤醒时做 chain activation，而 blocked donor 可能被另一个并发唤醒事件提前叫醒，于是激活路径要多拿一把 `p->blocked_lock` 才能不漏掉 donor。Patch 04/16 解决的是最刺眼的一个症状：**找不到 owner 时如何激活 blocked donor**。mutex 的 owner 可以一直是 NULL，直到 `mutex_unlock()` 选中的 waiter 真正拿到 CPU 并获取 mutex 为止，因此 `proxy_resched_idle()` 可能自旋得比「unlock 临界区」长得多，而把每个观察到 `!owner` 的任务都唤醒一遍代价很高。

Andrea Righi 原先提的备选是：proxy execution 打开且 mutex 带 `MUTEX_FLAG_WAITERS` 时，直接从 `mutex_unlock_slowpath()` 强制一次 handoff，这样 owner 始终可识别，也不用唤醒所有 `!owner` 观察者。Prateek 担心这会削弱 optimistic spinning + `mutex_trylock()` 的收益，于是去实测。

## 技术方案

三组实验都建立在 John Stultz 的开发树 `https://github.com/johnstultz-work/linux-dev.git` 分支 `proxy-exec-v31-7.2-rc4`、commit `06ac43db4d8e`（"[ANNOTATION] === Needs confirmation of functionality past this point ==="），`CONFIG_SCHED_PROXY_EXEC=y`。作者反复声明"very experimental，建议用 virtme-ng 或一次性环境验证"。

1. **实验 1 — Simple Handoff**：把 `__mutex_unlock_slowpath()` 里的强制 handoff 条件从 `current->blocked_donor` 放宽为 `current->blocked_donor || (owner & MUTEX_FLAG_WAITERS)`。
2. **实验 2 — Allow steal until next task is found**：在 `kernel/locking/mutex.h` 新增 `MUTEX_FLAG_STEAL 0x08`（`MUTEX_FLAGS` 由 `0x07` 扩到 `0x0F`）；unlock 时若 owner 带 WAITERS 就置 STEAL 并在成功后走 `__mutex_steal(lock, next)`；`__mutex_trylock_common()` 与 `mutex_spin_on_owner()` 看到 STEAL 即跳出（STEAL 不允许在 HANDOFF 已发起后置位，命中时清 STEAL 并把 task 解析为 `curr`）。约束被作者列成两条：老 owner 不能在 unlock 后继续留存（它可能死掉或阻塞在别的 mutex 上，会让新 waiter 挂到死任务/错误 owner 上）；也不能在 handoff 给新 owner 之后还允许 steal，否则并发偷锁会破坏 proxy。
3. **实验 3 — STEAL + Temporary swap to idle**：unlock 时把 owner 临时换成 `idle_task(raw_smp_processor_id())` 并带 STEAL——注释理由是 idle 永远 `->on_rq`，proxy donor 可以先临时迁到这里，直到 wakeup 或 optimistic spinner 把锁拿走。
   - 遗留竞态（作者在 patch 里标了 `XXX`）：最后一个 waiter 可能在"带 STEAL 的完整 unlock"完成前被信号打断，出现 `__mutex_remove_waiter()` 把 flag 全清掉、`lock->owner` 以 idle 身份残留且没有 STEAL 的窗口。他的做法是 `__mutex_clear_flag(lock, MUTEX_FLAGS & ~MUTEX_FLAG_STEAL)` 保留 STEAL，代价是 `__mutex_trylock_fast()` 对第一个竞争者临时失败；备选方案（他自认也可行）是在 `__mutex_unlock_slowpath()` 里，若 steal 已置但 `lock->wait_lock` 下已找不到 waiter，就补一次 `atomic_try_cmpxchg()`/`__mutex_clear_flag()`。

被放弃的备选：实验 1 被数据否定；实验 2 被作者与自己共同判定"只是收窄 handoff 窗口、大部分成本还在"。

## 版本演进与当前进展

- RFC v1：2026-08-26 发出 16 补丁（cover `<20260826062901.2137-1-kprateek.nayak@amd.com>`），当天 Andrea 已就 PELT 注释与 owner-NULL 自旋提过意见（见 sched-20260826-001）。
- 2026-08-31：Prateek 在 `04/16` 回帖给出上述三组实验与数据；Andrea 23:07 回复接受结论。**系列版本未变（仍是同一版 RFC）**，也没有出现新的重构 patch 集。
- 系列自身状态：cover 里写明"not bisectible in any way at the moment"，Patch 1–4 是可以脱离其余 RFC 单独讨论的 fix。

## Maintainer 意见与讨论焦点

- **Andrea Righi（NVIDIA，proxy-exec/sched_ext 侧主要 review 者）撤回自己的建议**："the results make it pretty clear that forcing a handoff whenever waiters are present is not viable, so my original suggestion doesn't look practical."
- 对实验 2 的判定："this only narrows the handoff window and still retains most of its cost."
- 对实验 3 提出**新的未解决问题**：idle task 在这里只是"临时 owner 标记"，但 `find_proxy_task()` 会把它当成真实的 mutex owner 处理，从而可能设置 `idle->blocked_donor`——"Should we handle the STEAL state explicitly in find_proxy_task() to avoid creating a donor relationship with the idle task?" 该问题当天没人回答。
- 作者自述的信心边界：实验 3 在他的机器上跑了一段时间，没看到 lockup / hung task，因此"至少互斥是站得住的"，其余部分寄望他人验证。
- Peter Zijlstra 当天未介入此线程；无 Acked-by、无 Reviewed-by、无 NAK。

## 合入评估

**unlikely**（就当前 RFC 而言）。这是一次方向探索而非可合入实现：系列自述不可 bisect、代码在 locking 侧新增 mutex owner flag 位并与 proxy-exec 状态机耦合、作者自己称之为"insane idea"并声明实验性；卡点是实验 3 里 idle-as-owner 的语义正确性（Andrea 的 `find_proxy_task()` 问题）与"老 owner 不能持久保留/steal 与 handoff 不能并存"这两条约束的完整解法。`next_action` 是作者要把实验 3 收敛成一个能回答 donor/owner 关系问题的正式方案，并让 Patch 1–4 这类可独立讨论的 fix 先行。

## 效果评估

唯一数据是 `sched-messaging`（Normalized time in seconds，AMean，越低越好），列为 vanilla / handoff / STEAL + handoff / idle + STEAL 四态对比：

| groups | vanilla | handoff | STEAL + handoff | idle + STEAL |
|---|---|---|---|---|
| 1 | 3.12 | 3.47（-11.21%） | 3.63（-16.34%） | 3.59（-15.06%） |
| 2 | 3.43 | 4.33（-26.23%） | 4.14（-20.69%） | 3.48（-1.45%） |
| 4 | 4.05 | 5.95（-46.91%） | 5.45（-34.56%） | 4.00（**+1.23%**） |
| 8 | 4.29 | 9.56（-122.84%） | 7.80（-81.81%） | 4.31（-0.46%） |
| 16 | 5.89 | 12.29（-108.65%） | 11.89（-101.86%） | 5.91（-0.33%） |

作者标注：1-groups、2-groups 两行"在所有版本上都有 >10% 的 run-to-run variance"。解读要点是**相对差异**（强制 handoff 在高并发组上灾难性回退，idle+STEAL 基本回到 vanilla 水平），而不是 idle+STEAL 比 vanilla 更快——它没有更快，只是把 proxy-exec 的额外代价抹平了。邮件里没有 mutex 微观延迟、也没有 proxy chain 命中率之类的数据。

## 我可以参与的点

- **直接可回的问题**：`find_proxy_task()` 遇到带 STEAL 的 idle owner 时如何避免建出 `idle->blocked_donor`——目前线程里没人回答，给出方案或至少给出受影响代码路径分析就是有效贡献。
- **独立复测**：该结论目前只有 AMD 一台机器的 `sched-messaging` 数据。在自家机型（尤其高核数、大 group 数）上跑同一棵树 `proxy-exec-v31-7.2-rc4`@`06ac43db4d8e` 的三态对比，比再造一个新方案更有价值。
- **可 bisect 化**：cover 的"不可 bisect"是最容易被维护者拿来卡的点，把 Patch 1–4（不依赖后续 RFC 的 fix）单独拆成可独立合入的小系列，是回合 OLK-6.6 前也需要做的事。

## 参考链接

- 本日回复（Andrea Righi）: https://lore.kernel.org/all/apWYv6SdL0Ck-a5w@gpd4/
- 被讨论补丁 04/16: https://lore.kernel.org/all/20260826062901.2137-5-kprateek.nayak@amd.com/
- 系列 cover（00/16）: https://lore.kernel.org/all/20260826062901.2137-1-kprateek.nayak@amd.com/
- 实验基线树: `https://github.com/johnstultz-work/linux-dev.git` 分支 `proxy-exec-v31-7.2-rc4`，commit `06ac43db4d8e`
- John Stultz 原始大补丁（cover 内引用的 msgid）: https://lore.kernel.org/all/20260807035232.1881495-9-jstultz@google.com/
- tip-bot commit: 未获取到
- stable backport: 未获取到

---
id: sched-20260831-002
date: '2026-08-31'
subject: "sched/core: Alternate approach to sleeping-owner handling in PROXY_EXEC"
subsystem: sched
type: discussion
status: rfc
severity: none
thread_root_msgid: "<20260826062901.2137-1-kprateek.nayak@amd.com>"
lore_url: "https://lore.kernel.org/all/apWYv6SdL0Ck-a5w@gpd4/"
authors: [K Prateek Nayak, Andrea Righi]
maintainers_involved: [Andrea Righi]
current_version: v1
patch_series:
  - version: v1
    msgid: "<20260826062901.2137-1-kprateek.nayak@amd.com>"
    date: 2026-08-26
    summary: "16 补丁 RFC PoC，用 __task_rq_lock() 方案替代 chain-wakeup 的多锁组合，Patch 1-4 为可独立讨论的 fix"
    review_outcome: "Andrea Righi 就 owner 为 NULL 时 proxy_resched_idle() 自旋与唤醒开销提问；Prateek 于 08-31 用三组 mutex 实验作答"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: unlikely
  blocking_issues:
    - "系列自述不可 bisect，属 PoC 性质"
    - "idle 作为临时 owner 标记后 find_proxy_task() 可能建立 idle->blocked_donor，正确性无人给出结论"
    - "MUTEX_FLAG_STEAL 与 HANDOFF/PICKUP 的互斥约束、最后一个 waiter 被打断导致 owner 卡在 idle 的窗口尚未收敛"
  next_action: "把实验 3 收敛为可回答 donor/owner 关系的正式实现，并让 Patch 1-4 独立先行"
contribution_opportunities:
  - kind: discussion
    description: "回答 find_proxy_task() 是否需要显式处理 MUTEX_FLAG_STEAL，避免与 idle 任务建立 donor 关系（线程内目前无人回应）"
  - kind: testing
    description: "在 proxy-exec-v31-7.2-rc4@06ac43db4d8e 上用自己的机型复测 vanilla/handoff/STEAL+handoff/idle+STEAL 四态 sched-messaging"
  - kind: new_patch
    description: "把不依赖后续 RFC 的 Patch 1-4 拆成可 bisect 的独立小系列"
generated_at: "2026-09-07T21:16:22"
source_email_count: 1
related_articles: [sched-20260826-001]
tags: [preempt, sched_ext]
---
