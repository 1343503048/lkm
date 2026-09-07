# sched: Scale cache-aware aggregation at LLC granularity

## TL;DR

Jianyong Wu（海光）的 23 片 RFC v2——把 cache-aware 调度的聚合域从「固定单个 LLC」扩展成「按 LLC 粒度有序铺开」，是当日 sched 目录里体量最大、也是唯一由 Peter Zijlstra 逐片跟读的一整个系列。**09-01 一天该系列产生 24 封邮件（PZ 12 / 作者 12）**，其中 patch 08 的 `numa_counts[]` 被当场判掉（改为按需求和）、patch 17 的「NUMA 与 LLC 迁移可分别开关」被 PZ 明确反对并给出替代方向。本篇覆盖整系列与尚未成文的 6 个子线程（08/09/10/14/17/20）；02/07/11/12 四片已有单独分析（sched-20260901-004~007）。

## 背景与问题

现有 cache-aware 实现是 **LLC 中心的聚合模型**：任务被聚到 preferred LLC，装不下才外溢。作者给出的问题定性是「fixed aggregation scope，跨 LLC 无法扩展」——单 LLC 容量成为聚合上界，超过之后放置退化。PZ 给的 directions 是**把资源按 LLC 粒度扩展**，本系列就是这个的实现。

要回答两个问题（cover letter 原话的复述）：LLC 按什么顺序被考虑，以及线程组要沿这个顺序铺多远。

- 顺序：以 preferred LLC 所在 node 的**距离矩阵行**给 node 排序；node 内部另建一张「没有物理含义、只用于排序」的 LLC 距离矩阵；其它 node 内按 LLC ID 升序。三者拼成一条 affinity sequence。因为真实 node 距离里一行会出现相同值，所以需要一张**每行数值唯一**的 node 距离矩阵（即 sched-20260901-004 那片）。
- 铺多远：估算整个 thread group 的总利用率，取能装下它的**最小前缀**；前缀内的 LLC 只要自身能装下这个任务就可以进（**不要求前序 LLC 先饱和**），前缀之外才退回原来的有序饱和检查。

被放弃的备选（cover 里明确写了，对判断合入难度很有用）：原本想给每个进程的线程组维护一张 LLC mask。两条理由否掉——mask 在 `task_cache_work()` 里更新、在 load balancing 里读，负载快速变化时读到的是过期值；且 load balance 找 source `sched_group`/rq 时**没有 task 上下文**去取对应的 mask。因此改为 task-independent 的每 rq / per-sd 聚合计数（patch 08/09/10 那组）。

## 技术方案

系列分五段（cover 的 patch organization）：1-6 建拓扑基础设施（`llc_to_node()`、唯一化 node 距离、node/LLC 遍历宏、新增 `sd_node` 调度域）；7-10 收集 preferred-NUMA 信息并加 per-sd 状态；11-16 实现 LLC 粒度的迁移决策（affinity gain、source rq/group 选择、可迁移判定、active balance 允许扩到别的 LLC）；17-19 处理与 NUMA balancing 的交互；20-22 估算整线程组利用率并推导 LLC 容量范围；23 暴露 preferred LLC 供调试。

与本日 6 个子线程直接相关的三处：

- **patch 08（本日定案）**：`numa_counts[]` 是 `llc_counts[]` 的节点级投影，作者原理由是粒度（NUMA 级打分 `numa_counts[node] * distance_delta` 与 NODE 级按 LLC 打分），维持成本只有一次 `llc_to_node()` O(1) 查表加入队/出队各一次自增。PZ 把取舍重新摆正：

  > Consider the trade-off. Adding the accounting adds a cache-miss to every enqueue/dequeue, while re-computing the value on-demand adds some little cost to the balancing (slow) path. If the llc_counts[] array is dense in node order, then it is likely all relevant numbers are in a single line and computing the sum is in fact fairly cheap.

  作者接受，**v3 将删除 `numa_counts[]` 改为按需累加 LLC 计数**。
