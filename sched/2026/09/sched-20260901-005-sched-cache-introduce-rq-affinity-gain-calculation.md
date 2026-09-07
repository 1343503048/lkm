# sched/cache: Introduce rq affinity gain calculation

## TL;DR

Jianyong Wu（海光）RFC v2 的 12/23 是整个「亲和性打分」系列的计算核心：在 `llc_balance()` 的候选目标上，用 `Σ(偏好该 LLC/NUMA 节点的任务数 × 距离增益)` 替代原来「任务偏好 LLC 是否等于目的 LLC」的二值判断。09-01 Peter Zijlstra 对该片提了两条正确性/冗余问题（用不稳定的全局 `max_lid` 做数组上界、多余的 `memset()`），作者当日均接受，并顺带暴露了一个关键事实：`llc_max` 只在 base sched domain（`rq->sd`）上被赋值，`env->sd` 上是 0。

## 背景与问题

`CONFIG_SCHED_CACHE` 的 cache-aware 负载均衡在挑选迁移目的时，依赖 sched_group 上累积的偏好统计（`nr_pref_dst_llc` 等）：一个任务被放到它「偏好」的 LLC 上才算收益，判断是二值的。这在单 LLC 粒度下够用，但跨 NUMA 或者同节点内多 LLC 的场景下会出现「往哪边挪、能赚多少」无法比较的问题——所有非当前偏好的目标得分都是 0，负载均衡拿不到连续量，也就无法在「换 LLC」和「换节点」之间排序。

12/23 要补的就是这个连续量：把 02/23 的去重距离矩阵、08/23 的 rq 级 `llc_counts[]`/`numa_counts[]` 偏好计数，组合成一个可以横向比较的 affinity gain（分数）。这是 12/23 存在的理由，也是前面所有拓扑补丁的消费者。

## 技术方案

新增两层打分函数，结构对称：

- `get_affi_llcs(sd, src_llc, dst_llc, affi_llcs, affi)`：枚举「在同一 NUMA 节点内、离 `dst_llc` 比离 `src_llc` 更近」的所有 LLC，`src_llc == dst_llc`、`sd->flags & (SD_NUMA | SD_SHARE_LLC)`、或 src/dst 不同节点时直接返回 0（不打分）。
- `get_affi_numas(src_node, dst_node, affi_nodes, affi)`：节点层的同构版本，枚举离目的节点更近的节点。
- 权重取距离差并夹逼：LLC 层 `affi[j] = clamp(src_llc - dst_llc, 1, 1024)`，NUMA 层 `affi[j] = clamp(src_dist - dst_dist, 4, 1024)`。**下限 1 / 4 意味着「一次节点级亲近」的最低权重被人为设为一次 LLC 级亲近的 4 倍。**
- `calc_affinity_llc_score()` / `calc_affinity_numa_score()`：`score += sd->llc_counts[affi_llc[i]] * affi[i]`（节点层用 `sd->numa_counts[]`），即「偏好该目标的任务数 × 距离增益」求和；下层用 `if ((unsigned int)affi_llc[i] < sd->llc_max)` 做越界保护。
- 结果缓存：用 `*last_llc` / `*last_node` 判断源是否变化，只有源变化时才重算亲和集合，输入/输出数组来自 10/23 在 sched_domain 上开的 per-sd scratch，避免热路径分配。

关键取舍：**全局 `max_lid` vs per-sd 的 `sd->llc_max`**。作者最初把数组上界写成全局最大 LLC id（并为此在遍历前 `memset()` 整段数组），Peter 指出这两处都不成立（见下节）。

## 版本演进与当前进展

v2 于 2026-08-27 发出，Peter 09-01 对本片回帖 2 条，作者当日回 2 条，全部已给出 v3 动作：

1. `get_affi_llcs()` 的 `for (int i = 0; i <= max_lid; i++)` 被判定不安全。作者确认 `max_lid` 不稳定，但补充了实现约束：`get_affi_llcs()` 收到的是 `env->sd`，而 `llc_max` 只在 base sched domain（`rq->sd`）上设置，`env->sd->llc_max` 为 0；解决办法是把 `calc_affinity_llc_score()` 已持有的 base `sd->llc_max` 作为参数传下去，而不是在 `env->sd` 上就地取用。
2. 三处 `memset(affi_node/affi_llc/affi, 0, (max_lid + 1) * sizeof(int))` 被质疑多余，作者确认 `get_affi_*()` 从下标 0 起直接赋值、求和只读返回的 `*num` 项，其余元素从不被读，v3 删除 `memset()`。

