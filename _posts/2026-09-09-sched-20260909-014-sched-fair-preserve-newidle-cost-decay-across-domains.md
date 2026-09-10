---
id: sched-20260909-014
date: '2026-09-09'
subject: 'sched/fair: Preserve newidle cost decay across domains'
subsystem: sched
type: bug
status: under_review
severity: medium
thread_root_msgid: 20260909094523.2314-1-lirongqing@baidu.com
lore_url: https://lore.kernel.org/all/20260909094523.2314-1-lirongqing@baidu.com/
upstream_commit: null
fixes_commit: e60b56e46b38
merged_branch: null
current_version: v1
generated_at: '2026-09-10T01:05:00'
authors:
- Li RongQing
maintainers_involved: []
patch_series:
- version: v1
  msgid: 20260909094523.2314-1-lirongqing@baidu.com
  date: '2026-09-09'
  summary: sched_balance_domains() 遍历调度域时 need_decay 由逐次赋值改为按位累积（= 改 |=），使任一域报告的 decay
    都能触发循环外 rq->max_idle_balance_cost 的更新；1 file changed, 1 insertion(+), 1 deletion(-)。
  review_outcome: v1 刚发出，当天无人回帖，无 Ack 无 NAK，也未见 tip-bot 收录。
merge_assessment:
  likelihood: medium
  blocking_issues:
  - 无任何 review 或维护者表态，单行无数据的调度器修复易被淹没
  - commit message 未说明失效后的可观测后果（max_idle_balance_cost 长期不衰减会怎样改变 newidle balance 行为）
  - 同一变量在循环内承担「当前域是否 decay」、在循环外承担「是否有域 decay」，语义混合且缺注释
  next_action: 等 review；或由人回帖追问受影响拓扑与负载特征，最好附 max_idle_balance_cost 不衰减的实测证据，同时建议拆成两个变量并清理重复的
    commit message 段落
contribution_opportunities:
- kind: testing
  description: 在多层调度域机器上用 /proc/sched_debug 观察 max_idle_balance_cost 与各 sd 值，对比补丁前后是否从长期贴在上界转为正常衰减，补上缺失的后果证据
- kind: review
  description: 建议拆成两个变量分别表达当前域 decay 与本次遍历是否有域 decay，避免 |= 后语义混合；并删掉 commit message
    结尾重复的一段
- kind: new_patch
  description: 含 e60b56e46b38 或其等价改动的自家分支可直接回合，Fixes 需指向自家引入该赋值形式的 commit 而非上游 hash
source_email_count: 1
related_articles: []
tags:
- load_balance
- topology
title: 'sched/fair: Preserve newidle cost decay across domains'
layout: article
---

## TL;DR

Li RongQing（百度）09-09 17:45 发出的单行修复：`sched_balance_domains()` 里 `need_decay` 在遍历调度域的循环中被**逐次赋值**而非累积，于是前面某个域报告的 decay 会被后面不需要 decay 的域覆盖掉，导致本应更新的 `rq->max_idle_balance_cost` 被跳过。修法就是把 `=` 换成 `|=`，`Fixes: e60b56e46b38`。我在本地主线（v7.0-rc 树）核对过，`kernel/sched/fair.c:13784` 处仍是 `need_decay = update_newidle_cost(sd, 0, 0);`，问题依旧存在。当天无人回帖。

## 背景与问题

`rq->max_idle_balance_cost` 是 newidle balance 的时间预算参考：它由各调度域的 `sd->max_newidle_lb_cost` 汇总而成，并在观察到「这次真的 decay 了 newidle 成本」时才更新（并夹到不低于 `sysctl_sched_migration_cost`）。这个聚合语义在 `e60b56e46b38 ("sched/fair: Wait before decaying max_newidle_lb_cost")` 之前是成立的——那次改动把 `update_newidle_cost()` 变成有返回值、并按域决定是否 decay，但循环里 `need_decay` 被改成了直接赋值，把「任一域 decay 就要更新 rq 级值」变成了「最后一个域说了算」。

失效条件很朴素：多层拓扑（典型如带 SMT / MC / DIE / NUMA 多个域的服务器）下，只要**最后一个被遍历的域**不需要 decay，前面任何域报告的 decay 都会被抹掉，`rq->max_idle_balance_cost` 就停止衰减。

## 技术方案

```c
-		need_decay = update_newidle_cost(sd, 0, 0);
+		need_decay  |= update_newidle_cost(sd, 0, 0);
```

