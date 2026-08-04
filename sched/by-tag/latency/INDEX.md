# tag: latency

共 2 篇

- [sched-20260804-021](../../2026/08/sched-20260804-021-cpufreq-cppc-resource-priority-sysfs.md) `feature/under_review` — CPPC v4（Resource Priority）新增 sysfs 接口，允许设置每个 CPU 的 CPPC 资源优先级，与 sched 的 uclamp/latency 偏好呼应，在共享电源域下影响硬件调度决策。v4 整合多轮反馈，合入可能性 medium（sysfs ABI 待确认）。
- [sched-20260804-022](../../2026/08/sched-20260804-022-intel_idle-avoid-deep-idle-during-init.md) `fix/low/under_review` — intel_idle 在初始化/early 阶段若进入 deep idle 状态，可能在某些平台引起唤醒延迟异常或初始化时序问题。Zhang Rui 改为初始化期间避免 deep idle，完成后再允许。低严重度修复，合入可能性 medium，待平台确认。
