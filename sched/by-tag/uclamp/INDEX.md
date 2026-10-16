# tag: uclamp

共 1 篇

- [sched-20261016-010](../../2026/10/sched-20261016-010-sched-uclamp-validate-min-max-pair-under-task-rq-lock.md) `fix/medium/under_review` — Hui Su 修复 `sched_setattr()` 中 UCLAMP_MIN/MAX 的校验竞态：两次不同的 `sched_setattr()` 调用可以在拿锁前各自基于同一份旧值通过校验，最终留下 `min > max` 的非法 `uclamp_req`。补丁把「任务相关」的 min/max 配对校验移到 `task_rq_lock()` 之后（更新已串行化），并拒绝一起提交的反向对。作者用
