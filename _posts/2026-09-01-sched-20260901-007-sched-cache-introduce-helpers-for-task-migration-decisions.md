---
subject: 'sched/cache: Introduce helpers for task migration decisions'
id: sched-20260901-007
date: '2026-09-01'
subsystem: sched
type: feature
status: rfc
severity: none
thread_root_msgid: null
lore_url: https://lore.kernel.org/all/20260901090843.GQ4120091@noisy.programming.kicks-ass.net/
authors:
- Jianyong Wu
- Peter Zijlstra
maintainers_involved:
- Peter Zijlstra
current_version: v2
patch_series:
- version: v2
  msgid: <20260827122816.756234-12-wujianyong@hygon.cn>
  date: '2026-08-27'
  summary: 新增 can_migrate_node()（LLC/NUMA 通用迁移可行性判定，返回 mig_unrestricted/mig_llc/mig_forbid）与
    get_span_stats() 包装；含"削峰例外"（src 明显更重且多出 2*tsk_util 时即使目的越余量也放行）与以 mm->sc_stat.cpu
    为 anchor 的节点遍历、get_src 跳过 anchor→src 之间节点
  review_outcome: Peter Zijlstra 两封回帖：逐条列出与既有 can_migrate_llc() 的 3 处口径分叉（src 统计失败的处理、!p
    何时合法、未做 src_util -= tsk_util），另指出 dst 分支的无条件 return、指出跳过 nearest 节点却又依赖 nearest
    节点否决的自相矛盾、重复的 for_each_llc_node_span/get_span_stats 计算、get_span_stats 抽象无意义；另有
    inverse xmas ordering、缩进、逻辑运算符换行、superfluous else 等风格意见。当日作者未回复
- version: v1
  msgid: null
  date: null
  summary: v1 未在本日与相邻日缓存中出现，具体差异未获取到
  review_outcome: 未获取到
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: unclear
  blocking_issues:
  - can_migrate_node() 与 can_migrate_llc() 并存且统计口径分叉，主评审人要求解释为何不能只用一份实现
  - get_src 跳过 anchor→src 之间节点，与后续"更近 LLC 可否决迁移"的逻辑直接冲突，需给出结论
  - 两处 for_each_llc_node_span() + get_span_stats() 对同一批 span 重复计算
  - 函数在本片中标注 __maybe_unused，尚无消费者，无法用现有回归验证行为
  - 无 Reviewed-by/Acked-by，作者当日未回复
  next_action: 作者需逐条回答与 can_migrate_llc() 的差异是有意还是副本漂移，并解决节点遍历顺序与就近否决的矛盾；同时按社区风格重排变量声明
contribution_opportunities:
- kind: review
  description: 构造 anchor 与 src 相隔多节点的场景，判定 get_src 的 skip 是否使"更近 LLC 否决"失效，把 Peter
    的"confusing"变成一个明确结论
- kind: new_patch
  description: 给出把 can_migrate_llc() 与 can_migrate_node() 合并为单一按粒度参数化的实现草案，消除 Peter
    指出的 3 处口径分叉
- kind: testing
  description: 为"削峰例外"的 2*tsk_util 阈值补实测边界：什么条件下放行是净收益、什么条件下会造成往返迁移
source_email_count: 2
related_articles:
- sched-20260901-004
- sched-20260901-005
- sched-20260901-006
- sched-20260902-009
- sched-20260903-012
- sched-20260831-005
tags:
- load_balance
- topology
- numa_balancing
generated_at: '2026-09-07'
title: 'sched/cache: Introduce helpers for task migration decisions'
layout: article
---

## TL;DR

