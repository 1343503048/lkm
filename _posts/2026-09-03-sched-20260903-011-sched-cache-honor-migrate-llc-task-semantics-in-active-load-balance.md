---
id: sched-20260903-011
date: '2026-09-03'
subject: 'sched/cache: Honor migrate_llc_task semantics in active load balance'
subsystem: sched
type: discussion
status: under_review
severity: medium
thread_root_msgid: <20260903020656.3793626-1-wanglu.priv@gmail.com>
lore_url: https://lore.kernel.org/all/20260903020656.3793626-1-wanglu.priv@gmail.com/
upstream_commit: null
fixes_commit: e4c9a4cb244a
merged_branch: null
current_version: v4
generated_at: '2026-09-07'
authors:
- Lu Wang
maintainers_involved:
- Tim Chen
- Chen Yu
patch_series:
- 'sched/cache: Honor migrate_llc_task semantics in active load balance'
merge_assessment:
  likelihood: likely
  blocking_issues:
  - 本线程无 Peter Zijlstra/Ingo Molnar 痕迹，作为独立 fix 还是并入 CAS 系列分发未定
  - v1~v4 均无量化验证数据，误迁移的实际影响面只有场景推演
  next_action: 在新基线上复现 p1/p2 场景并给出误迁移计数，同时确认合入路由
contribution_opportunities:
- 构造 preferred LLC 相反的双任务场景，统计修复前后被 ALB 搬离 preferred LLC 的任务数
- 核查 DELAY_DEQUEUE 与 LBF_ACTIVE_LB_LLC 组合下 can_migrate_task() 新返回值的影响
- 在 ef9293b3b7 基线上逐 patch 编译验证本补丁及其所属 CAS 系列
- 沉淀设计约束：跨 stopper 传递 lb_env 状态时新增 flag 而非复用 migration_type
source_email_count: 1
related_articles:
- sched-20260902-009
tags:
- sched/cache
- load_balance
- affinity
title: 'sched/cache: Honor migrate_llc_task semantics in active load balance'
layout: article
---

## TL;DR

CAS 用 `migrate_llc_task` 把任务推向它的 preferred LLC，但被动负载均衡回落到主动负载均衡（ALB）时这个语义会丢：ALB 里的 CPU stopper 会重建一个不继承 `migration_type` 的 `lb_env`，于是 `can_migrate_task()` 在 `env->flags & LBF_ACTIVE_LB` 分支里对任何任务直接 `return 1`，可能把任务搬离其 preferred LLC。Lu Wang 的 v4 新增 `LBF_ACTIVE_LB_LLC` 标志并在 kick 时挑选 stopper 回调来跨过这个异步边界保住语义，改动 `kernel/sched/fair.c` 51 增 6 删，带 `Fixes: e4c9a4cb244a`，并已同时挂上 Tim Chen 与 Chen Yu 的 `Reviewed-by`。本日（09-03）v4 相对 v3 无功能变化，只是把基线 rebase 到含 Tim Chen `f0d243a96f26` 的 sched tip（`ef9293b3b7`），发出时尚无人回帖。

## 背景与问题

`migrate_llc_task` 是 cache-aware scheduling（CAS）引入的迁移类型，用于把任务导向其 preferred LLC。问题出在被动 → 主动负载均衡的交接：ALB 由 CPU stopper 执行，它会从零构造一个 `lb_env`，不继承触发它的那轮被动负载均衡里的 `migration_type`。结果 ALB 看不到「这一轮是为 LLC 而做的」，仍会把首选 LLC 与目的地不匹配的任务搬走。

提交说明给了一个具体例子：`src_rq` 上有 p1、p2 两个 runnable 任务，p1 的 preferred LLC 是 `dst_rq` 所在的 `dst_llc`，p2 则 prefers `src_rq` 所在的 `src_llc`；因为至少有一个任务想走，被动 LB 会把 `migration_type` 置为 `migrate_llc_task`。但进入 ALB 后，`can_migrate_task()` 在 `LBF_ACTIVE_LB` 分支直接放行，于是 p2 被搬出它首选的 LLC——与本轮的意图恰好相反。

这与 08-09 那笔 `f0d243a96f26`（"sched/fair: Avoid creating misfits during cache-aware balancing"）处理的是同一族问题：CAS 的 LLC 语义在被动路径上被尊重，在异步/兜底路径上会漏。

## 技术方案

提交说明显式列出两条路并说明取舍：

- (a) 给 `struct rq` 增加成员，让 ALB 从触发它的被动 LB 继承 `migrate_llc_task`；
- (b) 新增 `LBF_ACTIVE_LB_LLC` 标志，在 kick 时就选定 stopper 回调，把迁移语义带过异步边界。

