# tag: cgroup

共 7 篇

- [sched-20260823-007](../../2026/08/sched-20260823-007.md) `feature/low/under_review` — Tao Cui 的 cgroup PSI selftest 推进到 v4：改成 kselftest harness（TEST_F/FIXTURE_SETUP/TEARDOWN），并把「poll 超时未触发」从 SKIP 改为 FAIL。已迭代四轮，合入概率高。
- [sched-20260823-006](../../2026/08/sched-20260823-006.md) `fix/low/under_review` — Tao Cui 把 08-19「cpu.max 配额未被 BPF 调度器强制时该告警还是文档」的裁定落地到 sched-ext.rst：v3 新增「Scheduler-Dependent Knobs」小节，说明 knob 经由 ops.cgroup_set_*() 透传、是否生效取决于调度器。纯文档，合入概率高。
- [sched-20260823-001](../../2026/08/sched-20260823-001.md) `fix/medium/under_review` — Michal Blaszczyk 修一个 CFS/SCX cgroup 参数「三视图发散」竞态：并发写 cpu.shares 等控制文件时，CFS 内部锁在调 SCX 回调前释放，允许多线程穿插，使 CFS 记录值、SCX 簿记、BPF 调度器三者拿到不同参数。v3 把锁上移到 core 层统一串行化。合入概率高。
- [sched-20260820-010](../../2026/08/sched-20260820-010.md) `bug/critical/under_review` — flat-hierarchy 除零崩溃（08-19 001）的 08-20 诊断更新：报告者打开 CONFIG_DEBUG 后 diagnosis WARN 确实触发，确认根因走 cpuset 路径（非仅发行版），uptime 21.4h 复现。配套 fix（tg_cpus floor at 1）已合入 tip（见 08-20 005）。
- [sched-20260820-008](../../2026/08/sched-20260820-008.md) `fix/low/merged_tip` — 08-19 的 sched_ext 文档两连修在 08-20 推进：① `ei->type → ei->kind` 示例修复已 Applied 到 `sched_ext/for-7.3-fixes`（Fixes `fa48e8d2c7b5`）；② `cgroup CPU knobs are scheduler-dependent` 文档补丁发 v2。
- [sched-20260820-003](../../2026/08/sched-20260820-003.md) `fix/low/under_review` — Michal Koutny（与同日 Liang Luo v2）把 08-19 的「cpu.max 配额未被 BPF 调度器强制时该告警还是文档」讨论落到了文档方案：cgroup-v2.rst 明确 cpu.max/cpu.idle 等 knob 仅在加载的 BPF 调度器实现了对应回调时才对相关任务生效。纯文档，合入概率高。
- [sched-20260820-001](../../2026/08/sched-20260820-001.md) `fix/medium/under_review` — Zhe Liu 修一个 CFS 带宽配置顺序陷阱：先 `cpu.max.burst` 配大值、再设有限 `cpu.max` quota 时，因旧 burst 校验不通过导致 quota 写入直接 EINVAL。修复为「改 quota 不兼容则把 burst 清零」，附文档与 selftest。Michal Koutny 倾向改成 clamp 到 quota，分歧待解。