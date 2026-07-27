# tag: sched_ext

| 文章 | type/severity/status | 一句话摘要 |
|---|---|---|
| sched-20260726-001-sched-make-proxy-execution-compatible-with-sched-ext.md | feature / none / under_review | proxy execution 兼容 sched_ext（v9），处理 owner 属 SCX 时的代理执行与迁移 |
| sched-20260726-002-sched-ext-bound-per-task-reenqueues-and-eject-the-owning-scheduler.md | feature / none / under_review | 给 per-task re-enqueue 设上限，超限即 eject 坏 BPF 调度器回退默认（v2） |
| sched-20260726-004-sched-ext-sparse-annotation-cleanups.md | fix / low / merged_tip | sparse 注解清理三连，已 apply 到 sched_ext/for-7.3 |
| sched-20260726-005-sched-ext-fix-incorrect-scx-pick-idle-cpu-flag-prefix-in-kernel-doc.md | fix / low / merged_tip | 修正 SCX_PICK_IDLE_CPU_* kernel-doc 前缀，已 apply 到 for-7.3 |
| sched-20260726-007-selftests-sched-ext-make-allowed-cpus-idle-validation-race-free.md | fix / medium / under_review | 修 WAKE_SYNC waker CPU 未标 busy + 重写 allowed_cpus selftest 消除竞态 |
