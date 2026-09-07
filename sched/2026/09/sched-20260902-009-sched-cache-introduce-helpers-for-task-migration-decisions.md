# sched/cache: Introduce helpers for task migration decisions

## TL;DR

Hygon Jianyong Wu 的 23 补丁 RFC v2 里 `11/23` 引入 `can_migrate_node()` / `get_span_stats()` 这组迁移决策
helper（把 `can_migrate_llc()` 的判断能力从 LLC 抬到 NUMA node 粒度）。9/1 Peter Zijlstra 对 11/23 做了
**逐行 14 处**质疑，9/2 作者 13:08 一封长帖逐条回答、13:46 再答排序风格问题。这一天全部是「作者解释 + 承诺改」，
**没有新版本、没有一行数据**。9/3 Tim Chen 又发现 11/23 单独编译不过（`'dst_pre' undeclared`），作者承认
补丁间自洽性有问题。

## 背景与问题

本系列的主线是给 cache-aware 负载均衡加 NUMA 维度：`01/23` `llc_to_node()`、`02/23` 唯一距离值的 NUMA
distance matrix、`04/23` llc distance 计算、`08/23`+`09/23` per-CPU task NUMA preference 计数、
`10/23` per-sd scratch 存放 affinity score、`12/23` rq affinity gain 计算、`17/23` 细粒度 NUMA balancing、
`20/23` 整个 thread group 的利用率估算。

`11/23` 在这条链上的位置是**决策函数**：现有 `can_migrate_llc()` 只在单个 LLC 粒度上判断
（`invalid_llc_nr()` / `exceed_llc_capacity()` / `task_cache_work()` 那一套，参见 [[sched-20260902-003]]），
`11/23` 新增按 NUMA node 亲和序列遍历、并能给出「迁移 / 不迁移 / 不受限（`mig_unrestricted`）」三态判断的
helper，为后面的 node 粒度均衡提供入口。RFC v2 的 cover 正文本地未缓存（缺 2026-08-27 邮件），动机段
**未获取到**。

## 技术方案

从 Peter 的评审对照可以还原 11/23 的结构（他的引述顺序即代码顺序）：

- `can_migrate_node()`：以「包含 `target_cpu` 的 node」决定 node 亲和遍历序列，沿序列遍历；对每个 node 调
  `get_span_stats()`；遇到 `dst_cpu` 所在 node 时进入**终结分支**——遍历该 node 内的 LLC，找到含 `dst_cpu`
  的 LLC 后直接返回决策；期间会跳过 target 与 src 之间的 node。
- 与既有 `can_migrate_llc()` 的三点差异（Peter 提出、作者确认）：(a) `can_migrate_llc()` 在
  `!get_llc_stats(src_cpu)` 时以 `mig_unrestricted` 早退，11/23 缺这条；(b) `can_migrate_llc()` 会把
  `src_util` 减去 `tsk_util` 并对 0 取下界，11/23 没有；(c) 11/23 用 `get_span_stats()` 而 span 其实只有一个
  LLC，等价于绕了一层 `get_llc_stats()`。
- 作者给出的关键设计意图（9/2 原话）：迁移前后两种利用率都要用——
  "The current imbalance check uses the utilization before the move, while the capacity and anti-bounce checks
  need the utilization after the move." 并承诺改成显式 `src_pre/src_post` 与 `dst_pre/dst_post` 四元组，
  源侧减法对 0 取下界。
- 「反跳」（anti-bounce）判断的存在说明 helper 需要同时防住「移过去又立刻被移回来」。
- 跳步语义澄清：`!to-prefer` 路径下目的 CPU 不在 target_llc→src_llc 的亲和子序列内，"That's why we skip them
  here"；且 "Once the walk reaches the dst llc, we have enough information to make the final decision ... LLCs
  after the destination llc don't affect this decision."
- 针对 Peter 指出的「上面那个循环与这段共用同一段代码，fall through 时会重复扫描」，作者的修法是显式化终结性：
  "I will make that explicit by returning mig_unrestricted if the destination llc is unexpectedly not found,
  so that the generic llc walk is only used for non-destination nodes. Thus, duplicate scan is avoided."

## 版本演进与当前进展

- 8/27：Jianyong Wu 发 RFC v2 共 23 补丁（cover `<20260827122816.756234-1-wujianyong@hygon.cn>`，
  11/23 `<20260827122816.756234-12-wujianyong@hygon.cn>`）；正文本地未缓存。
- 9/1 17:08：Peter Zijlstra 对 11/23 逐行评审（14 处，混合语义与风格）。
- 9/1 19:32：Peter 追加一条风格要求——"We prefer inverse xmas ordering -- where possible. So please go through
  the code and re-arrange things."，并给出 `get_span_stats()` 声明重排示例。
