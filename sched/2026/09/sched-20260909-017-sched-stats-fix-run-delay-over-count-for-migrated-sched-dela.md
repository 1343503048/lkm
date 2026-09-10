# sched/stats: Fix run_delay over-count for migrated sched_delayed tasks

## TL;DR

Wei Yang（腾讯，邮件显示名 `albin_yang@163.com`）09-09 21:33 发出的单行修复：在 `DELAY_DEQUEUE` 下，一个正在睡觉（`se.sched_delayed`）的任务被普通迁移路径搬走时，`sched_info_enqueue()` 会把 `last_queued` 重新设成迁移时刻，于是真正唤醒时无法再复位，整段睡眠时间被折叠进 `run_delay`。修法是给这个重新设值加一个 `!t->se.sched_delayed` 条件，`Fixes: 152e11f6df29`（实现 delayed dequeue 的那枚）。我核对了本地主线：`kernel/sched/stats.h:293` 仍是 `if (!t->sched_info.last_queued)`，没有 `sched_delayed` 判断，问题存在。当天无人回帖。

## 背景与问题

`sched_info.run_delay` 是任务等待运行的累计时间，暴露给 `/proc/<pid>/sched` 与 `sched_debug`。正常睡眠路径下 `DELAY_DEQUEUE` 让阻塞任务仍留在 runqueue 上（`se.sched_delayed` 置位），同时 `sched_info.last_queued` 被清掉，因此这段睡眠不计入 `run_delay`——这是设计意图。

缺陷出现在「睡眠中的 delayed 任务被迁移」这一交叉路径。走 `move_queued_task()` / `move_queued_task_locked()`（后者被 `__migrate_swap_task()` 使用）时，目标 CPU 上的 `activate_task(dst, 0)` 会调用 `enqueue_task()` 且**不带 `ENQUEUE_RESTORE`**，于是 `sched_info_enqueue()` 看到 `last_queued == 0`，把它设成迁移时刻。等到真正唤醒（带 `ENQUEUE_DELAYED`）时，`sched_info_enqueue()` 因为 `last_queued` 已经非 0 而**跳过复位**，`sched_info_arrive()` 于是把「迁移到唤醒之间」的整段睡眠时间算成 run_delay。结果是一个纯统计错误：`run_delay` 被系统性高估，且高估的量正好等于该任务睡眠时长。

## 技术方案

```c
 static inline void sched_info_enqueue(struct rq *rq, struct task_struct *t)
 {
-	if (!t->sched_info.last_queued)
+	if (!t->sched_info.last_queued && !t->se.sched_delayed)
 		t->sched_info.last_queued = rq_clock(rq);
 }
```

`kernel/sched/stats.h | 2 +-`，1 file changed, 1 insertion(+), 1 deletion(-)。

作者对副作用范围的论证是这段的关键，也写得比较清楚：真正的唤醒路径会在到达 `sched_info_enqueue()` 之前清掉 `sched_delayed`，所以它仍然会在真实唤醒时刻复位 `last_queued`；普通可运行任务不受影响；负载均衡的迁移也不受影响，因为 `sched_delayed` 的任务被排除在主动负载均衡之外。也就是说新条件只挡住了「睡眠中被人搬走」这一条路径上的重新设值。

值得注意的取舍是：作者选择**不把 delayed 任务的迁移计入 run_delay**，而不是反过来把 `last_queued` 更新为迁移时刻（后者会让 delayed 任务的睡眠开始出现在统计里）。两种都能自圆其说，前者保持了「delayed 睡眠不算等待」的既有语义，代价更小。

## 版本演进与当前进展

v1，09-09 21:33 发出（`<20260909133345.1572954-1-albin_yang@163.com>`），`From: Wei Yang <albinwyang@tencent.com>`。当天无人回帖（发出时间 21:33，剩余窗口很短），无 tip-bot、无 stable。

## Maintainer 意见与讨论焦点

未获取到——v1 刚发出，无 review。可以在意的三点：

1. **没有 `Reported-by`，也没给可观测实例**。整条描述是代码路径推演，看不出是自己在真实机器上观察到 `run_delay` 异常，还是纯静态审查发现。前者通常会有 trace 或 `/proc/sched` 数字，后者往往就停在文字层面。这直接影响维护者把它排在 urgent 还是常规窗口。
2. **`__migrate_swap_task()` 这条路径被点名，但没有测试**。`move_queued_task_locked()` 用于 `MIGRATION_SWAPER`，需要用户态主动 `migrate_swap()`（典型使用者是 mm 相关的换出/换入实验），比 `move_queued_task()` 冷得多。也就是说这条更隐蔽的触发路径目前没有验证。
3. **修复点位置是否最合适**。`sched_info_enqueue()` 现在同时读 `rq` 与 `se.sched_delayed`，即 sched stats 层直接依赖 fair 层的 delayed-dequeue 状态位。这与 09-09 另一条讨论（`nr_pref_llc_running` 与 `h_nr_queued` 的口径之争，见 sched-20260909-015）实际上是同一类问题：`DELAY_DEQUEUE` 之后，凡是拿「排队/运行」计数或时间戳做判断的地方都得重新对齐一次口径。这个补丁是这一系列对齐工作中最新的一枚。

## 合入评估

`likelihood=medium`。有利：`Fixes:` 精确指向 `152e11f6df29 ("sched/fair: Implement delayed dequeue")`，改动面是 1 行且逻辑单向（只会少设一次时间戳），作者对不影响的三类路径给了明确理由。这类统计正确性修复通常被调度器维护者接受得比较爽快。不利：当天零 review，没有可观测实例，而它修的是一个统计量而非行为，很容易被放到「有空再看」那一堆里。

