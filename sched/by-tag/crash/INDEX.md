# tag: crash

共 6 篇

- [sched-20260824-007-sched-core-stale-rq-curr-arm64](../../2026/08/sched-20260824-007-sched-core-stale-rq-curr-arm64.md) `bug/critical/under_review` — 在 arm64 平台上偶发地观测到运行队列 `rq->curr` 指向已过期/无效的任务，引发
- [sched-20260824-006-sched-fair-null-deref-v4.19](../../2026/08/sched-20260824-006-sched-fair-null-deref-v4.19.md) `bug/high/under_review` — 在基于 v4.19 的厂商内核上，`pick_next_task_fair()` 中触发了空指针解引用
- [sched-20260823-003](../../2026/08/sched-20260823-003.md) `bug/critical/under_review` — arm64 长运行服务器上偶发 `rq->curr != current`（rq 上记录的当前任务与实际 current 不一致），引发调度器崩溃。生产环境报告，触发条件与内核版本细节待补。属新出现的 crash 报告。
- [sched-20260823-002](../../2026/08/sched-20260823-002.md) `bug/high/under_review` — 两个生产环境（aarch64 Kunpeng 920、vendor 4.19.90）在长 uptime 后各自崩溃于 `pick_next_task_fair()` 解引用 NULL：root cfs_rq 的 `nr_running` 被污染成 0xFFFFFFFF（-1），使 idle 判定失效、从空 rb 树取到 NULL。签名一致，疑似 nr_running 计数损坏。基于 vendor 4.19，是否主线程可复现待定。
- [sched-20260820-010](../../2026/08/sched-20260820-010.md) `bug/critical/under_review` — flat-hierarchy 除零崩溃（08-19 001）的 08-20 诊断更新：报告者打开 CONFIG_DEBUG 后 diagnosis WARN 确实触发，确认根因走 cpuset 路径（非仅发行版），uptime 21.4h 复现。配套 fix（tg_cpus floor at 1）已合入 tip（见 08-20 005）。
- [sched-20260820-005](../../2026/08/sched-20260820-005.md) `fix/medium/merged_tip` — 两封 sched/urgent 已合入 tip：① `rebuild_sched_domains()` 加 `cpus_read_lock`（对应 08-19 005）；② `tg_cpus()` floor at 1（对应 08-19 001 flat-hierarchy 除零崩溃修复）。tip-bot 8/20 自动应用。