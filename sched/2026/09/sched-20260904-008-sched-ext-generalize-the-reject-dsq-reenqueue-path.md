# sched_ext: Generalize the reject DSQ reenqueue path

## TL;DR

`reject DSQ` 原本只服务 sub-scheduler 的 cap 失败：存储和初始化挂在 `CONFIG_EXT_SUB_SCHED` 下，排空路径假定每个被拒任务的原因都是 `SCX_TASK_REENQ_CAP`。Andrea Righi 的 12/18（属 v13 代理执行兼容系列）把它改为无条件存在，并把重入队原因直接携带在 `p->scx.flags` 里，供代理执行竞态停靠复用。本日 sched_ext 维护者 Tejun Heo 给出的是风格层面的反对意见：清理散落在各处且有时清两遍，要求收敛到统一出口标签。

## 背景与问题

除 sub-scheduler cap 失败之外，还有别的「瞬时放置失败」需要同一套能力：把任务停在它的源 rq 上，再交回其所属 BPF 调度器重新决策。代理执行与远端 DSQ 转移竞态正是这种失败（v13 的 13/18 会用到）。

现状不满足：`rq->scx.reject_dsq` 的存储与初始化依赖 `CONFIG_EXT_SUB_SCHED`，排空路径也按「被拒原因必然是 `SCX_TASK_REENQ_CAP`」写死。因此需要一个泛化的、原因随任务携带的机制。这是 v13 的准备性补丁。

## 技术方案

- reject DSQ 变为无条件存在（去掉 `CONFIG_EXT_SUB_SCHED` 门控），不再假定唯一的重入队原因。
- 重入队原因直接放进 `p->scx.flags`（`SCX_TASK_REENQ_REASON_MASK`），由拒绝点写入。
- 生命周期规则：原因在 `ops.enqueue()` 执行期间保持有效，让 BPF 可以读；回调返回之后、解析 direct dispatch 之前立即清除；绕过 `ops.enqueue()` 的路径在内核选定放置之前清除。这样「来自新放置的拒绝」可以把自己的原因写进一个确定已清空的字段。
- 相应地 `scx_dispatch_enqueue()` 不再在 `SCX_DSQ_LOCAL` 分支里手工置 `is_rq_owned = true`，改为进入时统一 `bool is_rq_owned = dsq_is_rq_owned(dsq)`（RQ-owned DSQ 的判定收敛到一个谓词）。
- `reenq_local()` / `reenq_user()` 中原有的「若已有原因则 WARN 并顺手清掉」改为纯 `WARN_ON_ONCE()`——清理由上游调用点负责，不再在两处重复清。
- 改动：`kernel/sched/ext/ext.c` 52 行、`kernel/sched/ext/sub.c` +2、`kernel/sched/sched.h` 2 行，合计 25 行新增 / 31 行删除（净减代码）。

## 版本演进与当前进展

- 本补丁是 v13（08-31，`20260831134338.1531664-1-arighi@nvidia.com`）的 12/18，补丁自身 msgid `20260831134338.1531664-13-arighi@nvidia.com`。泛化与代码搬移在更早版本已被拆开（v11 的 changes 记录「Split reject-DSQ code movement from its generalization and carry the re-enqueue reason directly in p->scx.flags」，即 11/18 搬代码、12/18 做泛化）。
- 09-04 06:39 Tejun Heo 回帖提出 nits；本日匹配 1 封邮件（仅该回帖）。
- 缓存中未见 v14，也未见该补丁被 apply；系列整体状态见同日文章《sched: Make proxy execution compatible with sched_ext》（Tejun 认为可以合入并在树内迭代，等 Peter Zijlstra 表态）。

## Maintainer 意见与讨论焦点

**Tejun Heo（sched_ext 维护者，09-04 06:39）**，两条意见都属实现质量而非方向：
1. `"No need for {}."` —— 针对 diff 里新增代码块中不必要的花括号。
2. `"This is too messy. The clearing is scattered all over and sometimes done twice. Can't you add one label that everyone jumps to for exit and clear it there?"` —— 直接命中本补丁的做法：`p->scx.flags &= ~SCX_TASK_REENQ_REASON_MASK` 被散布到 `scx_do_enqueue_task()` 的多条出口（错误返回、`direct`、`local_norefill`、`local`、`enqueue`）、`dequeue_task_scx()`、`set_next_task_scx()` 等多处，而且部分路径清两次。他要求改成统一出口标签集中清理。

**方向本身未被质疑**：「让原因随任务携带、把 reject DSQ 从 sub-sched 专属改为通用」在 v11 就已是他提出的拆法（见版本演进），v13 只是把清理时机做细。

**讨论焦点**：本补丁争的是可维护性——状态机式的 flag 清理散落是典型的易错点，新代码在 `put_prev_task_scx()` 里删掉了一次清理、又在 `scx_do_enqueue_task()` 里加了多处，正是 Tejun 说「sometimes done twice」的地方。缓存中未见其他人对该补丁的回应。

## 合入评估

likelihood: **possible**。

依据：它是 v13 的准备性补丁，v13 整体已获 sched_ext 维护者「ready to merge and iterate in tree」的评价，方向无争议；本补丁净减少代码（+25/-31），不新增外部行为，作为系列第 12 片会随系列一起排队。

