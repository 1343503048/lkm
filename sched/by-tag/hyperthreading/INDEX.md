# tag: hyperthreading

共 10 篇

- [sched-20260806-002](../../2026/08/sched-20260806-002-sched-fair-nohz-fully-idle-core-v5.md) `feature/under_review` — NOHZ fully-idle-core 优先整核全 idle（SMT 兄弟判定）。延续 08-05-002。

- [sched-20260805-002](../../2026/08/sched-20260805-002-sched-fair-prefer-fully-idle-cores-nohz-v3-v4.md) `feature/under_review` — NOHZ fully-idle-core 优先整核全 idle（SMT 兄弟判定）。延续 08-04-005。

- [sched-20260804-005](../../2026/08/sched-20260804-005-sched-fair-prefer-fully-idle-cores-for-nohz-balancing.md) `feature/under_review` — NOHZ 负载均衡选 ilb（idle load balancer）CPU 时优先选「整核全 idle」的 CPU，避免把已运行兄弟线程的 SMT 核心当 ilb 损失吞吐。作者实测无调频噪声下 6.2→9.4 TFLOP/s，但加 ibs 噪声后提升消失。v3 已获 Vincent R-b，合入可能性高。
- [sched-20260803-004](../../2026/08/sched-20260803-004-sched-fair-prefer-waker-cpu-for-non-smt-reciprocal-sync-wakeups.md) `discussion/under_review` — `sched/fair` 的「非 SMT reciprocal sync wakeup 优先选 waker CPU」补丁（v3）引发更深层的讨论：review 要求先定义 sync wakeup 的整体策略，而非零散修补。合入取决于策略共识，目前 medium。
- [sched-20260801-005](../../2026/08/sched-20260801-005-sched-fair-prefer-fully-idle-cores-for-nohz-balancing-v3.md) `feature/under_review` — Andrea Righi 让 NOHZ idle load balancer 优先挑选整个 core 都空闲的 CPU，避免 ILB 跑在繁忙 SMT core 的空闲兄弟线程上而挤占其算力。方案本身简单合理、已经过三轮 reviewer 打磨，但**三个版本自始至终没有给出任何效果数据**，这是它目前唯一的明显短板。
- [sched-20260801-004](../../2026/08/sched-20260801-004-sched-fair-prefer-waker-cpu-non-smt-reciprocal-sync-wakeups-v3.md) `feature/under_review` — Shubhang Kaushik (Ampere) 试图让 pipe 式乒乓负载的互惠同步唤醒直接留在 waker CPU 上，在 80 核非 SMT Ampere Altra 上 `perf bench sched pipe` 提升约 30%。但 v3 采用的「非 SMT 才生效」二分法遭到 K Prateek Nayak 的结构性异议，后者给出了一份下推进 `select_idle_sibli
- [sched-20260801-003](../../2026/08/sched-20260801-003-sched-fair-sync-wakeups-target-wakers-core.md) `feature/under_review` — Madadi Vineeth Reddy 提出让 `WF_SYNC` 同步唤醒把 wakee 放到 waker 所在 core 的 SMT 兄弟线程上，以保住已经热的 cache。POWER11 上 hackbench 小规模场景有 6–8% 提升，但 reviewer 当天就指出这个收益可能高度依赖 SMT 编号连续性，x86 上未必成立——在补齐跨平台数据之前不宜下结论。
- [sched-20260731-007](../../2026/07/sched-20260731-007-sched-fair-prefer-fully-idle-cores-nohz-v2-incremental.md) `feature/under_review` — 本文为增量更新，完整背景见 sched-20260730-008。Andrea Righi (NVIDIA) 的 "Prefer fully idle cores for NOHZ balancing" v2 补丁在 20260731 收到 Mete Durlu 的 s390 测试反馈和代码优化建议。Andrea 指出 Mete 建议的 `is_core_idle()` 实现存在不检查目标 CPU
- [sched-20260730-008](../../2026/07/sched-20260730-008-sched-fair-prefer-fully-idle-cores-nohz-balancing-v2.md) `feature/under_review` — Andrea Righi 的 v2 补丁优化 NOHZ idle load balancer 的 CPU 选择：优先选择整个 SMT core 都 idle 的 CPU，避免唤醒部分空闲 core 的 sibling。在 NVIDIA Vera 的 GEMM 测试中从 6.2 TFLOP/s 提升到 9.4 TFLOP/s（+51%）。本文为增量更新，完整背景见 sched-20260729-00
- [sched-20260729-001](../../2026/07/sched-20260729-001-sched-fair-prefer-fully-idle-cores-for-nohz-balancing.md) `feature/under_review` — NVIDIA 的 Andrea Righi 让 NOHZ idle load balancer 优先挑"整个物理核都空闲"的 CPU 来执行，避免 ILB 短暂唤醒 SMT 兄弟线程拖累另一个兄弟的单线程性能；GEMM 实测 6.2 → 9.4 TFLOP/s。当天讨论热烈（7 封），Peter Zijlstra 已介入，review 走向正面，值得关注 v2。
