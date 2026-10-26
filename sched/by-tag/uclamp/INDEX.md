# tag: uclamp

共 3 篇

- [sched-20261026-002](../../2026/10/sched-20261026-002-sched-uclamp-fix-race-condition-leading-to-imbalanced-uclamp.md) `fix/medium/under_review` — 本文为增量更新，完整脉络见 related_articles。
- [sched-20261025-001](../../2026/10/sched-20261025-001-sched-uclamp-fix-race-condition-leading-to-imbalanced-uclamp.md) `fix/medium/under_review` — Qais Yousef 发单补丁修 uclamp 的 static key 非原子翻转导致的 runqueue 计数失衡竞态：`sched_uclamp_used` 使能瞬间部分 CPU 走 uclamp 快路径、部分不走，跨 CPU 的 enqueue/dequeue 不对称会使 `uclamp_rq` 计数永久错位。方案不试图堵住竞态，改为「视为既成事实 + idle 入口纠错」。kernel
- [sched-20261016-010](../../2026/10/sched-20261016-010-sched-uclamp-validate-min-max-pair-under-task-rq-lock.md) `fix/medium/under_review` — Hui Su 修复 `sched_setattr()` 中 UCLAMP_MIN/MAX 的校验竞态：两次不同的 `sched_setattr()` 调用可以在拿锁前各自基于同一份旧值通过校验，最终留下 `min > max` 的非法 `uclamp_req`。补丁把「任务相关」的 min/max 配对校验移到 `task_rq_lock()` 之后（更新已串行化），并拒绝一起提交的反向对。作者用
