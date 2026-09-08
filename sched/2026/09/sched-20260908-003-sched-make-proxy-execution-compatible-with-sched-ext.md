# sched: Make proxy execution compatible with sched_ext

## TL;DR

本文为增量更新，完整背景见 related_articles 中的 sched-20260904-007 / sched-20260904-008 / sched-20260831-001。09-08 是这个 18 补丁的 v13 系列开始「解冻」的一天：Peter Zijlstra 首次表态（本周会看，粗略看"do indeed seem fine"），作者 Andrea Righi 在同一天集中回掉了三条一直挂着无人应答的 review——Prateek Nayak 关于 02/18 出队顺序的追问、Tejun 在 12/18 的一批 nit、Richard Cheng 关于 17/18 scx_qmap CID 竞态的质疑。系列的技术争议面基本清零，剩下的瓶颈是 Peter 的正式评审与 v14 落地。

## 背景与问题

代理执行把调度上下文（`rq->donor`，被阻塞的互斥锁等待者）与执行上下文（`rq->curr`，实际跑代码的锁持有者）拆开，用于缓解优先级反转；而 `CONFIG_SCHED_PROXY_EXEC` 此前直接 `depends on !SCHED_CLASS_EXT`。sched_ext 侧的难点是：BPF 调度器必须知道当前 rq 上「调度的是谁、执行的是谁」，被保留的 blocked donor 归谁管、迁移与唤醒怎么记账。系列的做法是先让 sched_ext 全面改用 `rq->donor` 做策略与记账（14/18 用八种 donor/curr/competing 组合把语义穷举了一遍），再引入 `SCX_OPS_ENQ_BLOCKED` 让 BPF 调度器显式选择接管 blocked donor，最后（18/18）删掉 Kconfig 互斥。

## 技术方案

本日没有出现新方案，讨论集中在三处实现细节的辩护与让步（完整设计见 related_articles）：

- **02/18 `sched/core: Dequeue waking proxy donors before reset`**：作者解释了为什么必须先做调度类出队、再 `proxy_reset_donor()`。链条是 `proxy_reset_donor() → put_prev_set_next_task() → put_prev_task_scx() → scx_do_enqueue_task() → ops.enqueue()`：如果 `proxy_reset_donor()` 先跑，此时 `SCX_TASK_QUEUED` 与 `p->is_blocked` 仍置位（`__clear_task_blocked_on()` 只清 blocked_on 关系，`is_blocked` 要到 `ttwu_do_wakeup()` 才清），`put_prev_task_scx()` 会走 retained-blocked-donor 路径把 donor 重新入 DSQ，随后 `block_task()` 立刻又把它 dequeue 掉。同时 `dequeue_task_scx()` 必须在 `rq->donor == p` 时运行才能识别 p 是当前调度上下文、发出正确的 stopping 转换并清 `SCX_TASK_QUEUED`。作者强调这是「重置被保留 donor」的特例，不是一条通用的 `dequeue_task_scx()` 必须先于 `put_prev_task_scx()` 的规则。
- **12/18 `sched_ext: Generalize the reject DSQ reenqueue path`**：Tejun 的 nit 全部接受（按其要求把 `SCX_TASK_REENQ_REASON_MASK` 的清理收敛到统一出口标签、去掉多余花括号）。
- **17/18 `sched_ext: scx_qmap: Add proxy execution support`**：作者承认 Richard 的竞态判断成立——`cmask_next_and_set_wrap()` 返回的 cid 在「交集检查」与「取 cid」之间掩码可能已变，因此该 cid 在传给 `needs_immed()` 或编码进 local DSQ id 之前必须做边界校验。但在「要不要加序列化」上他明确保留意见：不需要，若所有权在校验之后才变化，由核心的 capability 校验兜住竞态、拒绝并重排该任务即可。

## 版本演进与当前进展

