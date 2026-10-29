# sched/fair: Replace random newidle_balance with Bresenham accumulator

## TL;DR
Qing Wang 的 v3 补丁把 `newidle_balance` 里用随机掷骰（`sched_rng()`）决定「本次是否做负载均衡」的做法，换成 **Bresenham 累加器**——在 1024 次窗口内把允许的均衡次数**均匀铺开**，消除随机方差带来的「长时间不均衡」或「连续均衡」突发。今日讨论：Kayra Cizmeci 要求先给「突发是否有实际影响」的数据、否则倾向保留现状，并指出 v3 移除 `sched_rng()` 会在 Linus/tip 树上**编译报错**；作者承认 v3 在 `update_newidle_stats()` 里 `sd->newidle_window_pos = 0` 的 reset 是 bug（会丢弃未累计到 1024 的值），将发 v4 去掉该行。K Prateek Nayak 的 tbench 测试因带着这个 bug，不能反映 v4。

## 背景与问题
`newidle_balance` 在 CPU 进入 idle 时以一定概率尝试负载均衡。现行实现用随机数（`sched_rng()` 掷骰）决定是否均衡，作者认为：随机化在需要可预测性的内核机制里不理想——低 ratio 下可能「长时间不均衡」或「连续均衡几次」（几何分布），给调试/追踪带来不可复现的行为。动机是**确定性 + 可复现**，而非性能收益。

## 技术方案
用 Bresenham 式累加器替代随机掷骰：窗口 1024，每次 `pos += weight`，`pos >= 1024` 时 `pos -= 1024` 并允许一次均衡。这样给定 ratio 下均衡次数精确、间隔均匀、无突发。Peter Zijlstra 在 review 中给该路径加了「newidle balance throttling」，作者认可但实现方式上有不同看法。**今日暴露的关键 bug**：`update_newidle_stats()` 里 `sd->newidle_window_pos = 0;` 的 reset 是错的——作者原以为 `newidle_ratio` 每 1024 次调用更新一次，实际因 `newidle_call` 每次更新后减半、实际每 512 次更新，reset 会在累计到 1024 前就把值清零；且 `newidle_window_pos` 本就在 `[0,1024)` 内、无需 reset（残差可跨 ratio 更新自然延续）。v4 只需删掉这一行。

## 版本演进与当前进展
*current_version: v3*（v3 补丁 2026-10-28 发出，当日无缓存，msgid 未取到；v2 `<20261027093142.2337191-1-wangqing7171@gmail.com>`）。

- **v2**（2026-10-27）：首次引入 Bresenham 累加器。
- **v3**（2026-10-28）：据作者回帖，回应 Peter Zijlstra 的 review（含 newidle balance throttling），并做了 `newidle_window_pos` 重置逻辑——该重置即今日被确认的 bug。
- **今日**：Qing Wang 用 Python 仿真对比 Bresenham vs 随机（每 512 次调用把 ratio 随机到 [0,1023]，跑 20000 窗口/约 1000 万次调用）：Bresenham 每窗口最大误差 0.5 次，随机掷骰最大误差 41 次（约 16%）。作者承认无真机测试结果；Kayra 指出 Prateek 的 tbench 结果带 bug 不能反映 v4；作者承诺发 v4 删 reset 行并补 changelog 说明。

## Maintainer 意见与讨论焦点
- **Peter Zijlstra（维护者）**：给 newidle balance 路径加了 throttling 优化，作者认可方向、实现上有分歧（已在本线程展开）。
- **Kayra Cizmeci（今天，reviewer）**：核心质疑是**没有数据证明突发有实际影响**——「若无数据我倾向保留现状，不值得改」；并发现 v3 删 `sched_rng()` 导致 Linus/tip 树编译报 `implicit declaration of function 'sched_rng'`（`kernel/sched/fair.c:8663`）。
- **K Prateek Nayak（AMD）**：跑了 tbench，但结果基于带 bug 的 v3，作者请其在 v4 上重跑。
- 未解决焦点：价值论证（确定性 vs 随机是否有可测收益）仍是空的，Kayra 明确「无数据则保留现状」。

