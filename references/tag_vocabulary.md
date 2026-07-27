# 受控标签词表

生成文章的 `tags` 字段必须从这里选取，保证长期检索口径一致。可多选。
如果确实需要新增标签，先在这里追加一行（附一句说明），再在文章里使用，不要私自造词导致标签碎片化。

## 调度子模块
- `sched_ext` — sched_ext（SCX）可扩展调度类，含 BPF 调度器、DSQ、idle 跟踪等
- `cfs` — 完全公平调度器（CFS core）
- `eevdf` — EEVDF 调度算法相关
- `rt` — 实时调度类（SCHED_FIFO/SCHED_RR）
- `deadline` — SCHED_DEADLINE
- `load_balance` — 负载均衡
- `numa_balancing` — NUMA 负载均衡/内存迁移
- `cgroup` — cgroup 调度控制（cpu/cpuset controller）
- `psi` — Pressure Stall Information
- `cpufreq` — 与 CPU 频率调节的交互
- `idle` — idle 任务/idle governor 相关
- `core_sched` — core scheduling（超线程隔离）
- `preempt` — 抢占相关（PREEMPT_RT等）
- `topology` — 调度域/CPU拓扑
- `uclamp` — utilization clamping
- `dl_server` — deadline server（RT 调度中重要概念，SCHED_DEADLINE 的 server 机制）
- `nohz` — NOHZ/TICKLESS 相关（NOHZ_FULL、NOHZ_IDLE、tickless 调度）
- `affinity` — CPU 亲和性（cpumask、set_affinity、亲和性迁移）
- `thermal` — 热管理相关调度（与 thermal pressure 的交互）
- `autogroup` — autogroup 调度（/proc/sys/kernel/sched_autogroup）
- `rt_bandwidth` — RT 带宽控制（RT runtime、rt_bandwidth 限制）
- `sched_debug` — sched_debugfs / 调试接口（/proc/sched_debug、debugfs）
- `sched_clock` — 调度相关时钟处理（sched_clock、CLOCK_MONOTONIC 等）

## 问题性质（配合 type 使用，不重复 type 本身）
- `regression` — 明确的性能/行为回退
- `hang` — 死锁/挂起类问题
- `crash` — 崩溃/panic/oops类
- `syzbot` — syzbot 自动报告命中
- `perf` — 纯性能优化（非bug）

## 架构/平台限定（不涉及则不打）
- `arm64`
- `x86`
- `riscv`
- `hyperthreading`

## 使用示例
一个关于 EEVDF 在 NUMA 场景下负载均衡回退的 bug：
`tags: [eevdf, load_balance, numa_balancing, regression]`
