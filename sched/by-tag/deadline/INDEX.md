# tag: deadline

共 4 篇

- [sched-20260816-001](../../2026/08/sched-20260816-001.md) `fix/low/under_review` — Liang Hao 的 v1 小品：把 `start_dl_timer()` 的"过去到期"检测从 `ktime_us_delta(act, now) < 0` 改为 `ktime_before(act, now)`，使判定与 `act`/`now` 使用同一分辨率（ktime_t），避免微秒取整导致的边界误差。纯清理/正确性改进。
- [sched-20260809-005](../../2026/08/sched-20260809-005.md) `fix/low/under_review` — kernel test robot 在 2026-08-09 报告 sched/ext、rt、deadline 子系统的 sparse 警告（地址空间/上下文标注类），并给出修复建议。属代码质量类 fix，合入可能性高。
- [sched-20260802-004](../../2026/08/sched-20260802-004-sched-deadline-use-revised-wakeup-rule-only-for-running-dl-server.md) `fix/medium/merged_tip` — Ingo Molnar 于 2026-08-02 向 Linus 发出 `sched-urgent-2026-08-02` pull request，仅含一个补丁：Gabriele Monaco 修正 deferred DL server 的唤醒逻辑，让它真正做到"延迟唤醒"。改动 1 文件 2 增 1 删，**已合入 tip/sched/urgent，无需跟进**。
- [sched-20260729-002](../../2026/07/sched-20260729-002-sched-deadline-use-revised-wakeup-rule-only-for-running-dl-s.md) `fix/medium/under_review` — Gabriele Monaco（Red Hat）5 月发的 dl_server wakeup rule 修复被搁置两个多月，7-29 ping 之后 Peter Zijlstra（度假归来）直接回复 "sched/urgent this?"，作者确认——该修复大概率很快进入 tip/sched/urgent。跟踪合入即可，无参与空间。
