# sched/fair: Use cfs_rq->h_curr in the bandwidth paths

## TL;DR

Wanwu Li（kylinos）8/31 18:11 发出 2 补丁：EEVDF 单 runqueue 改造（`85570f10a4c6`）把"本层级是否有实体在跑"从 `cfs_rq->curr` 迁到 `cfs_rq->h_curr` 后，**CFS 带宽路径漏改了两处**，导致中间层 cgroup 的 `throttle_cfs_rq()` 永远拿不到一整份 `sched_cfs_bandwidth_slice()`、也永远不 arm 延迟 throttle 的 task_work——配置了 `cpu.max` 的子组可以超跑自己的配额。改动只有 3 行、两补丁都带 `Fixes:`。v1 刚发出，当天无人回复。对做 cpuset/cgroup 的人这是当天最值得看的一封。

## 背景与问题

- **触发条件**：`CONFIG_CFS_BANDWIDTH` 打开、在非根 cgroup 上配置 `cpu.max`（即存在中间层 `cfs_rq`），并且该层级自身有正在运行的实体时被 throttle。与架构无关。
- **症状**：带宽受控的 cgroup 在被判定耗尽配额时，走的是"没有运行实体"的分支——只分到 1ns 的 runtime，且不会 arm 延迟 throttle 的 task_work；正在跑的任务因此可以**继续越过本组配额**，直到下一次 pick 才把 work 挂上。
- **根因**：`85570f10a4c6 ("sched/eevdf: Move to a single runqueue")` 之后，`cfs_rq->curr` 只在**根** `cfs_rq` 上维护（由 `set_next_task_fair()`/`put_prev_task_fair()` 设置/清除），层级中每一层的"当前实体"改由 `cfs_rq->h_curr` 表示（`set_next_entity()` 在每层设置）。cgroup 层级本身仍被保留用于负载跟踪与带宽记账，于是带宽路径成了唯一还在**逐层运行、却又逐层读 `->curr`** 的代码。
- **影响范围**：作者自称把 `kernel/sched/fair.c` 里所有 `cfs_rq->curr` 引用都审了一遍，结论是只有两处仍会在层级的每一层执行：`throttle_cfs_rq()`（1/2）与 `distribute_cfs_runtime()`（2/2）；其余 reader 要么被限制在根 `cfs_rq`（`avg_vruntime`、`place_entity`、`pick_eevdf`、enqueue/dequeue、`update_curr_eevdf`、put/set_next_task_fair 及两处赋值），要么已经在读 `cfs_rq->h_curr`（`update_curr`、`check_enqueue_throttle`、`set_next_entity`、`put_prev_entity`）。

## 技术方案

两补丁各改一行读取点（合计 `kernel/sched/fair.c | 6 +++---`）：

1. **1/2 `throttle_cfs_rq()`**：`struct sched_entity *curr = cfs_rq->curr;` → `cfs_rq->h_curr`，并同步修正上方注释。修完之后，中间层 `cfs_rq` 在确有运行实体时会正常申请一份 `sysctl_sched_cfs_bandwidth_slice` 的带宽并 arm `task_throttle_setup_work()`，与根 `cfs_rq` 行为一致。
2. **2/2 `distribute_cfs_runtime()`**：`if (cfs_rq->curr)` → `if (cfs_rq->h_curr)`，恢复"只有该层确实有任务在跑（即处于延迟 throttle 窗口内）才刷新 rq clock 并用 `update_curr()` 记账"的原意。作者**如实说明这今天不是正确性漏洞**：自 `28ad5427682b ("sched/fair: Call update_curr() before unthrottling the hierarchy")` 起 `unthrottle_cfs_rq()` 会无条件补账，所以这个检查已成死代码，但它原本要做的"重分配前先把还在跑的任务消耗掉的 runtime 扣掉"这件事丢了。

备选方案：作者在 cover 末尾主动提出，`85570f10a4c6` 自身带着"最终去掉 `cfs_rq->h_curr`"的 TODO——如果维护者更希望走那条重构路线，这两个修复可以被折叠进去（"if you prefer, these fixes can be folded into the planned rework"）。这是本系列唯一被点名的设计分歧。

## 版本演进与当前进展

- 当前 v1（`<20260831101141.391382-1-liwanwu@kylinos.cn>`，base-commit `1b78070aaef63512688aebfbc82365ef9d6660f1`），v1 刚发出，暂无 review 意见。
- 无后续版本、无维护者表态、无 `Fixes:` 之外的元数据（两补丁均带 `Fixes: 85570f10a4c6`）。

## Maintainer 意见与讨论焦点

本日没有任何 maintainer 回复——收件人是 cover 里的 "Hi Peter, Ingo"，讨论尚未开始。

可预期的争议点（来自邮件本身，不是社区意见）：