同时这条线还挂着 08/23 的结论：`numa_counts[]` 记账被要求删掉、改成按需累加，而本片的 `calc_affinity_numa_score()` 正是 `sd->numa_counts[]` 的唯一消费者，v3 里这段循环必然随之改写。

## Maintainer 意见与讨论焦点

- **Peter Zijlstra（数组上界，`<20260901095840.GR4120091@noisy.programming.kicks-ass.net>`）**：`This isn't safe. max_lid isn't stable, you should use sd->llc_max which matches the actual allocation size of sd->llc_counts.` —— 他的理由不是风格，而是**缓冲区大小由 sd 的分配决定**，用全局 id 上界遍历会越过 `sd->llc_counts` 的实际分配长度。这是本片唯一的实质性正确性问题。
- **Peter Zijlstra（多余清零，`<20260901101607.GG776954@noisy.programming.kicks-ass.net>`）**：`Why do we need the memset()? AFAICT the get_affi_*() functions use direct assignment and the sum is limited to the number returned.` —— 他把 patch 里三处 `memset()` 串起来看（`This and... ... this.`），认定是无效工作。
- **作者的回应价值**：`get_affi_llcs() receives env->sd, whose llc_max is 0 - llc_max is only set on the base sched domain (rq->sd)` 这句话是本日系列里最有信息量的一条——它说明 `llc_max` 的语义是「base domain 的属性」，后续任何在 `env->sd` 上想用 LLC 维度的补丁都不能直接读 `sd->llc_max`，需要显式传递。这个约束目前没有写进任何 commit message。
- **无人质疑的部分**：`clamp(..., 1, 1024)` 与 `clamp(..., 4, 1024)` 这两组常数、以及 `score` 用 `int` 累加是否会溢出，Peter 当日没有评论。

## 合入评估

`likelihood = unknown`。本片本身是纯新增的计算函数，改动局部、可测试，但它是 23 片 RFC 的第 12 片，依赖 02/23（去重距离矩阵）、08/23/09/23（`llc_counts[]`/`numa_counts[]` 记账）、10/23（per-sd scratch）全部先落地；而其中 08/23 的 `numa_counts[]` 已被要求删除，意味着本片的 NUMA 层循环还没定型。当日没有任何 `Reviewed-by`/`Acked-by`，Peter 仍在逐片精读阶段。要推进，作者需要先把「记账 vs 按需累加」这一层定下来，再谈打分本身。

## 效果评估

**本日邮件中无任何效果数据**：没有 benchmark，也没有「二值偏好判断 vs 距离加权打分」的对比。可以量化只有静态规模：本片段新增约 174 行（Peter 回帖引用的 diff 头 `@@ -11998,6 +11999,174 @@`），其中打分函数两个、亲和集合枚举函数两个。打分权重的标度（LLC 下限 1、NUMA 下限 4、上限 1024）是作者直接给出的魔数，**未获取到**任何推导或实测依据，因此「这样标定是否合理」目前无法评估。

## 我可以参与的点

- **最空缺的一条：为 `clamp()` 的上下限提供依据。** LLC 用 `1..1024`、NUMA 用 `4..1024`，等价于硬编码「节点亲近 ≈ 4 倍 LLC 亲近」，且 1024 的上限在距离矩阵去重后（02/23 的 `Δ` 量级）是否还可达都不清楚。这一条主评审人当日没提，属于可以直接回帖补的实质意见。
- **溢出与类型**：`score` 为 `int`，`llc_counts[]`（任务数）× 距离增益的乘积累加，在千任务级 rq 上有溢出可能；`get_affi_*()` 返回 `int` 项数、数组按 LLC 数量定长，也值得确认边界。
- **实现约束值得沉淀**：`llc_max` 仅存在于 base sched domain 这一事实，目前只出现在邮件里。若你在做类似消费 per-sd LLC 数组的补丁，这是一个容易复现的坑。
- **回合判断**：本片依赖 `CONFIG_SCHED_CACHE` 与 `sched_domain` 布局变更，OLK-6.6 不具备 02/08/09/10/23 等前置补丁，短期无单独回合价值；但「距离加权替代二值偏好判断」这一思路，对我们自定义的 LLC 亲和策略有直接参考意义。

