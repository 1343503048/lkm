# tag: syzbot

共 2 篇

- [sched-20260907-002](../../2026/09/sched-20260907-002-sched-irq-cpu-hotplug-race-vs-set-cpus-allowed-ptr.md) `bug/medium/rfc` — Sebastian Andrzej Siewior（linutronix）09-07 16:58 发出 RFC：syzbot 报出的一个 CPU 热插拔与 `set_cpus_allowed_ptr()` 的竞态——IRQ 线程在 `irq_thread_check_affinity()` 里请求迁移到一个「当时在线、但可能马上掉线」的 CPU，`__migrate_task()` 被 `is_c
- [sched-20260809-006](../../2026/08/sched-20260809-006-kasan-slab-use-after-free-in-owner-on-cpu-via-iava-remove-mu.md) `bug/high/under_review` — 2026-08-09 收到 3 封 KASAN use-after-free 报告（通过 iavf、dw_edma_pcie、bna 三种驱动触发），根因相同：mutex 乐观自旋读取 owner 任务的 `on_cpu` 字段时任务结构体已释放。属 high 严重度崩溃类 bug，尚无修复 patch。
