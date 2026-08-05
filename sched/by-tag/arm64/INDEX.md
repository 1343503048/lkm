# tag: arm64

共 4 篇

- [sched-20260805-012](../../2026/08/sched-20260805-012-arm64-separate-preempt-resched-bits.md) `feature/under_review` — arm64 分离 need_resched 与 preempt 的 resched 位 v4（向 x86 对齐）。Mark/Catalin 介入。延续 08-03-007。

- [sched-20260801-007](../../2026/08/sched-20260801-007-sched-preempt-count-cleanups-and-separate-resched-bits.md) `feature/under_review` — Boqun Feng 发出一个 24 patch 的 preempt_count 清理与重构系列，其中三个与调度核心直接相关：两个是 `kernel/sched/core.c` 中调试断言函数的参数与比较清理，一个是为 arm64 打开 `HAS_SEPARATE_PREEMPT_RESCHED_BITS`。改动本身低风险，但作为跨架构大系列，合入取决于整体协调。
- [sched-20260801-004](../../2026/08/sched-20260801-004-sched-fair-prefer-waker-cpu-non-smt-reciprocal-sync-wakeups-v3.md) `feature/under_review` — Shubhang Kaushik (Ampere) 试图让 pipe 式乒乓负载的互惠同步唤醒直接留在 waker CPU 上，在 80 核非 SMT Ampere Altra 上 `perf bench sched pipe` 提升约 30%。但 v3 采用的「非 SMT 才生效」二分法遭到 K Prateek Nayak 的结构性异议，后者给出了一份下推进 `select_idle_sibli
- [sched-20260726-006](../../2026/07/sched-20260726-006-sched-update-the-thread-info-in-task-description.md) `fix/low/stalled` — Huacai Chen 更新 `THREAD_INFO_IN_TASK` 的 Kconfig 描述，纠正一处过时且误导的说明（并非要删除除 flags 外的所有字段，实际只需移除 task_struct 指针字段）。补丁自 6/9 发出后一直无人 review，7/26 作者发出 "Gentle ping?" 催促，目前停滞。