11/23 是 Jianyong Wu RFC v2 中「迁移可行性判定」这一层的实现补丁：把现有的 `can_migrate_llc()` 泛化成节点无关的 `can_migrate_node()`（LLC 与 NUMA 共用），并加 `get_span_stats()` 包装。Peter Zijlstra 用 09-01 一封逐行跟读的回帖给出了本日最密集的技术评审：**该函数与既有 `can_migrate_llc()` 存在 3 处口径分叉、1 处循环顺序自相矛盾、1 处重复计算**，其余为排版与 superfluous else。当日无作者回应，是本系列里最接近「重写」的一片。

## 背景与问题

现有的 `can_migrate_llc()` 只在 LLC 粒度回答「这个任务能不能从 src 挪到 dst」，返回 `enum llc_mig`（`mig_unrestricted` / `mig_llc` / `mig_forbid`）。本系列要把放置决策扩展到 NUMA 粒度（07/23 的两级偏好、12/23 的打分都需要一个跨粒度的可行性判定），因此需要一份「输入是任意 span（LLC 或 node）、判定逻辑同构」的 helper。11/23 提供的正是 `can_migrate_node(src_cpu, dst_cpu, p, to_pref)` 与 `get_span_stats(span, &util, &cap)`。

## 技术方案

- **两段判定**：`to_pref`（迁往偏好锚点）与「非偏好」路径分开。偏好路径先看 `fits_llc_capacity(dst_util, dst_cap)`，否则落入「削峰」例外。
- **削峰例外（peak-lowering escape）**：即使目的超过容量余量，只要 `src_cap && util_greater(src_util, dst_pre) && src_util >= dst_pre + 2 * tsk_util` 就放行。作者在注释里给出的理由是：如果同节点每个 LLC 都已越过余量线，一律拒绝会把峰值原地冻结（七任务的 LLC 永远是七，隔壁四任务的永远进不去），而第二条 `2 * tsk_util` 保证目的不会反过来变成更重的一方导致任务被弹回。
- **锚点起Walk**：`for_each_sched_node(target_cpu, node)` 以 `mm->sc_stat.cpu`（或 src_cpu）为 anchor 遍历节点，并用 `get_src` 标志跳过「anchor 到 src 之间」的节点——作者的解释是这些节点与本迁移无关（任务既不住那儿也不去那儿），让它们参与否决会被无关节点的余量误伤。
- **就近否决**：遍历更近的 LLC 时，必须把「该 LLC 若收下这个任务是否还装得下」一并计入（`acc_util + nu + tsk_util`），否则一个每核已放一任务的 LLC 会显得仍有空间并否决掉所有去往更远空闲 LLC 的迁移。

## 版本演进与当前进展

v2 的 11/23 在 09-01 收到 Peter 两封回帖（17:08 逐行跟读、19:32 排版），**当日作者未回复**，因此 v3 的具体动作尚不可知。已明确的待办：变量声明改成 inverse xmas ordering（Peter 直接给了改写后的样子）、`&&`/`||` 换行位置统一、消掉两处 superfluous else、减少缩进层级。

## Maintainer 意见与讨论焦点

Peter Zijlstra 全部意见都指向「与既有实现的对齐」，按分量排序：

1. **与 `can_migrate_llc()` 的口径分叉**（3 处，逐条对照）：
   - `Comparing against can_migrate_llc(), that bails with mig_unrestricted when !get_llc_stats(src_cpu).`（新代码把 `src_cap = 0` 继续往下走）
   - `It isn't clear when !p would be valid. migration is always about a task, no?`
   - `can_migrate_llc() also adjusts src_util by subtracting tsk_util (and flooring at 0).`（新代码只加了 `dst_util`）
   - 这三条合起来意味着 `can_migrate_node()` 不是 `can_migrate_llc()` 的泛化，而是又一份漂移过的副本。