- **patch 14**：`group_llc_balance` 可以绕过 `prefer_sibling`。PZ 说 `Not sure about blanked disable. Maybe only disable when cache aware scheduling is present and enabled?` 作者论证该分支只能由 `llc_balance()` 选中，而后者在 cache-aware 未激活时立即返回 false、`CONFIG_SCHED_CACHE` 关闭时 stub 也产不出 `group_llc_balance`，因此不存在无 CAS 时绕过 `prefer_sibling` 的路径——**这是一条已澄清而非待改的意见**。
- **patch 17/18（方向性分歧）**：本系列试图拆出 NUMA task 迁移与 page 迁移的独立开关（Chen Yu 在 v1→v2 阶段建议的 tunable）。PZ 明确反对拆，也反对「NUMA 与 LLC 谁优先」做成可切换：

  > At every point NUMA migration should take precedence over LLC. The remote node penalty is much greater than the 'other' llc penalty. … Disabling page-migration or numa task-migration separately completely wrecks things and you might as well just disable NUMA balancing.

  并给出他认可的形式：`Now, if the process spans multiple nodes we should go do the same again as this patch set does for llc, spread/interleave over the minimal set of nodes that do fit.`——即把本系列对 LLC 做的「最小前缀铺开」原样搬到 node 维度。

## 版本演进与当前进展

v1（2026-06-25，`https://lore.kernel.org/all/20260625030759.25928-1-wujianyong@hygon.cn/`）→ **v2（08-27，cover `<20260827122816.756234-1-wujianyong@hygon.cn>`）**，12 条 changelog：不再按调度域边界扩资源、新增行内唯一的 node 距离矩阵、新增 node 内 LLC 距离矩阵、改 affinity gain 算法、改迁移许可判定、修 schbench 饱和问题、把线程组所有 preferred node 纳入扫描范围、加 NUMA task/page 迁移独立开关（Chen Yu 建议）、估算整线程组利用率推导 LLC 容量范围、允许在该范围内跳过低序未饱和 LLC、从 preferred LLC 起遍历 preferred node、修 debug print 的 bug（Xiao Wu 建议）。

v2 的评审进展：08-31~09-01 PZ 集中跟读。本日**尚未有 v3**，但已确定要进 v3 的改动有：删 `numa_counts[]`（08/23）、给 `numa_counts`/per-sd scratch 数组补 `__counted_by_ptr(numa_max)` 与 `__counted_by_ptr(llc_max)` 注解（08/23、10/23）、commit message 补动机说明（09/23）。

作者自己的定位是求方向确认：`This patch set is far from perfect and still contains some unresolved issues. Before proceeding further, I would like to confirm whether I am heading in the right direction.`

## Maintainer 意见与讨论焦点

PZ 是本系列**唯一**评审者，12 封回帖里可分四层：

1. **认可并给方向**：affinity sequence + 按需扩范围这套骨架没有被质疑；09/23 的要求是「大系列必须写清 *why*」——`I mean, I can read the patch and see what it does, but I cannot divinate … why you're doing things. This is esp. important for large series -- or series that do complicated things -- or like this case: both!` 作者答应在 commit message 补。
2. **要求删除冗余状态**：08/23 的 `numa_counts[]`（见上，已定案删除）。
3. **代码级正确性**：`__counted_by_ptr` 注解（08/23、10/23）、`mul_u64_u32_shr()` 替 `mul_u64_u32_div()`（20/23，理由是后者内联 asm 无法优化除法）、inverse x-mas-tree 变量序与折行（11/23，见 sched-20260901-007）。
4. **架构级反对**：17/23 的 NUMA/LLC 优先级与双开关，**这是唯一没有当场被作者接受、也没有被作者反驳的分歧**——本日邮件里作者对 17/23 未回帖。加上 11/23 里 `can_migrate_node()` 与既有 `can_migrate_llc()` 的三处口径分叉（sched-20260901-007），PZ 的读后结论倾向于「先证明这两份逻辑为何不能合并成一个函数」。

另有一处只被 PZ 点破、双方都未展开的语义问题：17/23 的多节点循环里「跳过 target 与 src 之间那些 locality 更好的节点」与后面用「更近节点」来否决迁移互相矛盾（原样记录在 sched-20260901-007）。

## 合入评估