选择 (b) 的理由是不要把 `migration_type` 穿过 stopper 传递——那会改变 `migration_type` 对 delayed dequeue 任务的含义。落到代码上是 5 处改动（`kernel/sched/fair.c`，51 增 6 删）：

- 新增 `#define LBF_ACTIVE_LB_LLC 0x40`（与已有 `LBF_ACTIVE_LB`、`LBF_LLC_PINNED` 同族）。
- 新增 `migrate_llc_task_wrong_dst(p, env)`：`sched_cache_enabled()` 且（`env->migration_type == migrate_llc_task` 或 `env->flags & LBF_ACTIVE_LB_LLC`）且 `READ_ONCE(p->preferred_llc) != llc_id(env->dst_cpu)` 时为真；注释明确写了被动路径走 `migration_type`、主动路径走 `flags`，以免覆盖 `migration_type`。`!CONFIG_SCHED_CACHE` 时提供返回 false 的空实现。
- `migrate_degrades_llc()` 里原先手写的等价判断改为调用该 helper。
- `can_migrate_task()` 的 `if (env->flags & LBF_ACTIVE_LB) return 1;` 改为 `return !migrate_llc_task_wrong_dst(p, env);`——这是真正的语义修正点。
- `active_load_balance_cpu_stop()` 拆成 `__active_load_balance_cpu_stop(void *data, unsigned int lb_flags)`，构造 `lb_env` 时用 `.flags = LBF_ACTIVE_LB | lb_flags`，再派生两个回调：`active_load_balance_cpu_stop()`（0）与 `active_load_balance_llc_cpu_stop()`（`LBF_ACTIVE_LB_LLC`）。
- `sched_balance_rq()` 里 `stop_one_cpu_nowait()` 的回调参数改为 `alb_stop_fn(&env)`，`alb_stop_fn()` 在 `env->migration_type == migrate_llc_task` 时返回 LLC 版回调；旁边的注释即「`migration_type` 在别处被用于决定迁移策略，不应仅仅为了跨 stopper 标记一次 LLC 导向的主动均衡而复用它」。

整体是单文件、无新增 `struct rq` 字段、无 ABI 变化，且全部判断都在 `sched_cache_enabled()` 之后，未启用 CAS 的平台不受影响。

## 版本演进与当前进展

- v1（08-01 首发，标题为小写 "honor"）：把 `migration_type` 直接穿过 stopper 传给主动均衡。
- 08-03 ~ 08-07 一轮密集 review：Tim Chen 发 4 封、Chen Yu（`Chen, Yu C`）发 3 封、作者回 3 封（这些邮件的正文未被缓存保留，具体内容无法确认）。v2 的 changelog 显示这一轮改变了实现路线：改为「在 kick 时选择 stopper 回调」，理由是不再穿过 stopper 传 `migration_type`，避免影响 delayed dequeue 任务对该字段的语义。
- v2（08-09）→ v3（08-13）：v3 只重写提交说明与 helper 注释，无代码改动；08-24 作者在 v3 线程上再发过一封信（正文未保留）。
- **v4（本日 09-03 10:06）**：纯 rebase 到 `tip sched/core ef9293b3b7`，作者注明该基线已包含 Tim Chen 的 `f0d243a96f26`（"sched/fair: Avoid creating misfits during cache-aware balancing"），并声明「No functional changes vs v3」；标题首字母改为大写 `Honor`。
- v4 带 `Fixes: e4c9a4cb244a`、`Suggested-by: "Chen, Yu C"`，并携带 `Reviewed-by: Tim Chen` + `Reviewed-by: Chen Yu`（缓存无法确认两个 tag 具体落在哪一版）。
- 本日 v4 发出后尚无人回帖。

## Maintainer 意见与讨论焦点

- **路线之争已收敛**：`migration_type` 是否应当被复用来跨 stopper 传递，是本系列早期（08-03~08-07 那轮）的核心分歧。v4 的提交说明把结论固化成文字——两条可行方案列出后明确选 (b)，理由是「穿过 stopper 传 `migration_type` 会影响 delayed dequeue 任务对该字段的解读」；代码里 `alb_stop_fn()` 上方的注释再次强调 `migration_type` 在别处已用于决策，不应为标记一次 LLC 导向的主动均衡而复用它。这类「把被否决的方案留在提交说明里」的写法通常就是维护者意见沉淀的结果。
- **Chen Yu** 是方案的建议者（`Suggested-by: "Chen, Yu C" <yu.c.chen@intel.com>`），并已给 `Reviewed-by`。
- **Tim Chen**（CAS 系列作者）给了 `Reviewed-by`，并且他 09-03 之前刚合入的 `f0d243a96f26` 与本补丁处理同一族漏洞，v4 特意 rebase 到包含它的基线——说明 Intel 侧把 CAS 的语义完整性当作一条正在推进的整改线，而不是单个孤立补丁。
- 本日焦点不在观点：v4 只是 rebase，线程当天没有新意见，也没有 `Acked-by`/`Reported-by` 交换。
- 未参与：Peter Zijlstra、Ingo Molnar 在本线程无痕迹，合入路由（走 tip sched/core 还是走 CAS 系列分支）尚未见表态。