- 1/2 是真正的行为修复（配额超跑），2/2 只是复活一段死代码；维护者可能要求把 2/2 拆走或并入将来的 `h_curr` 去除重构。
- 作者自己承认 `h_curr` 是过渡态（`85570f10a4c6` 带 TODO 要删掉它），所以"改 `h_curr` 读取点"这种修法与"最终删掉 `h_curr`"存在方向性张力——这是最可能被追问的地方。

## 合入评估

**possible**。有利：改动 3 行、语义单向（读错字段→读对字段）、两补丁都带 `Fixes: 85570f10a4c6`、并给出了完整的同类引用点审计作为论证；1/2 描述的配额超跑是明确的隔离性问题，属于 stable 会想要的那类修复。不确定：v1 尚无人回复，作者没提供 reproducer 或数据；且修复是否被接受取决于维护者对 `h_curr` 过渡期长短的态度——如果 `h_curr` 很快被删，这两个补丁可能只作为 `Fixes:` 快速合入而不进入长期演进。`next_action`：需要 Vincent Guittot / Peter Zijlstra 表态，并需要一份能观测到"子组超跑配额"的测试或统计（例如对比 `cpu.stat` 的 `nr_throttled`/`throttled_usec` 与组内实际消耗）。

## 效果评估

暂无效果数据。邮件里没有 benchmark、没有 `cpu.max` 超跑幅度的量化、也没有 kselftest 结果；全部论证基于代码语义与 `cfs_rq->curr` 引用点审计。"running task can out-run its group's quota" 是对控制流的推演，不是测出来的数字。

## 我可以参与的点

- **给出可复现证据**（最高价值）：多层 `cpu.max` 配置 + 单任务持续消耗，采集 `cpu.stat`（`nr_throttled`、`throttled_usec`）与 cgroup v2 `cpu.pressure`/实际 runtime，对比本补丁前后；这正是社区接下来一定会问、而作者没给的东西。
- **回合价值判断**：`85570f10a4c6`（单 runqueue）是否已进入你要跟踪的stable/OLK 基线决定本补丁是否需要回合——如果基线里没有该 commit，`cfs_rq->curr` 仍是逐层维护的，这个 bug 不存在。
- **review 参与**：作者明确请求 Peter/Ingo 判断"是独立修还是折进 `h_curr` 移除重构"，可以先从 `distribute_cfs_runtime()` 是否属于死代码清理给意见。

## 参考链接

- lore thread（cover 0/2）: https://lore.kernel.org/all/20260831101141.391382-1-liwanwu@kylinos.cn/
- 1/2: https://lore.kernel.org/all/20260831101141.391382-2-liwanwu@kylinos.cn/
- 2/2: https://lore.kernel.org/all/20260831101141.391382-3-liwanwu@kylinos.cn/
- tip-bot commit: 未获取到
- stable backport: 未获取到

---
id: sched-20260831-004
date: '2026-08-31'
subject: "sched/fair: Use cfs_rq->h_curr in the bandwidth paths"
subsystem: sched
type: bug
status: under_review
severity: high
thread_root_msgid: "<20260831101141.391382-1-liwanwu@kylinos.cn>"
lore_url: "https://lore.kernel.org/all/20260831101141.391382-1-liwanwu@kylinos.cn/"
authors: [Wanwu Li]
maintainers_involved: []
current_version: v1
patch_series:
  - version: v1
    msgid: "<20260831101141.391382-1-liwanwu@kylinos.cn>"
    date: 2026-08-31
    summary: "throttle_cfs_rq()/distribute_cfs_runtime() 的 cfs_rq->curr 读取点改为 cfs_rq->h_curr，修复 85570f10a4c6 遗漏的逐层 current 转换"
    review_outcome: "v1 刚发出，暂无 review 意见"
upstream_commit: null
fixes_commit: "85570f10a4c6"
merged_branch: null
merge_assessment:
  likelihood: possible
  blocking_issues:
    - "无人回复，缺 reproducer 与量化数据"
    - "2/2 恢复的是当前已非正确性必需的检查（28ad5427682b 后 unthrottle 无条件补账），可能被评为死代码清理"
    - "h_curr 本身带被移除的 TODO，维护者可能要求把修复折进该重构"
  next_action: "提供 cpu.max 超跑的复现证据并请 Vincent Guittot / Peter Zijlstra 确认修法与拆分方式"
contribution_opportunities:
  - kind: testing
    description: "多层 cpu.max 场景下采集 cpu.stat 的 nr_throttled/throttled_usec 与实际 runtime，验证 1/2 是否消除配额超跑"
  - kind: review
    description: "就 2/2 属于行为修复还是死代码清理、以及是否应折进 h_curr 移除重构给出意见"
generated_at: "2026-09-07T21:16:22"
source_email_count: 3
related_articles: []
tags: [cgroup, cfs, eevdf]
---
