# sched/cache: Prioritize preferred NUMA node selection over LLC selection

## TL;DR

Jianyong Wu 的 23 片 RFC v2 里，「谁优先」这条设计主线在 09-01 被 Peter Zijlstra 正面否掉一次：他明确写出 **NUMA 迁移在任何时候都应优先于 LLC**，并据此认为 17/23「把任务迁移与页迁移拆成两个开关」的前提不成立。同日还有两条较小的定论：14/23 里 `prefer_sibling` 的无条件禁用被作者证明其实已被 `llc_balance()` 限定在 cache-aware 路径内；20/23 的 `mul_u64_u32_div()` 被建议换成 `mul_u64_u32_shr(..., NICE_0_LOAD_SHIFT)`。

## 背景与问题

本系列把「线程组偏好的 LLC」这个锚点从单层升级为两层：先按线程组在各 NUMA 节点上的占用量选出偏好节点，再在该节点内选出偏好 LLC，锚点存在 `mm->sc_stat.cpu`（进程级）。作者给出的动机是：当负载铺满整机、且每个 LLC 的 CPU 数很少时，单层偏好 LLC 会频繁漂移。为防止锚点抖动，切换阈值取 2 倍（`if (m_a_n_occ > 2 * curr_m_a_n_occ) new_cpu = m_a_n_cpu;`）。

另一侧的冲突来自 17/23：现有 NUMA balancing 把任务迁移和页迁移耦合成一个开关，而 cache-aware 负载均衡（CAS）只靠任务迁移聚合任务，两者同时开启会互相拉扯。17/23 的做法是让二者可独立开关。

## 技术方案

- **两级偏好选择**（07/23）：`get_scan_cpumasks()` 把三类候选折进扫描掩码——`p->numa_preferred_nid`、当前偏好 LLC 所在节点、当前运行节点；然后在候选中按占用量挑选，节点优先、节点内再选 LLC。
- **2 倍迟滞**：新锚点的占用必须超过旧锚点 2 倍才切换。作者注释里给的理由是「2X 意味着新偏好 LLC 至少比旧的多 1 个忙 CPU（200% vs 100%）」。
- **`WRITE_ONCE(mm->sc_stat.cpu, new_cpu)`**：锚点无锁读、单点写。
- **14/23**：把 `sds.prefer_sibling` 从 `sched_balance_find_src_group()` 的分支条件里摘出来，只在 `group_llc_balance` 之外的另一半条件上保留，使 `group_llc_balance` 不再受 sibling 偏好约束。
- **17/23**：拆分 NUMA balancing 的 task-migration / page-migration 开关。
- **20/23**：按线程组整体估算利用率，`mm_util = mul_u64_u32_div(cpu_util, min_t(unsigned long, occ, NICE_0_LOAD), NICE_0_LOAD)`。

被否掉/待定的备选：**「硬优先使用 NUMA balancing 的偏好节点」**，作者明确不采纳（理由见下节）；Peter 则从反方向要求整个系列的优先级次序应当以 NUMA 为纲，这实际上否掉了 17/23 的独立开关方案。

## 版本演进与当前进展

v2（2026-08-27 发出）在本日于 4 个补丁上产生结论：

- **07/23**：作者答复 Peter 08-31 的两条意见。(a) 注释里「as it did when the two updates were applied in that order」这类引用旧代码的表述删除；(b) 解释了为什么只把 `numa_preferred_nid` 当候选而不是硬优先。
- **14/23**：作者论证 `prefer_sibling` 旁路本就被限制在 cache-aware 内——`group_llc_balance` 只有在 `llc_balance()` 返回真时才可能被选中。当日未看到该论证是否说服 Peter。
- **17/23**：Peter 判定方向性不成立，作者当日未回应。
- **20/23**：待改为 `mul_u64_u32_shr()`。

## Maintainer 意见与讨论焦点

- **Peter Zijlstra（17/23，`<20260901124736.GI776954@noisy.programming.kicks-ass.net>`）——本日最重的一条，接近 NAK**：

  `Sorry, but this doesn't make sense. At every point NUMA migration should take precedence over LLC. The remote node penalty is much greater than the 'other' llc penalty.`

  以及 `Disabling page-migration or numa task-migration separately completely wrecks things and you might as well just disable NUMA balancing.`

  他还给出自己认为正确的下一步：`Now, if the process spans multiple nodes we should go do the same again as this patch set does for llc, spread/interleave over the minimal set of nodes that do fit.`——即把本系列在 LLC 维度做的「最小覆盖集合内摊开」复制到节点维度。这条既是反对意见，也是本系列的重构方向。
