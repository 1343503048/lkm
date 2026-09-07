---
id: sched-20260902-007
date: '2026-09-02'
subject: 'sched/fair: Rework/fix task_h_load()'
subsystem: sched
type: fix
status: under_review
severity: high
thread_root_msgid: <20260828075558.660152190@infradead.org>
lore_url: https://lore.kernel.org/all/20260828075558.660152190@infradead.org/
upstream_commit: null
fixes_commit: null
merged_branch: null
current_version: v1
generated_at: '2026-09-07'
authors:
- Peter Zijlstra
maintainers_involved:
- Peter Zijlstra
- Vincent Guittot
- Chen Yu
patch_series:
- '[PATCH 4/4] sched/fair: Rework/fix task_h_load()'
merge_assessment:
  likelihood: high
  blocking_issues:
  - Peter 只说 "I'll fold it in"，9/2 之后未重发版本、也无 tip-bot 合入通告
  - Vincent 指出遍历同样 clobber se，建议 save pse = p->se，尚未落地
  - '是否需要 Fixes: 标签 / 是否该走 sched/urgent 无人提出'
  - 1/4 - 3/4 当日无人评审
  next_action: 等作者重发包含 fixlet 与 pse 处理的版本；期间可提交 for_each_sched_entity_bl() 调用点的 clobber
    审计
contribution_opportunities:
- 审计 for_each_sched_entity_bl() 全部调用点在遍历后是否继续使用被改写的 se/cfs_rq
- 回答 for_each_sched_entity_bl() 是否要求从 root cfs 起遍历这一前置条件
- 在大核数物理机上扩大 crash 复现面，确认虚拟机是否掩盖同类问题
- 评审该 4 补丁系列中当日无人讨论的 1/4 - 3/4
source_email_count: 6
related_articles: []
tags:
- sched/fair
title: 'sched/fair: Rework/fix task_h_load()'
layout: article
---

## TL;DR

Peter Zijlstra 8/28 那个 4 补丁系列里的 `4/4` 重做了 `task_h_load()`，9/2 Chen Yu 报告整套（内核
`7.3.0-rc1-flat-hload+`）在 192 核机器上**启动即 panic**（`RIP: 0010:pick_task_fair+0x43/0xd0`）。Peter
当天定位到根因：`set_next_task_fair()` 里 `for_each_sched_entity_bl()` 会破坏 `cfs_rq`（以及 `se`），
导致随后 `cfs_rq->curr = se;` 写到中间层 cfs_rq 上。他给了两版移动遍历位置的 fixlet，Vincent Guittot
确认 "Yes, this fixes it for me too" / "should work too"，Peter 说 "I'll fold it in"。方案已定，缺的只是
作者把 fixlet 折回去重发。

## 背景与问题

`task_h_load()` 计算任务沿 cgroup 调度层级的「层级负载」。旧实现依赖 `for_each_sched_entity()` 遍历时
顺带设置的 backlink，而 `__update_blocked_fair()` 这类调用方走的是 `leaf_cfs_rq_list`、不做逐级上溯，
所以 `4/4` 的 rework 把层级信息参数化（两个允许为 NULL 的参数，见 [[sched-20260831-003]]）。

rework 引入的 `for_each_sched_entity_bl(se, cfs_rq)` 是个会**改写循环变量**的遍历宏：`se` 会走到层级
顶端、`cfs_rq` 同步被改掉。把它放进 `set_next_task_fair()` 之后，函数后半段继续使用的就是被改坏的值。

Chen Yu 给出的现场（`body_stripped` 原文摘录）：启动阶段 `systemd-udevd` 走
`ksys_setsid -> sched_autogroup_create_attach -> autogroup_move_group -> _raw_spin_unlock_irqrestore
-> preempt_schedule -> __schedule -> __pick_next_task -> pick_task_fair`，
`Oops: general protection fault, kernel NULL pointer dereference 0x69`。

## 技术方案

Chen Yu 的根因分析（原文）：

```
After the following top->down backlink traverse,
for_each_sched_entity_bl(se, cfs_rq)
    update_cfs_rq_h_load(group_cfs_rq(se), se, cfs_rq);

cfs_rq is not the root->cfs_rq anymore, but a middle cfs_rq(autogroup
in above example). Meanwhile rq->cfs.curr remains NULL because the
rq->cfs.curr has been dequeued if the task is runnable and queued:
if (on_rq)
	__dequeue_entity(cfs_rq, se)

se = &p->se;
cfs_rq->curr = se; /*wrong cfs_rq*/
```