- 9/2 13:08：作者一封帖按 Peter 的每条原文逐条答复（内容见上）；13:46：接受 inverse-christmas-tree 排序要求。
- 9/3 05:11：Tim Chen 报 11/23 单独编译失败
  `kernel/sched/fair.c:10855:69: error: 'dst_pre' undeclared (first use in this function)`（出现在
  `can_migrate_node()` 里 `!util_greater(u, dst_pre)`，宏定义在 10618 行），并判断
  "Likely the posted version is slightly different from the tested version."
- 9/3 10:04：作者解释 "the dst_pre fix landed in patch 20 but wasn't folded back into this patch, so patch 11
  alone doesn't build -- the full series builds because patch 20 fixes it"，承诺下一版 squash 修复并
  "compile-test each individual commit before posting the next version"。
- 版本仍是 v2；到 9/7 缓存内未见 v3。

## Maintainer 意见与讨论焦点

- **Peter Zijlstra**：没有 NAK、也没有任何认可，14 条意见全部是「读不懂 / 与既有 `can_migrate_llc()` 不一致 /
  风格」。其中真质疑是两条：(1) 为什么 `!p`（task 为 NULL）是合法输入——"It isn't clear when !p would be valid.
  migration is always about a task, no?"；(2) 为什么跳过 target 与 src 之间那些**局部性最好**的 node——
  "And then you skip the nodes between target and src, which are the nodes with best locality, confusing, but
  lets read on.." 这两条恰恰是设计语义问题，不是代码问题。
- **Jianyong Wu（作者）**：`!p` 的解释是 helper 也被 `llc_balance` 调用、那里传 NULL task，此时 `tsk_util` 为 0、
  决策走 `to_pref` 路径，与 `can_migrate_llc()` 一致。跳过中间 node 的解释依赖 `!to-prefer` 路径前提。态度是
  全面接受（"Agreed"、"Yeah, will remove it"、"Will change it"、"I'll refactor these code"），未与 Peter 争。
- **Tim Chen（sched/cache 维护者，Intel）**：关注点落在可构建性与补丁自洽，即评审这个系列时的**最小可用门槛**。
- 焦点收敛为：helper 的语义正确性目前**只靠作者口头解释**，Peter 的两条疑问没有第三方能验证。

## 合入评估

**unclear**。理由：(1) 这是 RFC，Peter 的一轮评审只换来解释与「下一版改」，没有任何 `Reviewed-by`/`Acked-by`；
(2) 11/23 单独不能编译，说明 23 个补丁之间存在跨补丁状态依赖（作者自己说 fix 落在 20 号补丁里），系列尚未达到
可 bisect/可分片评审的标准；(3) 23 补丁的体量、且横跨 sched/topology、sched/cache、sched/fair 三块，按上游惯例
一定会被要求拆分；(4) 全线程至今**没有一个数字**——既没有 helper 的热路径开销，也没有 node 粒度均衡带来的收益。
真正的近期前景是出 v3 并修掉 Peter 列的那批点，而不是合入。

## 效果评估

暂无效果数据。9/2 帖内没有任何 benchmark、迁移次数或 NUMA hint fault 统计。唯一可量化的信息是负面信号：Tim Chen
的编译失败（`fair.c:10855`、宏 `util_greater` 定义在 `fair.c:10618`，其形式为
`((util1) * 100 > (util2) * (100 + llc_imb_pct))`，说明不均衡阈值判断走的是百分比放大比较而非直接减法）。

## 我可以参与的点

- **补数据是最直接的贡献**：这个系列缺的不是解释而是数字。helper 在 `fast path` 上的开销（每 node 一次
  `get_span_stats()` + 潜在重复扫描）与 node 粒度均衡的收益，在多 NUMA（4P/8P 或 Hygon）机器上跑一组
  hackbench / spec / NUMA hint fault 对比就有帖子可回。
- **验证 `!p` 路径**：作者说 `llc_balance` 会传 NULL task、此时 `tsk_util` 为 0、决策走 `to_pref`。这条分支是
  helper 语义里唯一「无任务」的判断，很容易写一个针对性的 trace 验证它是否真的只在预期场景被走到。
- **跟进跳过中间 node 的合理性**：Peter 两次问「target 与 src 之间的 node 局部性更好，为什么跳过」，作者的回答
  依赖 `!to-prefer` 前提。如果目的 node 与 src 之间确实存在更优 node，这就是潜在的策略缺陷，值得独立验证。
