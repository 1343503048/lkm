# sched/topology: Add llc_to_node() to translate LLC id to NUMA node

## TL;DR

Jianyong Wu（Hygon）的 23 补丁 RFC v2 把 cache-aware scheduling（CAS）从"LLC 单层"扩成"NUMA 节点 + LLC 两级"偏好：先给 BIOS 的 NUMA 距离矩阵做**行内去重**得到唯一距离、再据此生成每节点/每 LLC 的亲和序列，让线程按序列跨节点、跨 LLC 聚拢。8/31  Peter Zijlstra 连发 6 帖，逐条质疑了 02/23 的去重算法界、04/23 的命名、07/23 与 NUMA balancing preferred node 的关系、08/23 新增计数器的必要性；作者已确认下一版把 `synchronize_rcu() + kfree()` 换成 `kfree_rcu_mightsleep()`。整体仍是 RFC，无 NAK 也无 ack，Peter 自称"还在往下读"。

## 背景与问题

主线 CAS 目前只在 LLC 粒度上做聚合：`mm->sc_stat.cpu` 记录该线程组偏好 CPU，判据是"哪个 LLC 上本组跑的时间最长"。问题在跨 NUMA 的大机器上：

- 优先 LLC 的抖动——当负载铺满全系统、尤其单个 LLC 上 CPU 数很少时，"最忙 LLC"会频繁翻覆，导致无谓迁移（07/23 的 commit message 就是这个动机）。
- 距离不可区分——BIOS 给的 NUMA 距离矩阵每一行里有大量相同值（例如 4 节点里的 20/20/20），无法据此排出"第二近、第三近"的迁移次序，聚合决策就退化成平局。

作者的对策是先在拓扑层造出**每行严格唯一**的距离，再用它生成亲和序列，使"先跨节点、再节点内换 LLC"的两级决策有确定的排序依据。

## 技术方案

- **01/23 `llc_to_node()`**：把 LLC id 翻译成所属 NUMA node，是后续两级决策的地基。
- **02/23 唯一距离矩阵**：以 BIOS 原始矩阵为输入，保持每行相对大小顺序不变、且保持主对角对称，把行内重复的距离值改成互不相同的值；每行升序排序后即为"该节点的亲和序列"。邮件里明确写这套 refined matrix **只服务 cache-aware scheduling，不影响调度域构建等既有 NUMA 拓扑逻辑**——这是该方案最重要的边界（也是它能作为 CAS 局部改动存在的前提）。
- **04/23 LLC 间距离**：`dist(LLC1, LLC2) = (rank1 + rank2) % k + 1`，其中 rank 是 LLC 在**本节点内**的局部序号、k 是本节点 LLC 总数，要求两 LLC 同节点；公式永不产生 0，所以对角自距离显式硬编码为 0。该方案只保证"从某个参考 LLC 看出去各 peer 距离互不相同"，不保证全系统任意 LLC 对唯一。
- **07/23 两级优先级**：先按"本组在该节点上的占用"选 preferred NUMA node，再在该节点内选 preferred LLC；切换判据是 2 倍阈值：

  ```
  if (m_a_n_occ > 2 * curr_m_a_occ)
      new_cpu = m_a_n_cpu;
  else if (pref_llc_cpu >= 0 && pref_llc_occ > 2 * curr_m_a_occ)
      new_cpu = pref_llc_cpu;
  if (new_cpu >= 0)
      WRITE_ONCE(mm->sc_stat.cpu, new_cpu);
  ```

  作者为 2X 给的三条理由：保持 preferred LLC 稳定比频繁改判更重要；2X 意味着新 preferred LLC 至少比旧的多一个忙 CPU（200% vs 100%）；2X 是"测试结果里目前最优"。
- **08/23 `sd->numa_counts`**：仿照已有 `sd->llc_counts`，记录每 rq 上偏好各 NUMA 节点的任务数。
- 备选方案：邮件里没有提出被放弃的第二套距离方案；争议是"用什么算法去重"与"要不要这个计数器"，而不是整条路线。

## 版本演进与当前进展