`need_decay` 声明处已是 `int need_decay = 0;`（主线 `kernel/sched/fair.c:13775`），改成按位累积后循环退出值就是「本次遍历是否有任何域 decay」。作者刻意不动 `update_newidle_cost()` 本身，也不动循环内 `if (!continue_balancing) { if (need_decay) continue; break; }` 的判定——那里读的是**当前域**的值，语义上正好与累积后的循环外读取区分开，`|=` 不会破坏它（`continue_balancing` 为假时，当前域返回 0 仍会 break 出去，与原行为一致）。

`kernel/sched/fair.c | 2 +-`，1 file changed, 1 insertion(+), 1 deletion(-)。

顺带一提：commit message 结尾两段有重复——"This restores the aggregate semantics of need_decay and ensures rq->max_idle_balance_cost is updated..." 与紧随其后的 "This restores the aggregate semantics of need_decay that existed before e60b56e46b38 and ensures..." 说的是同一件事，只差一个 `that existed before e60b56e46b38`。这种重复在同为注释修正类的今天另一篇里也被社区在意（见 sched-20260909-002 就是专门修重复词的），值得顺手清理。

## 版本演进与当前进展

v1，09-09 17:45 发出（`<20260909094523.2314-1-lirongqing@baidu.com>`），`From: Li RongQing <lirongqing@baidu.com>`。当天邮件里无人回帖，无 tip-bot、无 stable。

## Maintainer 意见与讨论焦点

未获取到——v1 刚发出，尚无人表态。可作为权重的事实是：`Fixes:` 指向的 `e60b56e46b38` 是 Peter Zijlstra 的提交，而本次是把它引入的行为回归恢复回去；改动是单行、纯保守方向（只会让 `rq->max_idle_balance_cost` 更常更新，不会让它少更新）。

讨论里目前缺的两块（不是分歧，是还没人问/没人答）：

1. **触发后的可观测后果没写**。commit message 只说「rq 级更新被跳过」，没有说明这会让 newidle balance 在真实负载上变成什么样——`max_idle_balance_cost` 长期不衰减会偏向多做还是少做 newidle balance，邮件里没有推演也没有数据。
2. **循环内 `continue_balancing` 分支的交互没有展开**。`if (need_decay) continue; break;` 依赖当前域的返回值，`|=` 之后变量含义从「当前域」悄悄变成「当前域或之前任一域」的混合体——虽然该分支在赋值语句之后立即读取、此时累积值等价于当前域值，但这个不变式很脆弱，值得有人提一句是否该用两个变量分开表达。

## 合入评估

`likelihood=medium`。理由：这是明确的回归修复，有 `Fixes` 指向具体提交，改动面极小且方向保守（不存在性能回退的新风险面），作者是有长期上游记录的贡献者。卡点完全是流程性的——单行、无数据、无复现描述的调度器修复很容易被淹没，通常需要有人回帖追问「什么负载会看到影响」才能被定级。

`next_action`：等 review；或有人回帖问清受影响条件（拓扑层级数、last-domain 是否总为 SMT 之类），必要时补一个能观测到 `rq->max_idle_balance_cost` 长期不下降的场景。

## 效果评估

无。邮件里没有 benchmark、没有 `rq->max_idle_balance_cost` 的实际取值曲线、没有指出哪个负载会因这个 bug 出现迁移行为偏移。「恢复聚合语义」这一点在代码层面是可验证的（我已核对主线仍是赋值），但**由此带来的行为差异大小完全未量化**，属作者对正确性的论证而非效果证明。

## 我可以参与的点

- `testing`：这类「统计量不再更新」的 bug 最容易给出增量证据——在多层拓扑机器上（`/proc/sched_debug` 里能看到 `max_idle_balance_cost` 与各 `sd->max_newidle_lb_cost`）跑混合突发型负载，对比打补丁前后 `max_idle_balance_cost` 随时间的走向。若能看到它长期贴着上界不衰减、打完补丁后正常衰减，就直接补上了 commit message 缺的那块后果描述。
- `review`：可以建议作者用两个变量分别表达「当前域是否 decay」（循环内 break 判定用）与「本次遍历是否有域 decay」（循环外更新用），避免 `|=` 之后同一变量承担两种语义；顺带删掉重复的那段 commit message。
- `new_patch`：自家分支若包含 `e60b56e46b38` 或其等价改动，这条修复适合直接回合；按 OLK 规范 `Fixes` 需指向自家分支中引入该赋值形式的那枚 commit，而不是上游 `e60b56e46b38`。

## 参考链接

- v1 邮件: https://lore.kernel.org/all/20260909094523.2314-1-lirongqing@baidu.com/
- `Fixes` 目标 `sched/fair: Wait before decaying max_newidle_lb_cost`（e60b56e46b38）: https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=e60b56e46b38
- tip-bot commit: 未获取到
- stable backport: 未获取到
