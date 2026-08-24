# tag: regression

共 4 篇

- [sched-20260824-004-sched-fair-cpufreq-pressure-invariant](../../2026/08/sched-20260824-004-sched-fair-cpufreq-pressure-invariant.md) `fix/medium/under_review` — cpufreq 压力（cpufreq pressure）用于向调度器反馈由于频率受限带来的算力损失。
- [sched-20260823-002](../../2026/08/sched-20260823-002.md) `bug/high/under_review` — 两个生产环境（aarch64 Kunpeng 920、vendor 4.19.90）在长 uptime 后各自崩溃于 `pick_next_task_fair()` 解引用 NULL：root cfs_rq 的 `nr_running` 被污染成 0xFFFFFFFF（-1），使 idle 判定失效、从空 rb 树取到 NULL。签名一致，疑似 nr_running 计数损坏。基于 vendor 4.19，是否主线程可复现待定。
- [sched-20260820-010](../../2026/08/sched-20260820-010.md) `bug/critical/under_review` — flat-hierarchy 除零崩溃（08-19 001）的 08-20 诊断更新：报告者打开 CONFIG_DEBUG 后 diagnosis WARN 确实触发，确认根因走 cpuset 路径（非仅发行版），uptime 21.4h 复现。配套 fix（tg_cpus floor at 1）已合入 tip（见 08-20 005）。
- [sched-20260820-004](../../2026/08/sched-20260820-004.md) `bug/low/under_review` — LKP sparse 在 `kernel/sched/fair.c:2004`（enqueue 路径判断 `cfs_rq->nr_running`）发出静态检查告警，疑似近期 commit `85570f10a4c6`（EEVDF single runqueue 合并）引入。无修复补丁，仅自动报告。