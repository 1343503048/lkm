# tag: performance

共 3 篇

- [sched-20260824-009](../../2026/08/sched-20260824-009-sched-flatten-the-pick.md) `discussion/high/under_review` — 本文为增量更新，完整背景见 related_articles 中的文章。社区成员在类似硬件上成功复现了 0day 报告的性能回退，定位到 `wake_affine_weight()` 在 concur 模式下因 `task_h_load()` 返回值增大而改变了负载均衡决策，导致 L2 miss 率上升和吞吐量下降。Peter Zijlstra 表示 `task_h_load()` 行为异常，正在
- [sched-20260822-003](../../2026/08/sched-20260822-003-steal-governor-v10-benchmark-3-5pct-regression.md) `discussion/under_review` — steal_governor v10 系列收到 Yury 的独立测试：steal ratio 成功收敛，但整体性能比基线差 3-5%。作者需要调查性能回退原因。
- [sched-20260821-003](../../2026/08/sched-20260821-003-sched-flatten-the-pick-v3-benchmark.md) `discussion/under_review` — PeterZ 的"sched: Flatten the pick"系列 v3 讨论继续，IBM 工程师在 tip:sched/core 最新基线上重复了 benchmark，对比扁平 pick 层级与当前实现的性能差异。系列仍在 review 中。
