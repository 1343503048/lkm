# tag: cpuidle

共 4 篇

- [sched-20260824-002](../../2026/08/sched-20260824-002-sched-cpufreq-reevaluate-tickless-idle.md) `fix/low/under_review` — `sugov_hold_freq()` 可能在 runqueue 转空时保持 UCLAMP_MIN 驱动的高频率，若随后 cpuidle 停掉 tick，CPU 将在整个 idle 期间维持不必要的高电压；此补丁在 tick 停止前发出最后一次频率更新。
- [sched-20260824-001](../../2026/08/sched-20260824-001-sched_ext-cgroup-init-cpu-idle.md) `fix/low/under_review` — sched_ext cgroup 初始化时遗漏了 cpu.idle 状态传递，导致已配置为 idle 的 cgroup 在调度器加载后被误报为 non-idle；v2 修复后获得 Andrea Righi Reviewed-by，合入前景良好。
- [sched-20260821-011](../../2026/08/sched-20260821-011-cpuidle-dt-idle-genpd-kfree-the-original-name-allocation.md) `fix/medium/under_review` — `dt_idle_pd_alloc()` 中 `pd->name` 指向 `kasprintf()` 分配内存的中间位置（`kbasename()` 偏移），`kfree()` 时触发内存错误。Linkai Gong 的修复改为直接 `kstrdup(kbasename(...))` 复制基名字符串。
- [sched-20260821-010](../../2026/08/sched-20260821-010-cpuidle-deny-idle-entry-when-cpu-already-have-ipi-interrupt-pending.md) `fix/medium/under_review` — v2 补丁尝试在 CPU 已有 IPI 中断挂起时阻止进入 idle 状态，但 Daniel Lezcano 认为这应该在 idle loop 而非 cpuidle 框架中处理，Maulik Shah 的 v2 方案方向受到质疑。