## 合入评估

likelihood: **likely**。

依据：Intel 两位 reviewer 都已 `Reviewed-by`，其中一位（Chen Yu）还是方案建议者；带指向已合入提交的 `Fixes: e4c9a4cb244a`，符合 fixes 通道条件；改动仅 51 增 6 删、单文件、无新增结构体字段、无 Kconfig 与 ABI 影响，且全部逻辑位于 `sched_cache_enabled()` 之后，未启用 CAS 的平台零风险；v4 唯一变化是 rebase 到已含相关修复的 sched tip 基线，属于「等合入」形态而非「等讨论」形态；连续四个版本的迭代已把实现路线的取舍写成文档。

卡点：只剩路由与验证两项。一是本 thread 中无 sched 核心维护者（Peter Zijlstra / Ingo Molnar）痕迹，需要确认是作为独立 fix 进 `tip:sched/core`，还是与 Tim Chen 的 CAS 系列合并分发；二是从 v1 到 v4 全部邮件都没有给出量化验证数据，且提交说明中「p1/p2 例子」这一触发条件依赖 `src_rq` 上恰好存在 LLC 偏好相反的两个任务，社区尚未看到生产规模或 benchmark 层面的证据。

## 效果评估

邮件中未提供效果数据。v4 正文只有场景推演（p1/p2 的例子）、方案取舍与 diffstat，没有任何 benchmark、`perf sched` 或 `sched_stats` 对比，也没有说明该 bug 在真实负载上的可观测表现（例如误迁移次数、preferred LLC 命中率）。

需要标注的证据缺口：v1~v3 及 08-03~08-24 全部回帖的正文未被邮件缓存保留，因此无法判断早期 review 轮次中是否曾给出过数据；本日 v4 与同日 Tim Chen 在 [[sched-20260903-012]] 中反馈的 CAS helper 编译问题都指向同一事实——CAS 这条线目前主要在 Intel 内部推进验证，公开线程里看不到量化结果。

## 我可以参与的点

1. 补上唯一的空白：把 v4 跑在一个 CAS 打开的多 LLC 机器上，用「同一 `src_rq` 上放一个 preferred LLC 指向 dst、另一个指向 src」的构造任务复现提交说明里的 p1/p2 场景，统计修复前后被 ALB 搬离 preferred LLC 的任务数（`sched_debug` 的 `llc_*` 统计或 `perf sched migrate`）。这类数据一旦回帖，基本可以收尾。
2. 审 delayed dequeue 这条被刻意绕开的路径：作者拒绝穿过 stopper 传 `migration_type` 的理由是它对 delayed dequeue 任务另有含义，可以顺着这条论证去核 `DELAY_DEQUEUE` + `LBF_ACTIVE_LB_LLC` 组合下 `can_migrate_task()` 的新返回值是否会让本应被推迟出队的任务滞留在源 CPU。
3. 与同线程反馈的编译问题（[[sched-20260903-012]]）呼应，确认本补丁在新基线 `ef9293b3b7` 上逐 patch 可编译——v4 只有 1 个补丁风险较低，但同族的 CAS 系列已被证明存在「只有整套能编、单 patch 编不过」的问题。
4. 回合判断：本补丁依附于 `migrate_llc_task` / `preferred_llc` / `LBF_*` 整套 CAS 基础设施，OLK-6.6 若未回合 `e4c9a4cb244a` 则无可回合对象；可移植的是那条设计约束——跨 stopper 传递 lb_env 状态时优先新增 flag 而非复用 `migration_type`，回合自研 LLC 亲和策略时同样适用。

## 参考链接

- 本补丁各版本（作者 changelog 中列出的 Link）：
  - v4（本日）：https://lore.kernel.org/all/20260903020656.3793626-1-wanglu.priv@gmail.com/
  - v3：https://lore.kernel.org/all/20260813045241.3039862-1-wanglu.priv@gmail.com/
  - v2：https://lore.kernel.org/all/20260809105343.1189051-1-wanglu.priv@gmail.com/
  - v1：https://lore.kernel.org/all/20260801122252.2476258-1-wanglu.priv@gmail.com/
- 相关文章：[[sched-20260902-009]]（NUMA 细粒度 + sched/cache 辅助框架 RFC v2）、[[sched-20260903-012]]（同族 CAS helper 的编译问题反馈）。
