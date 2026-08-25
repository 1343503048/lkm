---
layout: default
tag: "cgroup"
title: "标签: cgroup"
article_count: 30
---

- [sched-20260824-001](/lkm/2026/08/24/sched-20260824-001-sched_ext-cgroup-init-cpu-idle.html) `fix/low/under_review` — sched_ext: 在 scx_cgroup_init_args 中传递初始 cpu.idle 状态
- [sched-20260824-003](/lkm/2026/08/24/sched-20260824-003-docs-sched_ext-cgroup-knobs.html) `discussion/none/under_review` — docs/sched_ext: 文档化 cgroup CPU knobs 的调度器依赖性（增量更新）
- [sched-20260824-005](/lkm/2026/08/24/sched-20260824-005-sched-lift-cgroup-locking-core.html) `fix/medium/under_review` — sched: 提升 cgroup 更新锁到核心层（增量更新）
- [sched-20260823-001](/lkm/2026/08/23/sched-20260823-001.html) `fix/medium/under_review` — Michal Blaszczyk 修一个 CFS/SCX cgroup 参数「三视图发散」竞态：并发写 cpu.shares 等控制文件时
- [sched-20260823-006](/lkm/2026/08/23/sched-20260823-006.html) `fix/low/under_review` — Tao Cui 把 08-19「cpu.max 配额未被 BPF 调度器强制时该告警还是文档」的裁定落地到 sched-ext.rst：v3 新增「Sch...
- [sched-20260823-007](/lkm/2026/08/23/sched-20260823-007.html) `feature/low/under_review` — Tao Cui 的 cgroup PSI selftest 推进到 v4：改成 kselftest harness（TEST_F/FIXTURE_SETU...
- [sched-20260822-005](/lkm/2026/08/22/sched-20260822-005-sched-lift-cgroup-locking-peterz-suggests-mutex-rename.html) `fix/low/under_review` — 本文是 sched-20260821-001 的增量更新
- [sched-20260821-001](/lkm/2026/08/21/sched-20260821-001-sched-lift-cgroup-update-locking-to-core-to-prevent-cfs-scx-divergence.html) `fix/medium/under_review` — 并发写入 cgroup 控制文件（如 cpu.shares/cpu.weight）会导致 CFS 与 SCX 之间的状态不一致
- [sched-20260821-006](/lkm/2026/08/21/sched-20260821-006-sched-ext-serialize-concurrent-cpu-max-writers-in-scx-group-set-bandwidth.html) `fix/medium/under_review` — 并发写入同一 cgroup 的 cpu.max 会导致 SCX 侧的 `ops.cgroup_set_bandwidth()` 回调和 `tg->scx....
- [sched-20260820-001](/lkm/2026/08/20/sched-20260820-001.html) `fix/medium/under_review` — Zhe Liu 修一个 CFS 带宽配置顺序陷阱：先 `cpu.max.burst` 配大值、再设有限 `cpu.max` quota 时
- [sched-20260820-003](/lkm/2026/08/20/sched-20260820-003.html) `fix/low/under_review` — Michal Koutny（与同日 Liang Luo v2）把 08-19 的「cpu.max 配额未被 BPF 调度器强制时该告警还是文档」讨论落到了...
- [sched-20260820-008](/lkm/2026/08/20/sched-20260820-008.html) `fix/low/merged_tip` — 08-19 的 sched_ext 文档两连修在 08-20 推进：① `ei->type → ei->kind` 示例修复已 Applied 到 `sc...
- [sched-20260820-010](/lkm/2026/08/20/sched-20260820-010.html) `bug/critical/under_review` — flat-hierarchy 除零崩溃（08-19 001）的 08-20 诊断更新：报告者打开 CONFIG_DEBUG 后 diagnosis WAR...
- [sched-20260819-001](/lkm/2026/08/19/sched-20260819-001-sched-fair-flat-hierarchy-tgcps-divide-zero-fix.html) `bug/critical/under_review` — tip `sched/core` 的 flat-hierarchy rework 在 enqueue 路径触发 `#DE` 除零 panic（group ...
- [sched-20260819-007](/lkm/2026/08/19/sched-20260819-007-selftests-cgroup-add-psi-pressure-tests-v3.html) `feature/low/under_review` — Tao Cui 为 cgroup selftests 增加 `test_psi.c`
- [sched-20260819-008](/lkm/2026/08/19/sched-20260819-008-sched-ext-documentation-fixes-cgroup-knobs-exit-kind.html) `fix/low/under_review` — Liang Luo 修两处 sched-ext 文档：cgroup-v2.rst 里 `cpu.max`/`cpu.max.burst`/`cpu.idl...
- [sched-20260819-010](/lkm/2026/08/19/sched-20260819-010-sched-ext-cgroup-set-bandwidth-warn-vs-doc.html) `discussion/low/under_review` — 关于 "sched_ext 下 cpu.max 配额未被 BPF 调度器强制时是否告警" 的讨论：Tejun NAK 了运行时一次性警告（参照 cpu.w...
- [sched-20260818-004](/lkm/2026/08/18/sched-20260818-004-sched-ext-allow-ops-cgroup-set-bandwidth-to-be-sleepable.html) `feature/medium/under_review` — sched_ext: allow ops.cgroup_set_bandwidth() to be sleepable
- [sched-20260818-005](/lkm/2026/08/18/sched-20260818-005-sched-flatten-the-pick-v3-benchmarks.html) `feature/medium/under_review` — sched: Flatten the pick — v3 s390 benchmark results
- [sched-20260817-003](/lkm/2026/08/17/sched-20260817-003-scheduler-updates-for-v7-3.html) `feature/high/merged_tip` — Scheduler updates for v7.3
- [sched-20260815-014](/lkm/2026/08/15/sched-20260815-014-sched-fair-fix-flat-hierarchy.html) `fix/low/merged_tip` — sched/fair: Fix flat hierarchy
- [sched-20260814-008](/lkm/2026/08/14/sched-20260814-008-cgroup-sched-add-bpf-kfuncs-to-read-a-cpu-cgroup-s-stats.html) `feature/none/under_review` — cgroup, sched: add BPF kfuncs to read a cpu cgroup's stats
- [sched-20260807-002-sched-ext-find-parent-sched-null-check](/lkm/2026/08/07/sched-20260807-002-sched-ext-find-parent-sched-null-check.html) `unknown/none/in-review` — sched ext find parent sched null check
- [sched-20260807-013-sched-preserve-reset-on-fork](/lkm/2026/08/07/sched-20260807-013-sched-preserve-reset-on-fork.html) `unknown/none/in-review` — sched preserve reset on fork
- [sched-20260805-004](/lkm/2026/08/05/sched-20260805-004-sched-fair-remove-dead-throttled-check-pick-task-fair.html) `cleanup/low/superseded` — sched fair remove dead throttled check pick task fair
- [sched-20260804-004](/lkm/2026/08/04/sched-20260804-004-sched-ext-fixes-for-v7.2-rc6-pull.html) `fix/high/merged_tip` — sched_ext: Fix idle CPU state initialization and validation
- [sched-20260803-003](/lkm/2026/08/03/sched-20260803-003-sched-ext-fixes-for-v7.2-rc6.html) `fix/high/merged_tip` — cgroup: Fixes for v7.2-rc6
- [sched-20260801-001](/lkm/2026/08/01/sched-20260801-001-sched-ext-bandwidth-limited-rescue-execution.html) `feature/none/under_review` — sched_ext: Sync tools autogen enum headers
- [sched-20260730-001](/lkm/2026/07/30/sched-20260730-001-sched-fix-sched-flag-keep-params-side-effects.html) `fix/medium/under_review` — sched/deadline: Skip bandwidth accounting with SCHED_FLAG_KEEP_PARAMS
- [sched-20260730-002](/lkm/2026/07/30/sched-20260730-002-sched-fair-cgroup-mode-default-netperf-regression.html) `bug/high/under_review` — [linux-next:master] [sched/fair]  fb1050ac8e: netperf.Throughput_Mbps 14.6% regression