- v13 于 2026-08-31 21:42 发出（cover `<20260831134338.1531664-1-arighi@nvidia.com>`，18 补丁），09-01 起 Tejun/Prateek/Richard 陆续给意见，09-04 之前的状态是「三条提问无人应答 + 等 Peter 表态」。
- 09-08 16:02 Peter Zijlstra 在 PATCHSET v13 总帖下回帖："I'll try and have a look at things this week -- on a very cursory look they do indeed seem fine."（回复对象是 Tejun 的 `<apn6AdgyTr0btXDS@slm.duckdns.org>`）。
- 09-08 17:28 / 17:34 / 17:42 作者分别回掉 02/18（Prateek）、12/18（Tejun）、17/18（Richard）三条线，承诺的改动包括：去掉多余的 `reset_donor` 变量、把顺序要求写进注释、扩充 patch description 说明 sched_ext 特有的排序、给 qmap 加 cid 边界校验并把现有 rescue placement 抽出来复用。
- 本日没有 v14，也没有 tip-bot / stable 回帖。

## Maintainer 意见与讨论焦点

- **Peter Zijlstra**：首次松口，但措辞是"cursory look"且承诺"this week"——不构成 Ack。他的态度之所以关键，是系列大量改动落在 `kernel/sched/core.c` 与代理执行通用路径上，sched_ext 树的维护者无法独自放行。
- **Tejun Heo**：12/18 的 nit 被全额接受，属于可机械收敛的分歧，无残留。
- **K Prateek Nayak**：他在 09-01 提出的两个问题（是否真需要暂存 `reset_donor`；`dequeue_task_scx()` 是要正确 `rq->donor` 引用，还是 ext 永远要求先于 `put_prev_task_scx()`）本日得到完整答复，其中一半被作者确认为可简化（去掉暂存变量）、一半被反驳为「仅限重置被保留 donor 的特例」。这是本日最有信息量的一段——它把「顺序要求到底是不是全局不变式」讲清楚了，也意味着 commit message 需要重写以避免读者把它当成通用规则。
- **Richard Cheng**：17/18 的 cid 竞态质疑成立；但作者反对引入序列化，主张靠既有的 capability 校验拒绝并重排来兜住。**这是唯一残留的技术分歧点**：如果 cid 越界校验通过之后所有权才易手，是否真的一定会走到「拒绝并重排」而不是把任务放进一个它没有权限的 local DSQ，邮件里没有论证，只有断言。

## 合入评估

`likelihood=medium`（趋势向好）。理由：三条实质 review 全部有答复且已明确要改的东西，Peter 给出初步正面观感，18/18 解除 Kconfig 互斥这种收口补丁也已带 `Acked-by: John Stultz`；同时 15/18 的 `SCX_OPS_ENQ_BLOCKED` 契约、13/18 里"没有这些改动时 `stress-ng --pipeherd` 可以触发竞态并迁移活跃执行上下文，导致 sleeping-while-atomic 告警和随后的 lockdep 破坏"都说明系列自带的验证不是空的。卡点：其一，Peter 尚未真正评审，而他说的是"这周看"；其二，作者承诺的改动尚未成帖（需要 v14）；其三，17/18 的「不引入序列化」论证还缺一环。`next_action`：出 v14（清 nit、加 cid 边界校验、重写 02/18 说明与注释、带上已获得的 tag），然后等 Peter 的正式评审意见；若进入排队，18/18 应是最后合入的一片。

## 效果评估

- 09-08 全天没有任何新数据——Peter 的"seem fine"是浏览代码后的主观判断，未跑测试；作者三封回帖同样只有代码层面的论证。
- 系列侧已有的量化证据来自 13/18 的提交说明：`stress-ng --pipeherd` 在没有该补丁且开启代理执行时可触发竞态，产生 sleeping-while-atomic 告警与随后的 lockdep 破坏（这是缺陷复现，不是性能数字）；16/18 新增的 `enq_blocked` selftest 会统计每 CPU 的 blocked-donor 入队次数并报告互斥锁平均持有/等待时间，但邮件里没有给出运行结果。

## 我可以参与的点

- `review`：17/18 上唯一残留的分歧可以直接跟进——把 qmap 里 cid 校验之后所有权易手的情形走一遍代码，确认 capability 校验是否覆盖所有出口；若发现漏口，这比作者那句"should handle the race"更值得回帖。
- `testing`：16/18 的 `enq_blocked` selftest 需要 `CONFIG_SCHED_PROXY_EXEC=y` + `CONFIG_EXPERT=y`，且 17/18 给 scx_qmap 加了 `-X` 选项。任何人可以在自己的机器上跑一遍并回帖 `nr_enq_blocked` 计数与互斥等待时间，这正好补上本日完全空缺的效果证据。
- `discussion`：Peter 说本周看，若 v14 出现新问题，把 02/18 那段「只有重置被保留 donor 时才要求先 `dequeue_task_scx()`」的结论提炼成一条对 `task_tick`/`put_prev` 顺序不变式的文档化说明，可减少后续同类讨论成本。

