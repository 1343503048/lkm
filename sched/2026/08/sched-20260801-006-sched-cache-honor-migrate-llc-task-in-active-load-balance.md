---
id: sched-20260801-006
date: 2026-08-01
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: "<uid-14461@qq-imap>"
lore_url: unknown
authors: [Lu Wang]
maintainers_involved: []
current_version: v1
patch_series:
  - version: v1
    msgid: "<uid-14461@qq-imap>"
    date: 2026-08-01
    summary: "被动负载均衡把 group_llc_balance 标记为 migrate_llc_task 并排队 active balance，但 CPU stopper 回调会重建全新的 lb_env，migration_type 在异步边界上丢失。本 patch 在 rq 上新增 active_balance_type 字段把迁移类型带过异步边界；并在 LBF_ACTIVE_LB 快速路径上拒绝 preferred_llc 与目的 LLC 不匹配的候选任务"
    review_outcome: "当日刚发出，暂无 review 意见"
upstream_commit: null
fixes_commit: "e4c9a4cb244a"
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues: ["缺少任何效果数据或复现说明，未展示该 bug 造成的实际影响", "同一 patch 在 20:17 与 20:22 连发两封，可能存在重复投递或未标注的修订，需要作者澄清", "sched/cache（cache-aware scheduling）本身仍是较新的特性，其 maintainer 尚未表态"]
  next_action: "补充能说明问题的复现场景或数据；澄清重复投递；等待 cache-aware scheduling 方向的 reviewer（如 Chen Yu / Tim Chen）确认语义"
contribution_opportunities:
  - kind: testing
    description: "构造 cache-aware scheduling 开启且触发 active balance 的场景，用 tracepoint 验证修复前任务确实会被搬离其 preferred LLC、修复后不再发生——这正是该 patch 缺失的证据"
  - kind: review
    description: "核对在 LBF_ACTIVE_LB 快速路径上从无条件 return 1 改为 return !migrate_llc_task_wrong_dst(p, env) 是否会让某些本应成功的 active balance 变成空转，进而触发 balance 失败计数上升"
generated_at: "2026-08-02T00:55:00"
source_email_count: 2
related_articles: []
tags: [cfs, load_balance, topology]
---

## TL;DR

cache-aware scheduling 的 `migrate_llc_task` 迁移类型在被动负载均衡切换到 active balance 的异步边界上丢失了，导致 CPU stopper 可能把任务搬到它 preferred LLC 之外。Lu Wang 用一个 rq 字段把迁移类型传递过去并补上目的 LLC 校验。修复思路清晰，但完全没有提供复现或效果证据。

## 背景与问题

cache-aware scheduling（`sched_cache_enabled()`）引入了 `migrate_llc_task` 这种迁移类型，语义是「只把任务迁移到它 preferred LLC 所在的目的 CPU」。

问题出在被动均衡与主动均衡的交接处：

1. 一次被动负载均衡把 `group_llc_balance` 标记为 `migrate_llc_task`，但发现无法直接搬动任务，于是排队一次 active balance（`busiest->active_balance = 1`）。
2. active balance 由 CPU stopper 异步执行 `active_load_balance_cpu_stop()`，这个回调**构造了一个全新的 `lb_env`**，其中只填了 `src_cpu`/`dst_cpu`/`idle`/`flags` 等字段，`migration_type` 是缺省值。
3. 于是原本「只迁移到 preferred LLC」的约束在异步边界上**静默丢失**。

雪上加霜的是 `can_migrate_task()` 里对 active balance 有一条快速路径：`if (env->flags & LBF_ACTIVE_LB) return 1;`——无条件放行。这意味着即便迁移类型没丢，这条路径也不会去检查 LLC 匹配。两者叠加的后果是：active balance 可能把一个任务**搬离它的 preferred LLC**，与 cache-aware scheduling 的意图直接相悖。

`Fixes:` 指向 `e4c9a4cb244a ("sched/cache: Add migrate_llc_task migration type for cache-aware balancing")`，即引入该迁移类型的 commit 本身。

## 技术方案

三处改动，逻辑上是一条链：

**1. 把迁移类型带过异步边界**。在 `struct rq` 中新增 `active_balance_type` 字段；`sched_balance_rq()` 排队 active balance 时记录 `busiest->active_balance_type = env.migration_type`；`active_load_balance_cpu_stop()` 构造新 `lb_env` 时用 `.migration_type = (enum migration_type)busiest_rq->active_balance_type` 恢复。