2. **遍历顺序与自身注释矛盾**：先说 `So this iterates the nodes in the order specific to the node that contains target_cpu..`，随后 `And then you skip the nodes between target and src, which are the nodes with best locality, confusing, but lets read on..`，最后在就近否决处点破：`But you just skipped the nodes between target and src, those are nearer, no?` ——**这是本日唯一一条真正的逻辑级质疑：跳过的节点正是后面用来否决的「更近节点」。** 另附 `(sometimes target == src, and you thus don't skip anything, but other times this is the preferred cpu)`。
3. **无条件返回**：对 dst 分支里的 `return mig_forbid;` 标注 `This is an unconditional return..`，即整个多节点循环实际只看第一个含 dst_cpu 的节点。
4. **重复计算**：`This is shared with the above loop, meaning you're now duplicating this work in case you fell through.`（两处 `for_each_llc_node_span()` + `get_span_stats()` 对同一批 span 各算一遍）
5. **抽象层级存疑**：`@span is the span of the llc, but get_span_stats() is a wrapper around get_llc_stats(), and since span is just a single llc, why use this rather than get_llc_stats() directly?`
6. **风格**：`We prefer inverse xmas ordering -- where possible. So please go through the code and re-arrange things.`、`(indent is getting a little out of hand here)`、`(logical operators go at the end of the previous line, your patch is inconsistent on this point, since that is what you do elsewhere)`、`Strictly speaking this else is superfluous.`

值得强调：**「削峰例外」那套 2×tsk_util 阈值逻辑，Peter 本日没有评价**。这可能是最需
要社区检验的部分，却是唯一没被读的部分。

## 合入评估

`likelihood = unclear`。这一片是打分/放置决策的入口，逻辑密度高却与既有 `can_migrate_llc()` 并存而非替换，Peter 的跟读结论倾向于「先证明两者为何不能合并成一函数」。其中第 2 条（跳过 nearest 节点又用 nearest 节点否决）如果不成立，片子的行为会与设计意图相反，属必须修正项。当日无 `Reviewed-by`/`Acked-by`，也无 NAK。

## 效果评估

**暂无效果数据**。本日邮件里既没有 `can_migrate_node()` 的开销测量（它对每次迁移判定引入一次多节点 × 多 LLC 的 `get_span_stats()` 遍历，Peter 已指出其中一半是重复计算），也没有削峰例外所声称场景的实测样本。该片标注 `__maybe_unused`，说明在本片中还没有消费者，行为无法通过现有负载回归验证。

## 我可以参与的点

- **最容易出成果的一条：把 nearest 节点被跳过又被用于否决这个矛盾做成明确结论**。可以照着 diff 构造一个 4 节点、anchor 与 src 相隔 2 个节点的场景，说明 `get_src` 的 skip 究竟会不会让「更近 LLC 的否决」失效。作者当日还没回，抢先给出清晰分析是有效贡献。
- **`can_migrate_llc()` / `can_migrate_node()` 的合并方案**：Peter 的 4 条对照其实是在暗示应该只有一份实现。可以试着给出参数化（granularity 传入 + 统计口径统一）的合并 diff，比逐条修更容易被接受。
- **削峰例外的 2×tsk_util 没有数据支撑**：如果有人能给出「什么条件下放行是净收益」的形式化或实测边界，正好补上本日无人评价的空白。
- **回合判断**：`can_migrate_llc()` 在 OLK-6.6 已存在，其 `!get_llc_stats(src_cpu)` 的处理与 `src_util -= tsk_util` 口径是回合该系列时必须对齐的点；本片也提示我们：任何在 cache-aware 路径新增判定函数的改动，都要防止变成第二份副本。

## 参考链接

- 11/23 补丁本体（v2, 2026-08-27）: https://lore.kernel.org/all/20260827122816.756234-12-wujianyong@hygon.cn/
- Peter Zijlstra 逐行跟读: https://lore.kernel.org/all/20260901090843.GQ4120091@noisy.programming.kicks-ass.net/
- Peter Zijlstra（inverse xmas ordering）: https://lore.kernel.org/all/20260901113207.GZ687043@noisy.programming.kicks-ass.net/
- tip-bot commit: 未获取到（RFC）
- stable backport: 未获取到