## 参考链接

- v13 cover: https://lore.kernel.org/all/20260831134338.1531664-1-arighi@nvidia.com/
- Peter Zijlstra 的初步表态: https://lore.kernel.org/all/20260908080206.GL4121339@noisy.programming.kicks-ass.net/
- 作者对 02/18 顺序问题的答复: https://lore.kernel.org/all/ap_VIJdG80ZZ_8D0@gpd4/
- 作者对 12/18 nits 的确认: https://lore.kernel.org/all/ap_WmoSlrAYbJglk@gpd4/
- 作者对 17/18 CID 竞态的答复: https://lore.kernel.org/all/ap_YneRnbmk_ZYeQ@gpd4/
- Prateek 09-01 的原始追问: https://lore.kernel.org/all/3d4116ff-0634-4ab6-be24-0bd2c68f1698@amd.com/
- tip-bot commit: 未获取到
- stable backport: 未获取到

---
id: sched-20260908-003
date: '2026-09-08'
subject: 'sched: Make proxy execution compatible with sched_ext'
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: <20260831134338.1531664-1-arighi@nvidia.com>
lore_url: https://lore.kernel.org/all/20260908080206.GL4121339@noisy.programming.kicks-ass.net/
upstream_commit: null
fixes_commit: null
merged_branch: null
current_version: v13
generated_at: "2026-09-09T00:40:00"
authors:
- Andrea Righi
maintainers_involved:
- Peter Zijlstra
- Tejun Heo
- K Prateek Nayak
patch_series:
- version: v13
  msgid: <20260831134338.1531664-1-arighi@nvidia.com>
  date: '2026-08-31'
  summary: 18 补丁：sched_ext 全面改用 rq->donor 做策略与记账、新增 SCX_OPS_ENQ_BLOCKED 让 BPF 调度器接管 blocked donor、scx_qmap 与 enq_blocked selftest 跟进，最后解除 SCHED_PROXY_EXEC 与 SCHED_CLASS_EXT 的 Kconfig 互斥。
  review_outcome: '09-08: Peter Zijlstra 首次表态（本周评审，粗略看没问题）；作者集中回掉 Prateek（02/18 顺序）、Tejun（12/18 nits）、Richard（17/18 CID 竞态）三条线，承诺 v14 收敛。'
merge_assessment:
  likelihood: medium
  blocking_issues:
  - Peter Zijlstra 只给出 cursory 印象并承诺本周细看，系列大量改动在 kernel/sched/core.c，需要他的正式意见
  - 作者承诺的改动（去 reset_donor 暂存变量、cid 边界校验、重写 02/18 说明与注释、Tejun 的集中清理）尚未成帖，需要 v14
  - 17/18 上「不引入序列化、靠 capability 校验拒绝重排来兜竞态」的论证只有一句断言，未覆盖校验后所有权才易手的情形
  next_action: 出 v14 落实已承认的改动并携带已获得的 tag，随后等 Peter 正式评审；18/18 解除构建互斥应作为最后合入的一片
contribution_opportunities:
- kind: review
  description: 核对 17/18 qmap 中 cid 边界校验通过之后所有权易手时，是否一定被核心 capability 校验拒绝并重排，找出可能的越界/错放 DSQ 出口
- kind: testing
  description: 在 CONFIG_SCHED_PROXY_EXEC=y + CONFIG_EXPERT=y 下跑 16/18 新增的 enq_blocked selftest 与 scx_qmap -X，回帖 nr_enq_blocked 计数与互斥持有/等待时间，补齐本日完全缺失的效果数据
- kind: discussion
  description: 把 02/18 讨论出的「仅重置被保留 donor 时要求 dequeue_task_scx() 先于 put_prev_task_scx()」结论整理为顺序不变式说明，减少 v14 之后的重复讨论
source_email_count: 4
related_articles:
- sched-20260904-007
- sched-20260904-008
- sched-20260831-001
tags:
- sched_ext
---