## 合入评估
*likelihood=low*。机制本身简单、作者响应积极，但 Kayra 的「无数据不保留现状」质疑尚未被数据回答，且 v3 还引入了编译错误（移除 `sched_rng()` 未清理引用）。*blocking_issues*：缺「突发有无实际影响」的 benchmark；v4 需确保不破坏构建（处理 `sched_rng()` 引用）；Prateek 的 tbench 需在 v4 上重跑。*next_action*：作者发 v4（删 reset 行 + 补 changelog 动机），并给出说明突发影响的真机数据，Prateek 在 v4 上重跑 tbench。

## 效果评估
仅作者 Python 仿真：Bresenham 每窗口最大误差 0.5 次 vs 随机 41 次（~16%），证明的是「均衡次数精确、无突发」，不是端到端性能收益。真机性能（tbench 等）数据尚无（Prateek 的 v3 结果带 bug 作废）。「突发有实际影响」目前是作者主观判断，未见数据。

## 我可以参与的点
- **testing**：在 v4 落地后跑 tbench/hackbench 等，对比 Bresenham vs 随机掷骰在低 newidle ratio 下的尾延迟/突发表现，补上 Kayra 要的「突发是否有影响」证据。
- **review**：核对 v4 是否彻底移除 `sched_rng()` 引用、`newidle_window_pos` 的边界与 carry-over 逻辑是否正确。

## 参考链接
- lore thread（v2）: https://lore.kernel.org/all/20261027093142.2337191-1-wangqing7171@gmail.com/
- Qing Wang 今日的仿真说明: https://lore.kernel.org/all/20261029093144.2469124-1-wangqing7171@gmail.com/
- Kayra Cizmeci 的质疑: https://lore.kernel.org/all/auL5Yok7oZrX79GG@scheduler.schedules/

---
id: sched-20261029-006
date: 2026-10-29
subject: "sched/fair: Replace random newidle_balance with Bresenham accumulator"
subsystem: sched
type: discussion
status: under_review
severity: none
thread_root_msgid: "<20261027093142.2337191-1-wangqing7171@gmail.com>"
lore_url: "https://lore.kernel.org/all/20261027093142.2337191-1-wangqing7171@gmail.com/"
authors: [Qing Wang]
maintainers_involved: [Peter Zijlstra]
current_version: v3
patch_series:
  - version: v2
    msgid: "<20261027093142.2337191-1-wangqing7171@gmail.com>"
    date: 2026-10-27
    summary: "引入 Bresenham 累加器替代随机掷骰决定 newidle 均衡"
    review_outcome: "Peter Zijlstra 加 newidle balance throttling，作者认可但实现有分歧"
  - version: v3
    msgid: null
    date: 2026-10-28
    summary: "回应 PZ review；update_newidle_stats() 里的 window_pos reset 引入 bug"
    review_outcome: "Kayra 指出删 sched_rng() 编译报错、要求突发影响数据；Prateek 的 tbench 带 bug 作废"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: low
  blocking_issues:
    - "缺「突发有无实际影响」的 benchmark 数据"
    - "v4 需处理 sched_rng() 引用避免编译报错"
    - "Prateek 的 tbench 需在 v4 上重跑"
  next_action: "作者发 v4（删 reset 行 + 补动机），给出突发影响的真机数据"
contribution_opportunities:
  - kind: testing
    description: "v4 落地后跑 tbench/hackbench 对比 Bresenham vs 随机在低 ratio 下的尾延迟/突发表现"
  - kind: review
    description: "核对 v4 是否彻底移除 sched_rng() 引用、window_pos 边界与 carry-over 逻辑"
generated_at: "2026-10-30T09:30:00"
source_email_count: 5
related_articles: []
tags: [load_balance]
---