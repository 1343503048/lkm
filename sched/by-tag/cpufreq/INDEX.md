# tag: cpufreq

共 1 篇

- [sched-20260903-010](../../2026/09/sched-20260903-010.md) `patch_series/medium/under_review` — cpufreq 压力（`cpu.capacity` 因频率限制而下降）用于让调度器感知降频带来的算力损失。本系列延续 09-02 的 cpufreq pressure 讨论：仅在频率「不变（invariant）」的 CPU 上施加 cpufreq 压力，避免在频率本身随负载变化的平台上重复/错误地折算算力，导致任务放置与频率选择相互放大。