- v1 → v2（2026-08-27，`<20260827122816.756234-1-wujianyong@hygon.cn>`，23 补丁）。
- 8/29：Peter 开始逐 patch 回（01/23 的 `<20260829103102.GE776954@noisy.programming.kicks-ass.net>`）。
- 8/31：Peter 对 02/23、04/23、07/23、08/23 共 6 条意见；作者 17:43 对 01/23 答复并承诺改动。
- 已确认的 v3 改动（作者原话）："I'll replace synchronize_rcu() + kfree() with kfree_rcu_mightsleep() in the next version."——避免在 `llc_to_node()` 构建路径上同步等一个 grace period。
- 其余意见当天未答复，v3 尚未发出。

## Maintainer 意见与讨论焦点

Peter Zijlstra 一人提了全部实质意见，且都不是格式级：

1. **示例与代码粒度不符**（02/23）："This example uses Node only, but the code in question is specifically aimed at Cache granularity; might it be better to use a cache example?" 他还亲自写了一张 8 个 LLC 的 Pre/Post 矩阵贴回来，并自嘲这张表是"prompting Gemini 生成更复杂示例结果不可收拾"之后手写的。
2. **去重算法的质量**（02/23）："IIRC greedy has significant worse bounds than many other schemes. This would result in more unique distances than strictly needed here, right? Since this is all on slow paths anyway, does it make sense to pick a slightly better algorithm in order to reduce this bound and get better results?" 即：贪心去重会产出比实际需要更多的唯一距离，既然是慢路径，为什么不换界更好的算法。这是本系列**最实质的技术问题**，当天没有答复。
3. **命名误导**（04/23）："I got confused by your sched_cache_node_distance naming, and thought it was cache-to-cache distance."
4. **与 NUMA balancing 的关系**（07/23）："if we're going to look at nodes, should we not also consider the numa balancing preferred node, and perhaps priorize an llc inside that nore, rather than the occupancy wise busiest node?" 这是方向性问题——CAS 自己算"最忙节点"与 `task_numa` 的 preferred node 可能给出矛盾指引。同一帖还要求把过深缩进提成 helper。
5. **注释规范**（07/23）："Comments should never refer to old code that no longer exists. Comments are for the code as it is now... that's what the Changelog is for."
6. **新计数器的必要性**（08/23）："To what purpose? Is not the node occupancy the direct sum of its constituent llc occupancy?"——若节点占用可由 LLC 占用求和得到，`sd->numa_counts` 就是冗余；另问是否漏了 `__counted_by_ptr()` 标注（对比 `llc_counts __counted_by_ptr(llc_max)`）。
7. 收尾一句"Anyway, let me continue trying to dig through all this."——说明 Peter 当天并未读完 23 个补丁，后面还有意见要来。

## 合入评估

**possible**。有利：维护者在认真逐 patch review 且提的是可执行的工程问题（RCU 释放、命名、注释、helper 抽取、冗余计数器），没有一处质疑"该不该做跨节点聚合"；作者已在按意见调整并有明确 v3 计划。卡点：02/23 的去重算法界、07/23 与 NUMA balancing preferred node 的职责划分、08/23 计数器必要性三个问题都还没答复；系列 23 补丁偏大、且改动落在 `include/linux/sched/topology.h` 与 `kernel/sched/topology.c` 这种敏感位置；作者自称 2X 阈值"来自测试结果"但邮件里没有任何数据。

## 效果评估

暂无效果数据。当日线程里唯一与"效果"相关的表述是 07/23 注释中的"2X is chosen based on test results, as it delivers the optimal performance gain so far"——**作者主观判断，未见测试数据**，没有基准名、没有机器、没有对比数字。Peter 对 08/23 的"冗余计数器"质疑如果成立，还会带来一份 per-rq 数组的内存与更新开销白付。

## 我可以参与的点

- **补数据**：这是全系列最缺的东西。若手上有跨 NUMA、LLC 切分较碎的双路/多路机型，可测 2X 阈值与"两级优先"相对现有 LLC-only 的收益（吞吐 + 迁移次数），直接回 07/23——Peter 已明确要 test results。
- **回答 07/23 的方向性问题**：CAS 的 preferred node 与 NUMA balancing 的 preferred node 冲突时谁让步，是 Hygon/Intel/ARM 都要面对的；对 cpuset 场景（节点已被硬绑定）尤其值得说清楚"两者不冲突"或给出优先级建议。
- **回答 08/23**：从实现上确认 `sd->numa_counts` 能否由 `sd->llc_counts` 求和替代；这个判断只需要读 `build_sched_domains()` 的分配逻辑就能回帖。
- **回合评估**：该系列目前明确"不影响调度域构建"，对 OLK-6.6 属于可隔离的 CAS 增强；但 6.6 是否有等价的 CAS 框架需要先确认（CAS 主线落地时间晚于 6.6）。