## 参考链接

- 12/23 补丁本体（v2, 2026-08-27）: https://lore.kernel.org/all/20260827122816.756234-13-wujianyong@hygon.cn/
- Peter Zijlstra（`max_lid` 不安全）: https://lore.kernel.org/all/20260901095840.GR4120091@noisy.programming.kicks-ass.net/
- 作者（`llc_max` 仅在 base sd）: https://lore.kernel.org/all/97476ef46a42491f83599fac8fe4c8d6@hygon.cn/
- Peter Zijlstra（质疑 memset）: https://lore.kernel.org/all/20260901101607.GG776954@noisy.programming.kicks-ass.net/
- 作者（确认删除 memset）: https://lore.kernel.org/all/e92cc24da4c94d6d9d20383921adf5da@hygon.cn/
- 同系列 08/23 讨论（`numa_counts[]` 删除）: https://lore.kernel.org/all/80ded281acca43a28043b261e850250c@hygon.cn/
- tip-bot commit: 未获取到（RFC）
- stable backport: 未获取到

---
subject: "sched/cache: Introduce rq affinity gain calculation"
id: sched-20260901-005
date: '2026-09-01'
subsystem: sched
type: feature
status: rfc
severity: none
thread_root_msgid: null
lore_url: "https://lore.kernel.org/all/20260901095840.GR4120091@noisy.programming.kicks-ass.net/"
authors: [Jianyong Wu, Peter Zijlstra]
maintainers_involved: [Peter Zijlstra]
current_version: v2
patch_series:
  - version: v2
    msgid: '<20260827122816.756234-13-wujianyong@hygon.cn>'
    date: '2026-08-27'
    summary: 'RFC v2 第 12 片：新增 get_affi_llcs()/get_affi_numas() 枚举"离目的比离源更近"的 LLC/节点，calc_affinity_llc_score()/calc_affinity_numa_score() 以 Σ(偏好任务数 × clamp(距离差)) 计算亲和性增益，替代原有的二值偏好判断；结果按 last_llc/last_node 缓存，数组取自 10/23 的 per-sd scratch'
    review_outcome: 'Peter Zijlstra 两条意见均被作者接受：(1) 用不稳定的全局 max_lid 做数组上界不安全，应改用与 sd->llc_counts 分配长度一致的 sd->llc_max；(2) 三处 memset() 多余。作者补充 llc_max 只在 base sched domain 有效，v3 将以参数下传'
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
  - '23 片 RFC 的第 12 片，依赖 02/08/09/10/23 全部前置；其中 numa_counts[] 已被要求删除，本片 NUMA 层循环尚未定型'
  - '待落实：以 base sd->llc_max 作参数下传替代 max_lid；删除多余 memset()'
  - 'clamp(1,1024)/clamp(4,1024) 的标度无任何推导或实测依据，主评审人当日未评论，属未决风险'
  - '无 Reviewed-by/Acked-by，Peter Zijlstra 仍在逐片通读'
  next_action: '发 v3 落实上界与清零修正，并为 LLC/NUMA 两级权重标度给出量化依据'
contribution_opportunities:
  - kind: review
    description: '质疑并帮助标定 clamp(src-dist, 1, 1024) 与 clamp(src-dist, 4, 1024) 两组常数：1:4 的 LLC/NUMA 权重比与 1024 上限从何而来，去重矩阵下距离差是否可达上限'
  - kind: review
    description: '检查 int score 累加 llc_counts[]（任务数）× 距离增益在千任务 rq 上的溢出风险'
  - kind: new_patch
    description: '把 "llc_max 仅在 base sched domain 有效、env->sd 上为 0" 这一约束写入 commit message 或注释，避免后续 per-sd LLC 数组消费者重复踩坑'
source_email_count: 4
related_articles: [sched-20260901-004, sched-20260831-005]
tags:
- load_balance
- numa_balancing
generated_at: '2026-09-07'
---