卡点：
- Tejun 的两条 nits 尚未在新版本中落实（缓存中未见 v14），其中「统一出口标签清理原因」是对现有实现的结构性重写，不是简单调整。
- 「只在 `ops.enqueue()` 之后清一次」的写法必须保证所有绕过 `ops.enqueue()` 的路径仍然清干净，否则 `WARN_ON_ONCE()` 会在下一次拒绝时触发；这个不变式由集中出口标签来保证更容易，Tejun 的意见正是在降低这层风险。
- 上游系列整体仍在等 Peter Zijlstra 表态。

## 效果评估

邮件中未提供效果数据。本补丁是内部机制泛化，作者自述为「preparatory change to support proxy execution with sched_ext」，没有可测的性能或用户可见行为变化；Tejun 的回帖也未要求任何测试数据。唯一可量化的信息是代码规模：净减少 6 行、删掉了 `CONFIG_EXT_SUB_SCHED` 对 reject DSQ 的门控。

## 我可以参与的点

- **可直接贡献的实现**：Tejun 要求的「统一出口标签」改法边界清楚，适合做成一版建议：把 `p->scx.flags &= ~SCX_TASK_REENQ_REASON_MASK` 收敛到 `scx_do_enqueue_task()` 的单个 out 标签，并核对 `dequeue_task_scx()` / `set_next_task_scx()` / `reenq_local()` / `reenq_user()` 中哪些清理可以随之删除。同时给出一条不变式说明：任何设置原因的路径必须在返回前经过同一出口。
- **值得复核的具体点**：`scx_dispatch_enqueue()` 改为 `bool is_rq_owned = dsq_is_rq_owned(dsq)` 后，`SCX_DSQ_LOCAL` 分支会先经 `scx_resolve_local_dsq()` 改写 `dsq`，需确认判定用的是解析前还是解析后的 DSQ——这直接决定 local DSQ 入队时是否仍被当作 RQ-owned。这是一个只看函数体就能回答、且容易出错的对齐点。
- **与调度器上下文的耦合**：本补丁的 `is_rq_owned` 判定与同日 008/007 讨论的「donor 是调度上下文、owner 是执行上下文」直接相关；如果关心代理执行下 DSQ 归属的语义，从 `dsq_is_rq_owned()` + `scx_resolve_local_dsq()` 这一对函数入手是最省力的切入口。
- **暂不建议介入**：无 benchmark 空间，也不涉及 cgroup/cpuset 语义；回合层面单独拿这片没有意义（它是 v13 的内部准备）。

## 参考链接

- 邮件线程：
  - Tejun Heo 的 nits 评审: <https://lore.kernel.org/all/apn3GHPzhPZtGbSs@slm.duckdns.org/>
  - 本补丁（v13 12/18）: <https://lore.kernel.org/all/20260831134338.1531664-13-arighi@nvidia.com/>
  - 所属 v13 系列 cover letter: <https://lore.kernel.org/all/20260831134338.1531664-1-arighi@nvidia.com/>
- 相关文章/系列：
  - [[sched-20260902-001]] 代理执行与 sched_ext 兼容（影响 DSQ 路径）。
- 相关代码/commit：
  - `kernel/sched/ext/ext.c` `scx_dispatch_enqueue()` / `scx_do_enqueue_task()` / `reenq_local()` / `reenq_user()` / `dsq_is_rq_owned()`
  - `kernel/sched/ext/sub.c`（reject DSQ 原属 sub-sched 的部分）
  - `SCX_TASK_REENQ_REASON_MASK` / `rq->scx.reject_dsq`

---
id: sched-20260904-008
date: '2026-09-04'
subject: 'sched_ext: Generalize the reject DSQ reenqueue path'
subsystem: sched
type: discussion
status: under_review
severity: medium
thread_root_msgid: 20260831134338.1531664-13-arighi@nvidia.com
lore_url: https://lore.kernel.org/all/20260831134338.1531664-13-arighi@nvidia.com/
upstream_commit: null
fixes_commit: null
merged_branch: null
current_version: v13
generated_at: '2026-09-07'
authors:
- Andrea Righi
maintainers_involved:
- Tejun Heo
patch_series:
- 'sched_ext: Generalize the reject DSQ reenqueue path'
merge_assessment:
  likelihood: medium
  blocking_issues:
  - Tejun 要求把 SCX_TASK_REENQ_REASON_MASK 的清理收敛到统一出口标签，当前实现散落且重复清理
  - diff 中不必要的花括号（风格问题）
  - 所属 v13 系列整体在等 Peter Zijlstra 表态
  next_action: 作者需在 v14 落实集中清理并说明各绕过 ops.enqueue() 的路径仍满足「设置前字段已清空」的不变式。
contribution_opportunities:
- 给出 Tejun 要求的统一 out 标签实现草案，并列出可随之删除的重复清理点
- 核对 scx_dispatch_enqueue() 中 dsq_is_rq_owned() 判定使用的是解析前还是解析后的 DSQ
- 说明 p->scx.flags 原因位与 ops.enqueue() 可见性之间的生命周期契约
source_email_count: 1
related_articles:
- sched-20260902-001
tags:
- sched_ext
---