## 参考链接

- lore thread（01/23，被讨论的首个补丁）: https://lore.kernel.org/all/20260827122816.756234-2-wujianyong@hygon.cn/
- 02/23 唯一距离矩阵: https://lore.kernel.org/all/20260827122816.756234-3-wujianyong@hygon.cn/
- 04/23 LLC 距离: https://lore.kernel.org/all/20260827122816.756234-5-wujianyong@hygon.cn/
- 07/23 两级优先级: https://lore.kernel.org/all/20260827122816.756234-8-wujianyong@hygon.cn/
- 08/23 per-CPU NUMA 偏好计数: https://lore.kernel.org/all/20260827122816.756234-9-wujianyong@hygon.cn/
- Peter 当日意见汇总: https://lore.kernel.org/all/20260831115004.GF776954@noisy.programming.kicks-ass.net/ 、 https://lore.kernel.org/all/20260831131643.GK4120091@noisy.programming.kicks-ass.net/ 、 https://lore.kernel.org/all/20260831132229.GL4120091@noisy.programming.kicks-ass.net/ 、 https://lore.kernel.org/all/20260831132414.GN4120091@noisy.programming.kicks-ass.net/
- tip-bot commit: 未获取到
- stable backport: 未获取到

---
id: sched-20260831-005
date: '2026-08-31'
subject: "sched/topology: Add llc_to_node() to translate LLC id to NUMA node"
subsystem: sched
type: feature
status: rfc
severity: none
thread_root_msgid: "<20260827122816.756234-1-wujianyong@hygon.cn>"
lore_url: "https://lore.kernel.org/all/20260827122816.756234-2-wujianyong@hygon.cn/"
authors: [Jianyong Wu, Peter Zijlstra]
maintainers_involved: [Peter Zijlstra]
current_version: v2
patch_series:
  - version: v2
    msgid: "<20260827122816.756234-1-wujianyong@hygon.cn>"
    date: 2026-08-27
    summary: "23 补丁：NUMA 距离矩阵行内去重 + LLC 距离公式 + preferred node 优先于 preferred LLC + sd->numa_counts，把 CAS 扩成节点/LLC 两级"
    review_outcome: "Peter Zijlstra 6 条意见：贪心去重界更差、sched_cache_node_distance 命名误导、应与 NUMA balancing preferred node 一并考虑、numa_counts 疑似可由 llc_counts 求和替代、注释不得引用已删除代码、synchronize_rcu 可改 kfree_rcu_mightsleep"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
    - "02/23 去重算法选用贪心、唯一距离数量多于实际需要，作者尚未回应是否换算法"
    - "07/23 与 NUMA balancing preferred node 的优先级关系未决"
    - "08/23 sd->numa_counts 的必要性被质疑（可能等于 LLC 占用求和）"
    - "2X 阈值声称来自测试但邮件内无任何 benchmark 数据"
  next_action: "作者需发 v3：换用 kfree_rcu_mightsleep()、改命名、抽 helper、补 benchmark，并回答去重算法与 numa_counts 两个问题"
contribution_opportunities:
  - kind: testing
    description: "在跨 NUMA/LLC 切分较碎的多路机型上测 2X 阈值与两级优先策略的收益（吞吐 + 迁移次数），回应 Peter 对测试数据的要求"
  - kind: discussion
    description: "就 CAS preferred NUMA node 与 NUMA balancing preferred node 冲突时的取舍给意见，尤其 cpuset 已硬绑定节点的场景"
  - kind: review
    description: "确认 sd->numa_counts 能否由 sd->llc_counts 求和替代，以及是否漏掉 __counted_by_ptr() 标注"
generated_at: "2026-09-07T21:16:22"
source_email_count: 7
related_articles: []
tags: [topology, numa_balancing, load_balance, x86]
---