- **对 cpuset/cgroup 场景的意义**：一旦迁移决策从 LLC 粒度抬到 NUMA node 粒度并以 affinity score 打分，
  cpuset 边界与 node 亲和的组合会直接影响摆放结果；这个方向如果落地，长期分支上的 cpuset 均衡行为要重新评估。
- **系列拆分意见**：`01/23`–`10/23` 是拓扑/统计基础设施，`11/23`–`14/23` 是决策，`17/23`、`20/23` 是策略；
  建议按这三段拆帖，本身就是 maintainer 会欢迎的输入。

## 参考链接

- 系列 cover：https://lore.kernel.org/all/20260827122816.756234-1-wujianyong@hygon.cn/
- `11/23` 原始补丁：https://lore.kernel.org/all/20260827122816.756234-12-wujianyong@hygon.cn/
- Peter Zijlstra 逐行评审：https://lore.kernel.org/all/20260901090843.GQ4120091@noisy.programming.kicks-ass.net/
- Peter Zijlstra inverse-christmas-tree 要求：https://lore.kernel.org/all/20260901113207.GZ687043@noisy.programming.kicks-ass.net/
- 作者逐条答复：https://lore.kernel.org/all/226d79fa93a84193aa2507113747d348@hygon.cn/
- 作者答复排序要求：https://lore.kernel.org/all/89add08a0761429a851196d7ea5a10a2@hygon.cn/
- 相关：[[sched-20260902-003]]（sched/cache UAF，同一子系统）、[[sched-20260903-012]]、[[sched-20260904-006]]

---
id: sched-20260902-009
date: '2026-09-02'
subject: 'sched/cache: Introduce helpers for task migration decisions'
subsystem: sched
type: feature
status: under_review
severity: medium
thread_root_msgid: <20260827122816.756234-12-wujianyong@hygon.cn>
lore_url: https://lore.kernel.org/all/20260827122816.756234-12-wujianyong@hygon.cn/
upstream_commit: null
fixes_commit: null
merged_branch: null
current_version: v2
generated_at: '2026-09-07'
authors:
- Jianyong Wu
maintainers_involved:
- Peter Zijlstra
- Tim Chen
patch_series:
- '[RFC PATCH v2 01/23] sched/topology: Add llc_to_node() to translate LLC id to NUMA
  node'
- '[RFC PATCH v2 02/23] sched/topology: Introduce a NUMA distance matrix with unique
  distance values'
- '[RFC PATCH v2 04/23] sched/topology: Introduce a method to calculate the llc distance'
- '[RFC PATCH v2 07/23] sched/cache: Prioritize preferred NUMA node selection over
  LLC selection'
- '[RFC PATCH v2 08/23] sched/topology: Introduce a per-CPU tasks NUMA preferred counter'
- '[RFC PATCH v2 09/23] sched/cache: Account percpu sd task NUMA preference'
- '[RFC PATCH v2 10/23] sched/topology: Add per-sd scratch for the load balance affinity
  score'
- '[RFC PATCH v2 11/23] sched/cache: Introduce helpers for task migration decisions'
- '[RFC PATCH v2 12/23] sched/cache: Introduce rq affinity gain calculation'
- '[RFC PATCH v2 14/23] sched/cache: Drop prefer_sibling restriction for llc_balance'
- '[RFC PATCH v2 17/23] sched/fair: Fine-granularity NUMA balancing'
- '[RFC PATCH v2 20/23] sched/cache: Estimate utilization of the whole thread group'
merge_assessment:
  likelihood: unknown
  blocking_issues:
  - RFC 阶段：Peter Zijlstra 的 14 条意见只换到解释与「下一版改」，无任何认可标签
  - 11/23 单独编译失败（dst_pre undeclared），跨补丁依赖未清理，作者承诺 v3 squash 并逐补丁编译测试
  - 23 补丁横跨 sched/topology、sched/cache、sched/fair，未拆分，无法分片评审
  - 全线程无性能数据：helper 热路径开销与 node 粒度均衡收益均未测
  - 跳过 target 与 src 之间局部性更优 node 的策略依据仅有作者口头解释
  next_action: 等 v3：需包含 src_pre/src_post/dst_pre/dst_post 重构、mig_unrestricted 早退、inverse-christmas-tree
    排序与逐补丁可编译
contribution_opportunities:
- 在多 NUMA（4P/8P 或 Hygon）平台量化 11/23 helper 开销与 node 粒度均衡收益
- 验证 llc_balance 传入 NULL task 的 !p 分支是否只在预期场景走到
- 独立验证跳过 target-src 之间 node 的策略是否损失局部性
- 给出按拓扑/决策/策略三段拆分 23 补丁系列的建议
source_email_count: 2
related_articles: []
tags:
- sched/cache
- load_balance
---