`next_action`：等 review；若有人能给出一个 `run_delay` 明显被高估的实测（delayed 任务 + `move_queued_task`），它会立刻从「文字推演」升级为可定级的 bug 修复。

## 效果评估

无数据。没有 `run_delay` 的改前/改后读数，没有说明受影响负载的形态与偏差量级。按代码推演，偏差等于「delayed 任务从被迁移到真正唤醒之间的整段睡眠时间」，这个上界可以很大（分钟级的睡眠），但邮件里没有实测支持，属作者的机制论证而非效果证明。

## 我可以参与的点

- `testing`：这是当天最容易做出实证的一条。写一个小用例：让一个任务长时间睡眠（保证它以 `sched_delayed` 留在 rq 上），期间从另一 CPU 触发 `move_queued_task()`（`MIGRATION_SWAPER` 路径可用 `migrate_swap()` 系统调用），对比 `/proc/<pid>/sched` 里 `run_delay` 与真实 runnable 等待时间。有 `CONFIG_SCHED_CORE`/`migrate_swap` 权限的环境就能做，做完把数字贴到线程里就是这条补丁最缺的东西。
- `review`：顺着 `DELAY_DEQUEUE` 把其它读 `nr_running` / 时间戳 / 计数的地方扫一遍（`sched_info_*`、`avg_idle`、`nr_pref_llc_running`、`h_nr_runnable`），确认是否还有同类「delayed 任务被算成等待或被漏算」的地方。本线程与 sched-20260909-015 的争议都源于同一个缺口，这类横向检查通常能直接产出后续补丁。
- `discussion`：可以问清作者这是静态审查还是实测发现；若是实测，请他把数据贴出来；若是静态审查，则建议明确说明，因为这会影响维护者的定级。
- `new_patch`：`Fixes: 152e11f6df29` 意味着凡是回合过 delayed dequeue 的分支都受影响；OLK 6.6 类分支若含该特性，这枚单行修复适合回合，但 `Fixes` 需指向自家分支中引入 delayed dequeue 的 commit 而不是上游 hash。

## 参考链接

- v1 邮件: https://lore.kernel.org/all/20260909133345.1572954-1-albin_yang@163.com/
- `Fixes` 目标 `sched/fair: Implement delayed dequeue`（152e11f6df29）: https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=152e11f6df29
- 同一 DELAY_DEQUEUE 口径问题的另一条讨论线: https://lore.kernel.org/all/aqFFu1Xo52cQV3iy@fengwei-dev/
- tip-bot commit: 未获取到
- stable backport: 未获取到

---
id: "sched-20260909-017"
date: "2026-09-09"
subject: "sched/stats: Fix run_delay over-count for migrated sched_delayed tasks"
subsystem: sched
type: bug
status: under_review
severity: low
thread_root_msgid: "<20260909133345.1572954-1-albin_yang@163.com>"
lore_url: "https://lore.kernel.org/all/20260909133345.1572954-1-albin_yang@163.com/"
upstream_commit: null
fixes_commit: "152e11f6df29"
merged_branch: null
current_version: v1
generated_at: "2026-09-10T01:15:00"
authors:
  - "Wei Yang"
maintainers_involved: []
patch_series:
  - version: v1
    msgid: "<20260909133345.1572954-1-albin_yang@163.com>"
    date: "2026-09-09"
    summary: "sched_info_enqueue() 增加 !t->se.sched_delayed 条件，避免睡眠中的 delayed 任务被 move_queued_task()/move_queued_task_locked() 迁移时把 last_queued 设成迁移时刻，从而防止真正唤醒时无法复位、整段睡眠被计入 run_delay；1 file changed, 1 insertion(+), 1 deletion(-)。"
    review_outcome: "v1 于 21:33 发出，当天无人回帖，无 Ack 无 NAK，无 tip-bot 收录。"
merge_assessment:
  likelihood: medium
  blocking_issues:
    - "零 review：发出时间为当天 21:33，几乎没有回帖窗口"
    - "无 Reported-by 与可观测实例，未说明是静态代码审查还是实测发现，影响定级"
    - "被点名的 __migrate_swap_task() 冷路径无测试覆盖"
    - "修复使 kernel/sched/stats.h 直接依赖 fair 层的 se.sched_delayed，该分层依赖是否合适无人评价"
  next_action: "等 review；或由人补一份 run_delay 被高估的实测数据，并说明这是静态审查还是实测发现"
contribution_opportunities:
  - kind: testing
    description: "构造长睡眠的 delayed 任务并在睡眠期用 migrate_swap() 触发迁移，比对 /proc/<pid>/sched 的 run_delay 与真实等待时间，为补丁补上目前完全缺失的实测证据"
  - kind: review
    description: "横向排查其它在 DELAY_DEQUEUE 下读 nr_running、时间戳或计数的位置（sched_info_*、avg_idle、nr_pref_llc_running、h_nr_runnable），确认是否还有同类漏算或重复计数"
  - kind: discussion
    description: "向作者确认这是静态审查还是实测发现；若为实测请其贴出数据，若为静态审查则建议在 commit message 中写明，以便维护者定级"
  - kind: new_patch
    description: "回合过 delayed dequeue 的分支（如 OLK 6.6）均受影响，适合直接回合这枚单行修复，Fixes 需指向自家分支引入该特性的 commit 而非上游 152e11f6df29"
source_email_count: 1
related_articles:
  - "sched-20260909-015"
tags:
  - "cfs"
  - "sched_debug"
---