即 `pick_eevdf()` 在错误的（中间层、空树）cfs_rq 上返回 NULL，`se->sched_delayed` 读空指针。他建议的修法是
遍历后显式恢复：`se = &p->se; cfs_rq = &rq->cfs; cfs_rq->curr = se;`。

Peter 确认的是同一个机制，但承认是自己读错了语义："I think I misread the `se = &p->se; cfs_rq->curr = se;`
to reset both se and cfs_rq, but clearly it doesn't."，并回忆同类问题早前在 `task_tick_fair()` 已修过一次
（"where `for_each_sched_entity_bl()` clobbered `cfs_rq`, and fixed that by moving things after
`reweight_eevdf()`"）。他没有采纳「恢复 `cfs_rq`」，而是选择**把遍历挪到函数尾部**，先后两版：

- 第一版：把 `for_each_sched_entity_bl(...)` 从 `if (throttled) task_throttle_setup_work(p);` 之前移到
  `if (task_on_rq_queued(p))` 之前。
- 第二版（最终）：进一步把遍历移到 `list_move(&se->group_node, &rq->cfs_tasks);` 与
  `WARN_ON_ONCE(se->sched_delayed);` **之后**，并把 `if (!first) return;` 挪到遍历之后，
  使 `hrtick_start_fair()` 仍在 `!first` 早退之后。

Vincent 指出第二版仍有一处残余语义：遍历同样修改了 `se`，而 `se` 在下面被
`list_move(se->group_node, &rq->cfs_tasks)` 和 `WARN_ON_ONCE(se->sched_delayed)` 使用，
因此 "Might be good to save pse = p->se"，并追问 "Doesn't for_each_sched_entity_bl assume to start from
root cfs as well ?"。对第二版他仍给 "should work too"。他还补了一条重要触发条件：
"Some of my platforms didn't crash until I added +cpu in cgroup.sub_controller"。

## 版本演进与当前进展

- 8/28：Peter 发出 4 补丁系列；`4/4` 为 "sched/fair: Rework/fix task_h_load()"。`1/4`–`3/4` 的标题与正文
  未获取到（本地缺 2026-08-27 ~ 08-30 的缓存）。
- 8/31：Vincent 要求给两个可空参数补注释并表态 "the rework looks good to me"，Peter 给出注释稿，Vincent 提
  `s/then/when/`，Peter 接受；Vincent 同时说测试本周跑（[[sched-20260831-003]]）。
- 9/2 13:26 Chen Yu 报 panic + 根因 + 建议；15:55 Vincent "I faced the same crash while testing"；
  16:13 Peter 第一版 fixlet 并说 "Let me go and try and reproduce"；18:36 Peter 第二版 + "I'll fold it in"；
  18:37 Vincent 提 `pse` 意见；18:39 Vincent "should work too"。
- 版本仍是 v1。9/2 之后直到 9/7 缓存里该线程无新邮件，也没有对应的 tip-bot 合入通告。

## Maintainer 意见与讨论焦点

- **Chen Yu（Intel）**：唯一的问题报告者，给出了完整栈、机制解释和一种修法。他的 `cfs_rq = &rq->cfs` 方案未被
  采纳，Peter 用移动遍历位置替代。
- **Vincent Guittot（linaro，sched/fair 维护者）**：8/31 承诺的测试兑现了，且是独立复现者。三处实质意见是
  `se` 同样被 clobber（建议 `pse = p->se`）、`for_each_sched_entity_bl()` 是否隐含「必须从 root cfs 起」的前置
  条件、以及 `+cpu` 才触发这一触发条件细化。对两版 fixlet 都给了正向确认。
- **Peter Zijlstra（作者）**：两次自我归因（misread 了 `cfs_rq->curr = se` 的覆盖面、"clearly I missed one"）。
  复现环境上他遇到的是物理机/虚拟机差异："Weirdly that crash didn't show up for me :-(, I had a few others that
  I cured." 以及 "Different physical machine.. *splat*, virtual machine it lives. Argh I hate computers.
  Anyway, confirmed on physical machine that triggered it, the blow seems to cure things."