**2. 抽出可复用的判定**。新增 inline helper：

```c
static inline bool
migrate_llc_task_wrong_dst(struct task_struct *p, struct lb_env *env)
{
	return sched_cache_enabled() &&
	       env->migration_type == migrate_llc_task &&
	       READ_ONCE(p->preferred_llc) != llc_id(env->dst_cpu);
}
```

`migrate_degrades_llc()` 中原有的同款内联条件被替换为对该 helper 的调用，属于纯重构；同时在 `CONFIG_SCHED_CACHE` 关闭的分支下提供返回 `false` 的空实现，保证不影响未开启该特性的构建。

**3. 收紧 active balance 快速路径**。`can_migrate_task()` 中 `if (env->flags & LBF_ACTIVE_LB) return 1;` 改为 `return !migrate_llc_task_wrong_dst(p, env);`。这是行为改变的关键点——active balance 不再无条件放行，而是会拒绝 preferred LLC 不匹配的候选。

改动规模：`fair.c` + `sched.h` 共 23 增 3 删。

## 版本演进与当前进展

v1 于 2026-08-01 发出，当日无 review 回复。

需要注意一个异常：同一主题、同一作者的邮件在 20:17（uid 14461）与 20:22（uid 14462）连续出现两封，间隔 5 分钟。从可获取的信息无法确定这是重复投递、还是第二封包含了未在标题中标注的修订。作者应当澄清这一点，否则容易让 reviewer 困惑。

## Maintainer 意见与讨论焦点

**暂无相关内容**——当日没有任何 review 回复，也没有 Cc 明确的 maintainer。

值得说明的背景是：cache-aware scheduling 是相对较新的特性，其语义细节（preferred LLC 的更新时机、与 active balance 的交互边界）仍在演化中。这类修复通常需要该方向的原作者或活跃 reviewer 来确认「丢失 migration_type 究竟是 bug 还是有意为之的降级行为」——存在一种可能：active balance 作为最后手段，被设计成故意忽略 LLC 偏好以保证均衡能推进。作者在 changelog 中把它当作明确的 bug 处理，但没有引用任何设计文档或讨论来支撑这个前提。

## 合入评估

合入可能性 **medium**。

**有利因素**：问题定位具体、`Fixes:` tag 指向明确、改动小且对 `CONFIG_SCHED_CACHE` 关闭时零影响、helper 抽取让代码更清晰。

**不利因素**：

1. **零证据**。没有复现步骤、没有 tracepoint 输出、没有性能数据，无法判断这个 bug 在实际负载下的影响程度，也无法验证修复确实生效。
2. **快速路径的行为改变需要论证**。把 `LBF_ACTIVE_LB` 从无条件放行改为有条件拒绝，可能让某些 active balance 变成空转（找不到可迁移任务），进而推高 balance 失败计数、影响后续的均衡决策。作者未讨论这个副作用。
3. **前提未经确认**。如前所述，active balance 忽略 LLC 偏好是否为有意设计，需要该方向的人确认。
4. **重复投递未澄清**。

## 效果评估

**暂无效果数据**。邮件中没有任何 benchmark、复现日志或 tracepoint 输出。「active balance 可能把任务搬离 preferred LLC」是从代码路径推导出的结论，逻辑上站得住，但属于**作者的代码分析，未见实测数据佐证**，也没有说明这在真实负载中出现的频率与代价。

## 我可以参与的点

- **测试（该 patch 最缺的东西）**：在开启 cache-aware scheduling 的机器上构造能触发 `group_llc_balance` → active balance 路径的负载，用 `sched_migrate_task` tracepoint 配合 `p->preferred_llc` 观测，验证修复前任务确实会被搬离 preferred LLC、修复后不再发生。把 trace 片段回帖到 thread，能直接把这个 patch 从「代码推导」提升到「有证据的修复」。
- **Review**：核对第 3 项改动的副作用——`can_migrate_task()` 在 `LBF_ACTIVE_LB` 下从 `return 1` 改为条件返回后，`active_load_balance_cpu_stop()` 若因此找不到可迁移任务，是否会导致 `sd->alb_count` 与 balance 失败计数的统计语义变化，进而影响 `sd->nr_balance_failed` 的累积和后续 active balance 触发频率。

## 参考链接

- lore thread: 未获取到
- 被修复的 commit: `e4c9a4cb244a ("sched/cache: Add migrate_llc_task migration type for cache-aware balancing")`
- tip-bot commit: 未获取到
- stable backport: 未获取到
