# tag: cpuidle

共 2 篇

- [sched-20260821-011](../../2026/08/sched-20260821-011-cpuidle-dt-idle-genpd-kfree-the-original-name-allocation.md) `fix/medium/under_review` — `dt_idle_pd_alloc()` 中 `pd->name` 指向 `kasprintf()` 分配内存的中间位置（`kbasename()` 偏移），`kfree()` 时触发内存错误。Linkai Gong 的修复改为直接 `kstrdup(kbasename(...))` 复制基名字符串。
- [sched-20260821-010](../../2026/08/sched-20260821-010-cpuidle-deny-idle-entry-when-cpu-already-have-ipi-interrupt-pending.md) `fix/medium/under_review` — v2 补丁尝试在 CPU 已有 IPI 中断挂起时阻止进入 idle 状态，但 Daniel Lezcano 认为这应该在 idle loop 而非 cpuidle 框架中处理，Maulik Shah 的 v2 方案方向受到质疑。
