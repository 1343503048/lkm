# tag: sched_debug

共 4 篇

- [sched-20260729-007](../../2026/07/sched-20260729-007-perf-sched-latency-refine-outputs-unit-scaling-and-histogram.md) `feature/under_review` — Aaron Tomlin 的 perf sched latency 改进系列更新到 v4（07-26 的 v3 已收录为 sched-20260726-003，本篇为增量分析）：v4 集中解决 pipe mode 支持问题并加固 NULL 防护。工具类改动、迭代活跃、意见都被逐条回应，合入可能性高。
- [sched-20260729-006](../../2026/07/sched-20260729-006-sched-debug-introduce-per-cpu-debugfs-files.md) `feature/under_review` — Aaron Tomlin 的 v2 补丁在 debugfs 下为每个 CPU 增加独立的调度调试文件 `/sys/kernel/debug/sched/cpu/cpu<N>/debug`，避免排查单 CPU 问题时读全量 `/sys/kernel/debug/sched/debug`。v2 已回应 v1 全部意见，等待维护者表态，可关注但非紧急。
- [sched-20260728-004](../../2026/07/sched-20260728-004-sched-debug-introduce-per-cpu-debugfs-files.md) `feature/under_review` — Aaron Tomlin 提出在 debugfs 下新增 per-CPU 调度调试文件 `/sys/kernel/debug/sched/cpu/cpu<N>/debug`，避免大型 SMP 系统上读取全量 debug 输出的开销。PeterZ 质疑使用场景，作者将重写 commit message 发 v2。有用户（DPDK/realtime 方向）表示支持。
- [sched-20260726-003](../../2026/07/sched-20260726-003-perf-sched-latency-refine-outputs-unit-scaling-and-histogram-support.md) `feature/under_review` — Aaron Tomlin 改进 `perf sched latency` 的第 3 版：修复缺少 tracepoint 时误报成功的 bug、为延迟/运行时列做单位自适应缩放（ns/us/ms/s）、新增延迟直方图与时间区间过滤。属于 perf 工具侧的可用性增强，已迭代到 v3、逐条回应了 review，合入可能性较高。