- **Peter Zijlstra（07/23，08-31）**：`Hmm, if we're going to look at nodes, should we not also consider the numa balancing preferred node, and perhaps priorize an llc inside that node, rather than the occupancy wise busiest node?`
- **作者的反驳（07/23，本日）——一个真实的粒度冲突**：`numa_preferred_nid is per-task while the preferred LLC is per-process. Different threads of the same process can hold different preferred nodes, so prioritizing any one of them would make the process-wide preferred LLC bounce between nodes.` 这个「per-task 的 NUMA 偏好 vs per-process 的 LLC 锚点」矛盾在本日无人跟进，是后续版本必须解决的结构性问题——Peter 要求的「NUMA 优先」在进程级锚点模型下无法直接实现。
- **Peter Zijlstra（14/23）**：`Not sure about blanked disable. Maybe only disable when cache aware scheduling is present and enabled?`
- **Peter Zijlstra（20/23）**：`mul_u64_u32_shr(..., NICE_0_LOAD_SHIFT); will probably generate better code -- I *think* the mul_u64_u32_div() ends up being inline asm and as such cannot optimize the divide properly.`
- **风格类**：`Comments should never refer to old code that no longer exists. Comments are for the code as it is now. ... that's what the Changelog is for.` 作者当日照单采纳。

## 合入评估

`likelihood = unknown`，且本日出现了系列发出以来第一条方向性反对意见。17/23 被 Peter 用「NUMA 优先于 LLC」的第一性原理正面否定，而 07/23 的两级偏好选择正是建立在这个次序被模糊处理的基础上：作者的「把 NUMA 偏好节点当候选、让占用量决定」策略与 Peter 的原则冲突，作者给出的 per-task/per-process 粒度反驳当日没有得到回应。加上 08/23 的 `numa_counts[]` 已被要求删除、11/23 被逐行质疑（另见 sched-20260901-007），v3 面对的不是修修补补而是要重排优先级模型。无任何 `Reviewed-by`/`Acked-by`。

## 效果评估

作者为 2 倍迟滞常数写过 `3. 2X is chosen based on test results, as it delivers the optimal performance gain so far.`——**但本日的邮件里没有任何具体数字**：没有平台规格、没有负载、没有对比曲线，无法评估「2X 是最优」这一结论。除该定性陈述外，07/14/17/20 四片在本日均无效果数据。

## 我可以参与的点

- **粒度冲突是最值得下场的一点**：per-task `numa_preferred_nid` 与 per-process `mm->sc_stat.cpu` 的矛盾目前是作者单方面陈述、无人反驳也无人解。可提出的方向是把锚点下沉到 per-task 并只做进程级一致性收敛，或反之让 NUMA 偏好也进程级化——cpuset/cgroup 视角尤其关心「谁最终决定进程落在哪个节点」。
- **替 Peter 把话说清楚**：他建议的「跨多节点时在最小可满足节点集合上摊开/交织」尚无实现，也没有人量化它与现有 `mempolicy`/`set_mempolicy` 语义的关系。若你有 NUMA 交错策略与调度器协同的实现经验，这一条是明确空缺。
- **2 倍阈值的可证伪性**：若手上有每 LLC CPU 数较小的机型（正是作者声称的抖动场景），复现「单层偏好 vs 两级偏好」的锚点漂移次数与性能差异，可以直接支撑或推翻 07/23 的动机。
- **小改动可代做**：20/23 的 `mul_u64_u32_shr(..., NICE_0_LOAD_SHIFT)` 属零风险清理，作者 v3 前如果有人先把整系列同类除法都排查一遍，是低成本贡献。
- **回合判断**：`prefer_sibling` 与 `group_llc_balance` 的交互（14/23）在 OLK-6.6 的 `sched_balance_find_src_group()` 里同样存在，即使本系列不合入，这段条件改写的取舍也值得对照自有分支评估。

## 参考链接

