# tag: sched_ext

共 12 篇

- [sched-20260904-011](../../2026/09/sched-20260904-011.md) `patch_series/high/under_review` — 延续 09-03 004，sub-sched 错误路径 NULL deref 修复进入 v3，本日收到复审（Re）。错误路径（open/enable 失败回滚）访问已释放/未初始化的 `sched` 对象，可能触发 NULL deref crash。
- [sched-20260904-010](../../2026/09/sched-20260904-010.md) `patch_series/high/under_review` — 延续 09-03 003 的 NMI kfunc 审计，本日收到 0/2 封面的复审（Re）。该系列补齐 NMI 上下文下调用会拿锁/未加保护的 kfunc 路径，防止 NMI 与正常上下文并发访问产生数据竞争或死锁。
- [sched-20260904-009](../../2026/09/sched-20260904-009.md) `bug/low/under_review` — 0day/LKP 在 torvalds `master`（head `940de590b839`）上报告 sparse 告警：`kernel/sched/ext/sub.c:288` 参数 1 地址空间不一致（different address spaces）。该告警针对已合入提交 `bb70e4fb626b` "sched_ext: Eject the top rescue consumer on overload"（约 4 周前）。
- [sched-20260904-008](../../2026/09/sched-20260904-008.md) `patch_series/medium/under_review` — 作为某个 18 补丁 sched_ext 系列的第 12 个（[PATCH 12/18]），泛化 reject DSQ 的重入队（reenqueue）路径。Tejun 给出 nits 评审，引用 Andrea Righi 在 `scx_dispatch_enqueue()` 中将 `is_rq_owned` 改为 `dsq_is_rq_owned(dsq)` 的改动。
- [sched-20260904-007](../../2026/09/sched-20260904-007.md) `patch_series/high/under_review` — 让代理执行（proxy execution）与 sched_ext 兼容的系列推进到 v13。Tejun 从 scx 视角给出 "looks okay ... ready to merge and iterate in tree"，并询问 Peter Zijlstra 的意见，等待其拍板。
- [sched-20260903-016](../../2026/09/sched-20260903-016.md) `patch_series/low/rfc` — `WF_SYNC` 是唤醒标志，用于表达「唤醒者即将睡眠、被唤醒者应立即在就近 CPU 运行」的放置意图。scx 调度类对该标志的放置语义此前缺乏明确文档。本系列（RFC）补上 `WF_SYNC` 在 scx 下的唤醒放置语义说明，帮助 BPF 调度器作者正确实现 `select_cpu` / `enqueue`。
- [sched-20260903-014](../../2026/09/sched-20260903-014.md) `patch_series/low/under_review` — `ops.cgroup_set_idle()` 用于按 cgroup 设置 idle 偏好。当下发的新值与当前已生效值相同时，无需重复下发该 ops 调用。本系列使之幂等，避免冗余的 BPF 回调与状态切换开销。
- [sched-20260903-004](../../2026/09/sched-20260903-004.md) `patch_series/high/under_review` — 在 sub-sched（子调度）的错误处理路径（open/enable 失败回滚）中，访问了已释放/未初始化的 `sched` 对象，导致 NULL 解引用，可能触发 NULL deref crash。本系列覆盖两类触发点：`kfunc` 子调度错误路径与 `select_cpu_and` 子调度错误路径。
- [sched-20260903-003](../../2026/09/sched-20260903-003.md) `patch_series/high/under_review` — 09-02 进入评审的「拒 NMI 调用拿锁 kfuncs」审计在 09-03 推进到 v3，并发现两处新的上下文不安全点：NMI 路径下仍可能调用会拿锁的 kfunc，以及 idle 搜索使用的 scratch nodemask 未在 `irqsave` 下保护。本系列补齐这些 NMI 上下文安全缺口。
- [sched-20260902-006-sched-ext-null-deref-select-cpu-and](../../2026/09/sched-20260902-006-sched-ext-null-deref-select-cpu-and.md) `bug/high/under_review` — `sched_ext` 在 `select_cpu_and` 处理「子调度（sub-sched）」错误路径时，未对 `sched`
- [sched-20260902-005-sched-ext-vtime-ordering-v3](../../2026/09/sched-20260902-005-sched-ext-vtime-ordering-v3.md) `fix/low/under_review` — sched_ext 的 dsq（调度队列）按虚拟时间（vtime）排序，其中 `dsq_vtime` 依赖
- [sched-20260902-004-sched-ext-reject-nmi-lock-kfuncs](../../2026/09/sched-20260902-004-sched-ext-reject-nmi-lock-kfuncs.md) `fix/medium/under_review` — sched_ext 的若干 BPF kfunc 内部会获取锁（如 rq 锁、dsq 锁）。在 NMI 上下文调用这些