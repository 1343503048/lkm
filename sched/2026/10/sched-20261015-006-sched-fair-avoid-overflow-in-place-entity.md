# sched/fair: Avoid overflow in place_entity()

## TL;DR
本文为增量更新，完整脉络见 related_articles。

- sched-20260928-005：Hui Su 修 `place_entity()` s64 溢出——`lag * (load + weight) / load` 除法前中间乘积就可能溢出，破坏 EEVDF 虚拟 lag 放置；改为等价 `lag + lag * weight / load`。
- sched-20261015-006（今天）：Peter Zijlstra 回帖给出自己的等价改写（`lag += div64_long(lag * weight, load)`，注释点明 `(W + w_i)*vl'_i` 会溢出 s64），Hui Su 认可该改写（仅 `WARN_ON_ONCE(!load)` fallback 有微小差异，判定为不变量违反路径、实际无影响）。方向一致、接近可收。

## 背景与问题
（承接 20260928-005）`place_entity()` 用 `lag * (load + weight) / load` 放大实体虚拟 lag；commit `4823725d9d1d` 把权重换成 `avg_vruntime_weight()` 后丢掉了算术余量，即便最终商可表示，乘法本身也可能先溢出 s64。0-9-28 的补丁把表达式重写为等价 `lag + lag * weight / load`。今天 Peter 独立给出同样的重写思路并注释了数学等价性：

```
vl_i = (W + w_i)*vl'_i / W = (W*vl'_i + w_i*vl'_i) / W = vl'_i + w_i*vl'_i/W
```

## 技术方案
（承接 20260928-005）核心是无溢出等价改写。今天 Peter 的 diff 与 Hui 原有补丁一致，仅结构略有不同：把 `WARN_ON_ONCE(!load) → load = 1` 早移、后置 `weight` 读取，再 `lag += div64_long(lag * weight, load)`。Hui 指出唯一语义差异在 `WARN(!load)` fallback：旧代码得到 `lag * weight`、新代码得到 `lag * (weight + 1)`（load 被置 1 后），但这是不变量违反路径，实际无影响。

## 版本演进与当前进展
- v1（2026-09-28，<20260928124754.1692077-1-sh_def@163.com>）：`lag * (load + weight) / load` → `lag + lag * weight / load` 重写。
- 今天（2026-10-15）：Peter Zijlstra review 原补丁并给出自己的等价改写 diff；Hui Su 表示对正常路径「looks good」，认可该改写。

## Maintainer 意见与讨论焦点
Peter Zijlstra 主动提供改写并把溢出机制写进注释，说明方案方向已被认可。无遗留实质分歧；唯一讨论点是 `WARN_ON_ONCE(!load)` fallback 路径的细微数值差异，双方均认为无关紧要。

## 合入评估
*likelihood=high*。维护者（Peter）亲自给出等价改写、作者认可，方向完全一致，无需再补充材料。*blocking_issues*：无实质阻塞，仅需 Hui 按 Peter 的 diff 落一版（或 Peter 直接改）。*next_action*：以 Peter 的改写为最终版提交或由 Peter 直接收取。

## 效果评估
原补丁附 UBSAN、`__int128` oracle 十万随机用例、x86_64/i386/arm64 构建验证；今天无新增量化数据。溢出触发条件（114 个最大权重实体时中间乘积 9.23e18 > s64 上限）为理论推演，未见真实触发现场。

## 我可以参与的点
当前阶段暂无明显参与空间，方案已收敛、等待落版合入；可持续观察后续版本。

## 参考链接
- Peter 的改写：https://lore.kernel.org/all/20261015094008.GW4120091@noisy.programming.kicks-ass.net/
- Hui 的回应：https://lore.kernel.org/all/20261015101030.e41fec0c-b3c4-42e9-982e-4f3d7750940c@163.com/
- 原补丁：https://lore.kernel.org/all/20260928124754.1692077-1-sh_def@163.com/

---
id: sched-20261015-006
date: 2026-10-15
subject: "sched/fair: Avoid overflow in place_entity()"
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: "<20260928124754.1692077-1-sh_def@163.com>"
lore_url: "https://lore.kernel.org/all/20260928124754.1692077-1-sh_def@163.com/"
authors: ["Hui Su"]
maintainers_involved: ["Peter Zijlstra"]
current_version: v1
patch_series:
  - version: v1
    msgid: "<20260928124754.1692077-1-sh_def@163.com>"
    date: 2026-09-28
    summary: "place_entity() 无溢出等价改写：lag * (load + weight) / load → lag + lag * weight / load"
    review_outcome: "Peter Zijlstra 给出等价改写并认可，Hui 确认"
upstream_commit: null
fixes_commit: "4823725d9d1d"
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: []
  next_action: "按 Peter 的改写落最终版或由 Peter 直接收取"
contribution_opportunities: []
generated_at: "2026-10-16T01:05:00"
source_email_count: 2
related_articles: ["sched-20260928-005"]
tags: [eevdf, cfs]
---