# tag: bpf

共 4 篇

- [sched-20260822-004](../../2026/08/sched-20260822-004-sched-ext-fix-spurious-aborts-in-scx-bpf-dsq-move.md) `fix/medium/merged_tip` — Tejun Heo 修复 `scx_bpf_dsq_move()` 中的虚假调度器中止：任务在迭代过程中可能合法地失去所有权（退出或被重新分配），但早期所有权检查将这些良性竞态升级为调度器中止。修复将所有权检查移到 cursor-lost 检查之后。已合入 `sched_ext/for-7.3-fixes`。
- [sched-20260821-007](../../2026/08/sched-20260821-007-bpf-sched-ext-mark-ops-argument-container-pointer-fields-as-trusted.md) `feature/merged_tip` — sched_ext 的 ops 参数容器指针字段被标记为 trusted，允许 BPF 调度器安全地解引用这些指针。补丁已被 bpf/bpf-next.git 合入。
- [sched-20260815-015](../../2026/08/sched-20260815-015-selftests-sched-ext-fix-flaky-ddsp-failure-tests-on-busy-sys.md) `feature/low/under_review` — bpf-ci 代为提交的补丁：让 `selftests/sched_ext` 通过共享的 `lib.bpf.mk` 构建 libbpf，与上游 libbpf 同步，消除版本漂移。CI 已测试通过（2026-08-15 13:55）。属 08-14 系列 010 的延续（selftests/sched_ext 构建现代化）。
- [sched-20260814-008](../../2026/08/sched-20260814-008-cgroup-sched-add-bpf-kfuncs-to-read-a-cpu-cgroup-s-stats.md) `feature/under_review` — Ziyang Men 提交 v1（2 patches）「cgroup, sched: add BPF kfuncs to read a cpu cgroup's stats」。为 cgroup CPU 控制器提供高效 BPF 读取统计（CFS 带宽计数直接读字段，新增 kfunc 计算 throttled time）。含 selftest。under_review。