`likelihood = medium`，且**本季度内进 tip 的可能性低**。支持面：唯一评审者是 PZ 且在逐片跟读、方向（LLC 粒度扩展）就是他本人提的、基准数据在 2S/8node/每 node 4LLC 的 Hygon 机器上是正向且给出复现命令。阻塞面按分量排：

1. 17/23 与 NUMA balancing 的关系没谈拢——作者要把 task/page 迁移拆开可关，PZ 说这样会把 NUMA balancing 拆坏；这一条决定系列后三分之一是否重写。
2. LLC 粒度迁移决策与既有 `can_migrate_llc()` 并存而非泛化，评审意见倾向于「先合并」。
3. 新增 `sd_node` 调度域层与「不按调度域边界扩资源」之间的一致性需要在 v3 交代（v2 刚改掉这条）。
4. 平台证据只有 Hygon 一家，作者自己也写 `Further testing across a wider range of workloads and hardware platforms is needed`。

## 效果评估

cover 给出完整数据（基线 = 同树 `0f23d56f17fd` 且已带 `CONFIG_SCHED_CACHE`，两边都设 `numa_balancing=0`、`aggr_tolerance=90`，每项 ≥20 次取均值；括号内为标准差占均值百分比）：

- **hackbench -T -p（18 个配置）**：16 个更快，中位提升 **27.7%**；中段最明显（`-f 8 -g 1` 0.654 → +34.6%，`-f 12 -g 1` 0.646 → +35.4%）；两端收敛。两处变慢：`-f 48 -g 2` 为 **-4.1%**（超出噪声，唯一真回退）、`-f 32 -g 2` -0.15%（噪声内）。run-to-run 方差在 12/18 个配置改善，小端最明显（baseline 30-59% vs llc_gran 4-27%）。
- **schbench p99 wakeup latency（11 个线程数）**：**全部** 改善，中位 **16.8%**，10/11 超出噪声；峰值在 48/64 线程（+33.0% / +35.3%），128 线程 +4.8% 落在噪声内。方差在 8/11 个线程数改善，但 96/128 线程时反而高于基线（15-18% vs 3-5%）。
- 作者对两个负向结果的态度是 `The root cause … will be investigated in future work`——即 **48 管道 hackbench 回退与高线程数下 p99 抖动变大的根因未定位**。这是本系列目前唯一有数字支撑、也唯一没有解释的问题。

## 我可以参与的点

- **PZ 与作者在 17/23 上的分歧正对主线**：「NUMA 迁移恒定优先于 LLC」+「跨多 node 的进程应在装得下的最小 node 前缀上 spread/interleave」是一条可直接实现也可以证伪的命题。若自家有 2/4/8 node 且业务按 node 绑核（cpuset 收紧）的环境，给出「PZ 形态 vs 作者的双开关形态」在同类负载上的对比数据，比再加一份功能测试有分量。
- **补平台维度**：作者点名要更宽硬件覆盖。非 Hygon 拓扑（尤其每 node LLC 数不均、带 CCD/簇结构的平台）上跑他给的 hackbench/schbench 脚本并回帖，是最廉价的介入点，也能提前判断这套 affinity sequence 在自家拓扑上是否会退化。
- **可提前评估的回合风险**：`sd_node` 新调度域层 + `per-sd scratch` + 唯一化距离矩阵都会改变 `rebuild_sched_domains()` 的产物形状，与 cpuset/isolcpus 触发的域重建有交叉；即便不回合本系列，这套拓扑扩展的形状值得先看清。
- **v3 待发**：删 `numa_counts[]` 后 NUMA 级打分改走「按需累加 llc_counts」，届时 `llc_counts[]` 在 node 序上的稠密性（决定它是否落在一根缓存行内）就是新补丁的关键前提，值得在 v3 发出时第一个去核。

## 参考链接