- 07/23 作者答复（per-task vs per-process）: https://lore.kernel.org/all/82a9b1c118424a48a0b70439ddae6905@hygon.cn/
- 07/23 作者答复（删除引用旧代码的注释）: https://lore.kernel.org/all/62e8081a9432407893fb6a9a8e397d87@hygon.cn/
- 17/23 Peter Zijlstra（NUMA 优先，方向性反对）: https://lore.kernel.org/all/20260901124736.GI776954@noisy.programming.kicks-ass.net/
- 14/23 Peter Zijlstra: https://lore.kernel.org/all/20260901102917.GH776954@noisy.programming.kicks-ass.net/
- 14/23 作者答复: https://lore.kernel.org/all/a064643f494b45c9bb0b8290308a1329@hygon.cn/
- 20/23 Peter Zijlstra（mul_u64_u32_shr）: https://lore.kernel.org/all/20260901144449.GJ776954@noisy.programming.kicks-ass.net/
- 17/23 补丁本体（v2, 2026-08-28）: https://lore.kernel.org/all/20260828020731.785556-1-wujianyong@hygon.cn/
- tip-bot commit: 未获取到（RFC）
- stable backport: 未获取到

---
subject: "sched/cache: Prioritize preferred NUMA node selection over LLC selection"
id: sched-20260901-006
date: '2026-09-01'
subsystem: sched
type: feature
status: rfc
severity: none
thread_root_msgid: null
lore_url: "https://lore.kernel.org/all/20260901124736.GI776954@noisy.programming.kicks-ass.net/"
authors: [Jianyong Wu, Peter Zijlstra]
maintainers_involved: [Peter Zijlstra]
current_version: v2
patch_series:
  - version: v2
    msgid: '<20260828020731.785556-1-wujianyong@hygon.cn>'
    date: '2026-08-28'
    summary: 'RFC v2 的优先级/次序层：07/23 先选偏好 NUMA 节点再选节点内偏好 LLC（2 倍占用迟滞，WRITE_ONCE 更新 mm->sc_stat.cpu）；14/23 去掉 group_llc_balance 的 prefer_sibling 约束；17/23 拆分 NUMA balancing 的任务迁移与页迁移开关；20/23 按线程组估算利用率'
    review_outcome: 'Peter Zijlstra 对 17/23 给出方向性反对（"At every point NUMA migration should take precedence over LLC"、"Disabling page-migration or numa task-migration separately completely wrecks things"）；对 07/23 质疑为何不硬优先 numa_preferred_nid（作者以 per-task vs per-process 粒度反驳）；14/23 质疑无条件禁用；20/23 建议 mul_u64_u32_shr；要求注释不得引用已不存在的旧代码'
  - version: v1
    msgid: null
    date: null
    summary: 'v1 未在本日与相邻日缓存中出现，具体差异未获取到'
    review_outcome: '未获取到'
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues:
  - '17/23 的前提被主评审人以"NUMA 迁移始终优先于 LLC"否定，作者当日未回应'
  - 'per-task 的 numa_preferred_nid 与 per-process 的 mm->sc_stat.cpu 粒度冲突无解，直接阻碍 Peter 所要求的 NUMA 硬优先'
  - 'Peter 建议的"跨节点时在最小可满足节点集合上摊开/交织"尚无实现'
  - '2 倍迟滞常数的"基于测试结果"无任何数据支撑'
  - '无 Reviewed-by/Acked-by'
  next_action: '作者需在 v3 重排 LLC/NUMA 优先级模型并正面回应 17/23 是否撤回；同时补出 2X 阈值的实测依据'
contribution_opportunities:
  - kind: discussion
    description: '就 per-task NUMA 偏好与 per-process LLC 锚点的粒度冲突提出可选建模（锚点下沉到 task 并做进程级收敛，或 NUMA 偏好进程级化）'
  - kind: discussion
    description: '评估 Peter 提出的"在最小可满足节点集合上 spread/interleave"与现有 mempolicy 语义的边界，该方向目前无人接手'
  - kind: testing
    description: '在每个 LLC CPU 数较少的机型上量化单层 vs 两级偏好选择的锚点漂移，验证 2X 阈值是否真的最优'
  - kind: new_patch
    description: '把全系列中 mul_u64_u32_div(..., NICE_0_LOAD) 一类写法统一替换为 mul_u64_u32_shr(..., NICE_0_LOAD_SHIFT)'
source_email_count: 6
related_articles: [sched-20260901-004, sched-20260901-005, sched-20260901-007, sched-20260831-005]
tags:
- numa_balancing
- load_balance
- topology
generated_at: '2026-09-07'
---