- 没有 NAK、没有备选方案之争；截至 9/7 线程里没有出现 `Reviewed-by`/`Acked-by`，也没有 `Fixes:` 标签。

## 合入评估

**likely**。补丁出自 sched 核心维护者本人，崩溃被 Chen Yu 与 Vincent 两人独立复现，Peter 的 fixlet 得到 Vincent
明确确认，讨论已收敛到「遍历放在哪一行」这种细节。卡点是流程性的：fixlet 只表示 "I'll fold it in" 到作者本地树，
9/2 之后既没有重发版本也没有进 tip 的通告；Vincent 点出的 `se` clobber 残余（是否引入 `pse = p->se`）需要在下
一个版本里落地；`1/4`–`3/4` 至今无人评审；是否需要 `Fixes:`、是否该走 `sched/urgent` 也还没人提。

## 效果评估

线程内没有任何 benchmark 数字，效果证据只有「崩溃消失」这一条：Chen Yu 的 192 核 GPF、Vincent 的
"I faced the same crash" -> "this fixes it for me too"，以及需要 `+cpu in cgroup.sub_controller` 才炸的那批平台
从无法启动到可启动。层级负载计算本身的正确性与负载均衡质量收益没有被量化——Vincent 8/31 说的 "looks good to me"
是代码审读判断。

## 我可以参与的点

- **把 Peter 没做完的审计做完**：`for_each_sched_entity_bl()` 的全部调用点，逐个检查遍历之后是否还继续使用
  `se`/`cfs_rq`。他自己承认 "clearly I missed one"，这类清单最容易由第三方补出来。
- **回答 Vincent 的前置条件问题**：`for_each_sched_entity_bl()` 是否隐含「必须从 root cfs 开始遍历」；如果是，
  应当在宏或注释里写明，而不是靠调用方自觉。
- **扩大复现面**：192 核物理机 + autogroup + `+cpu` 的门槛不低，手上有大核数机器的人回帖本身就是有效输入；
  顺带确认虚拟机会不会掩盖同类 bug（Peter 当天就踩了这个坑）。
- **看整个系列**：`1/4`–`3/4` 当日无人讨论；同时跟踪 flat-hierarchy 系列另一条独立故障
  `[BUG] sched/fair: divide error in __calc_prop_weight()`（除零类，参见 [[sched-20260819-001]]）。
- 对 OLK-6.6 回合判断：这条属于上游 flat-hierarchy/`h_load` 重构的自修过程，6.6 上没有 `for_each_sched_entity_bl()`
  与 `cfs_rq->h_curr` 这套基础设施，暂时无可回合；真正值得关注的是 `h_curr`/`h_load` 语义演进
  （[[sched-20260901-002]]），它会决定后续几年 cpuset/cgroup 场景下的负载估算口径。

## 参考链接

- 系列 cover：https://lore.kernel.org/all/20260828074059.232353141@infradead.org/
- `4/4` 原始补丁：https://lore.kernel.org/all/20260828075558.660152190@infradead.org/
- Chen Yu panic 报告与根因：https://lore.kernel.org/all/apezcsScwu5hdNrr@fengwei-dev/
- Vincent 独立复现：https://lore.kernel.org/all/CAKfTPtBNAGQUQZbaDKYU7+Nsrcnj4M4p=54XkeML7rrLy+x+ZQ@mail.gmail.com/
- Peter 第一版 fixlet：https://lore.kernel.org/all/20260902081301.GS4120091@noisy.programming.kicks-ass.net/
- Peter 第二版 fixlet（"I'll fold it in"）：https://lore.kernel.org/all/20260902103654.GB4121620@noisy.programming.kicks-ass.net/
- Vincent 的 `pse = p->se` 意见：https://lore.kernel.org/all/CAKfTPtA2Xew+F9EAbmyz8ke5vU9wNTLzi7h2rtFNZ2qYdUiGhA@mail.gmail.com/
- Vincent "should work too"：https://lore.kernel.org/all/CAKfTPtBcshM-BGr1qzfT233E3tr_bxZX6xkMTBjqdSKWFXz61A@mail.gmail.com/
- 相关：[[sched-20260831-003]]、[[sched-20260819-001]]、[[sched-20260901-002]]