- cover letter (v2): https://lore.kernel.org/all/20260827122816.756234-1-wujianyong@hygon.cn/
- cover letter (v1): https://lore.kernel.org/all/20260625030759.25928-1-wujianyong@hygon.cn/
- patch 08/23 PZ 取舍质疑: https://lore.kernel.org/all/20260901102127.GY687043@noisy.programming.kicks-ass.net/
- patch 08/23 作者接受并删 numa_counts: https://lore.kernel.org/all/80ded281acca43a28043b261e850250c@hygon.cn/
- patch 09/23 PZ「写清 why」: https://lore.kernel.org/all/20260901075457.GO4120091@noisy.programming.kicks-ass.net/
- patch 10/23 `__counted_by_ptr(llc_max)`: https://lore.kernel.org/all/20260901080210.GP4120091@noisy.programming.kicks-ass.net/
- patch 14/23 prefer_sibling 质疑: https://lore.kernel.org/all/20260901102917.GH776954@noisy.programming.kicks-ass.net/
- patch 17/23 PZ 反对拆开关: https://lore.kernel.org/all/20260901124736.GI776954@noisy.programming.kicks-ass.net/
- patch 20/23 `mul_u64_u32_shr()` 建议: https://lore.kernel.org/all/20260901144449.GJ776954@noisy.programming.kicks-ass.net/
- tip-bot commit: 未获取到（RFC）
- stable backport: 未获取到

---
id: sched-20260901-015
subject: "sched: Scale cache-aware aggregation at LLC granularity"
date: '2026-09-01'
subsystem: sched
type: feature
status: rfc
severity: none
thread_root_msgid: "<20260827122816.756234-1-wujianyong@hygon.cn>"
lore_url: "https://lore.kernel.org/all/20260827122816.756234-1-wujianyong@hygon.cn/"
authors: [Jianyong Wu, Peter Zijlstra]
maintainers_involved: [Peter Zijlstra, Chen Yu]
current_version: v2
patch_series:
  - version: v1
    msgid: "<20260625030759.25928-1-wujianyong@hygon.cn>"
    date: '2026-06-25'
    summary: '首版 23 片：按调度域边界扩资源、LLC 聚合'
    review_outcome: 'PZ 建议改为按 LLC 粒度扩资源；Chen Yu 建议拆分 NUMA task/page 迁移开关'
  - version: v2
    msgid: "<20260827122816.756234-1-wujianyong@hygon.cn>"
    date: '2026-08-27'
    summary: '12 条改动：去掉按 sd 边界扩资源、新增行内唯一 node 距离矩阵与 node 内 LLC 距离矩阵、改 affinity gain 与迁移许可算法、按线程组利用率推导 LLC 容量范围、线程组全部 preferred node 纳入扫描'
    review_outcome: '08-31~09-01 PZ 逐片跟读：08/23 numa_counts 判掉改按需求和、09/23 要求补动机、10/23 补 __counted_by_ptr、14/23 澄清后接受、17/23 反对拆分 NUMA 开关、20/23 换 mul_u64_u32_shr'
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
  - "patch 17/23 与 PZ 的方向分歧：作者要 NUMA task/page 迁移独立开关，PZ 认为拆开即 wreck，应改为按最小 node 前缀 spread/interleave；作者当日未回应"
  - "can_migrate_node() 与既有 can_migrate_llc() 并存而非泛化，评审倾向先合并（见 sched-20260901-007）"
  - "48 管道 hackbench -4.1% 回退与高线程数 p99 方差变大，作者自陈根因未定位"
  - "硬件覆盖仅 Hygon 一台，作者明确要求更多平台数据"
  next_action: "v3 落实 numa_counts 删除/计数注解/commit message 动机，并就 17/23 的方向给出答复"
contribution_opportunities:
  - kind: discussion
    description: "在自有 2/4/8 node 平台上对比 PZ 提议的『NUMA 优先 + 最小 node 前缀 spread』与作者的双开关方案，回帖给出数据"
  - kind: testing
    description: "在非 Hygon 拓扑（每 node LLC 数不均、CCD/簇结构）跑 cover 给出的 hackbench/schbench 脚本并回帖"
  - kind: review
    description: "v3 发布后核对 llc_counts[] 在 node 序上的稠密性——它决定按需累加是否真在一根缓存行内"
source_email_count: 24
related_articles:
  - "sched-20260901-004"
  - "sched-20260901-005"
  - "sched-20260901-006"
  - "sched-20260901-007"
  - "sched-20260901-011"
tags:
- load_balance
- numa_balancing
- topology
generated_at: '2026-09-07'
---
