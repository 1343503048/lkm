# sched/fair: Avoid overflow in place_entity()

## TL;DR

Hui Su 修复 `place_entity()` 里的 s64 溢出：`lag * (load + weight) / load` 在除法前就可能因 `lag * (load + weight)` 的中间乘积溢出 s64，即使最终商可表示，也会破坏 EEVDF 实体的虚拟 lag 放置。修复把表达式重写为等价的 `lag + lag * weight / load`，避免用虚拟 lag 乘以总运行队列权重。补丁附了 UBSAN、`__int128` oracle 十万随机用例、x86_64/i386/arm64 构建等多重验证，v1 刚发出。

## 背景与问题

（bug/fix 类）`place_entity()` 用 `lag * (load + weight) / load` 放大实体的虚拟 lag。commit 4823725d9d1d（"sched/fair: Increase weight bits for avg_vruntime"）把此计算里原先经 `scale_load_down()` 缩小过的权重换成 `avg_vruntime_weight()`，去掉了算术余量。即便最终商可表示，乘法本身也可能先溢出 s64。触发条件与量级：组调度下任务的层级有效权重经 `avg_vruntime_weight()` 缩放后可小到 2，而 `entity_lag()` 把 |vlag| 限制在 `calc_delta_fair(cfs_rq_max_slice(cfs_rq) + TICK_NSEC, se)`；以 HZ=1000、NICE_0_LOAD=1048576、最小缩放层级权重 scale_load(2)=2048 为例，该界为 891289600，114 个最大权重实体时运行队列 load 达 10361604096，中间乘积 891289600 × (10361604096 + 2) = 9235189971864780800，溢出 s64 并破坏实体放置。

## 技术方案

把 `lag * (load + weight) / load` 重写为等价的 `lag + lag * weight / load`。二者等价，但后者不再用虚拟 lag 去乘总运行队列权重；`entity_lag()` 把 vlag 限制在实体自身有效权重下，所以剩下的 `lag * weight` 乘积保持有界。`rescale_entity()` 跨 h_load 变化时保持该缩放，且在 rescale vlag 时已依赖同一乘积。保留原有零 load 警告语义：在把除数替换为 1 后再乘 weight。改动集中在 `kernel/sched/fair.c` 的 `place_entity()`（12 insertions, 3 deletions）。

## 版本演进与当前进展

*current_version: v1*，28 日发出，暂无 review 回复。补丁自带测试：UBSAN 正/负溢出用例、零 load/控制路径、64 位与未缩放 32 位地标、10 万随机用例对照 `__int128` oracle 全部 PASS；完整 x86_64 内核构建、`kernel/sched/fair.o` 的 i386/arm64 构建也通过。

## Maintainer 意见与讨论焦点

无维护者或社区回应。这是一处带 `Fixes:` 标签的明确正确性修复，且有系统化测试背书，但 EEVDF 路径维护者（Peter Zijlstra、Vincent Guittot 等）尚未表态。

## 合入评估

*likelihood=unknown*。v1 刚发出、无人回复，但属有 `Fixes:` 标签、有测试背书的正确性修复，一旦有维护者细读，合入概率较高。*blocking_issues*：无评审反馈；需维护者确认重写后的 `lag + lag * weight / load` 在边界（零 load、极值 weight）下与原式语义完全一致。*next_action*：等待 EEVDF 维护者 review；如需加速可补充实际复现（组调度 + 极端权重下的放置偏差）回帖。

## 效果评估

作者给的是正确性验证（UBSAN + oracle 对照 + 多架构构建），非性能数据。溢出在最终商可表示时才破坏放置，属静默正确性问题，无性能量化。

## 我可以参与的点

- `testing`：在启用组调度（cgroup v2 cpu controller）的机器上构造极端权重场景，实测修复前后 `place_entity()` 的放置行为差异并回帖。
- `review`：核对 `lag + lag * weight / load` 重写是否在所有 `avg_vruntime_weight()` 缩放下保持等价，尤其零 load 警告分支的语义保留。

## 参考链接

- 补丁: https://lore.kernel.org/all/20260928124754.1692077-1-sh_def@163.com/

---
id: sched-20260928-005
date: '2026-09-28'
subject: 'sched/fair: Avoid overflow in place_entity()'
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: '<20260928124754.1692077-1-sh_def@163.com>'
lore_url: 'https://lore.kernel.org/all/20260928124754.1692077-1-sh_def@163.com/'
authors:
  - 'Hui Su'
maintainers_involved: []
current_version: v1
patch_series:
  - version: v1
    msgid: '<20260928124754.1692077-1-sh_def@163.com>'
    date: '2026-09-28'
    summary: '把 lag * (load + weight) / load 重写为 lag + lag * weight / load 避免 s64 溢出'
    review_outcome: '暂无 review'
upstream_commit: null
fixes_commit: 4823725d9d1d
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues:
    - '无评审反馈，需确认重写式与原式在边界下等价'
  next_action: '等待 EEVDF 维护者 review'
contribution_opportunities:
  - kind: testing
    description: '组调度 + 极端权重场景实测修复前后放置行为并回帖'
  - kind: review
    description: '核对重写式在所有 avg_vruntime_weight 缩放下的等价性'
generated_at: '2026-09-29T01:00:00'
source_email_count: 1
related_articles: []
tags:
  - eevdf
  - cfs
---